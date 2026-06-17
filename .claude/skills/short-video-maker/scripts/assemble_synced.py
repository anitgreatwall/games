#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker · 精确同步拼装器（每卡时长 = 该段口播真实时长）

解决"均匀切换导致后面错位"：MPT 对图片用固定 clip_duration，口播各段长短不一 → 误差累积。
本拼装器逐段用 edge-tts 合成、量出每段真实时长，再让每张卡精确停留那么久，拼接成片——
画面切换与口播段落构造性对齐，不靠估算。

**两套渲染引擎**（`--engine`）：
- `ffmpeg`（默认，快）：原生 ffmpeg 滤镜图——zoompan 做 Ken Burns、ASS(libass) 烧字幕、
  concat 拼接，AMD `h264_amf` 硬件编码（`--codec x264` 回退 libx264 veryfast/16 线程）。
  渲染在 C 层完成，不再受 MoviePy 单线程逐帧重算拖累。
- `moviepy`（兜底）：旧的 MoviePy 逐帧路径，留作 ffmpeg 引擎出问题时对照/回退。

**出片版本**：默认只出口播版 `<issue>-voice.mp4`。`--also-silent` 额外出无人声版
（旁白静音、留 BGM+字幕）；`--silent` 只出无人声版。无人声版**复用同一次视频编码**
（`-c:v copy` 仅换音轨），近乎免费——不再像旧流程那样把整条管线跑两遍。

**TTS 并行**：各段 edge-tts 合成在单事件循环内 `asyncio.gather` 限流并发，问候段一并纳入，
不再逐段串行阻塞。

**必须在 MPT venv 里跑**（用其 edge_tts / moviepy / 字体；ffmpeg 用 imageio-ffmpeg 自带）：
    cd tools/MoneyPrinterTurbo
    uv run python <skill>/scripts/assemble_synced.py --inputs <inputs.json> [--voice ...] [--rate 1.1] [--bgm 文件名] [--also-silent]

约定：script.txt 一行=一段=一张卡，行数应与 materials(卡片) 数一致（多退少补，按 min 对齐并告警）。
"""
import argparse
import asyncio
import re
import shutil
import subprocess
import sys
import json
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import ImageFont

W, H, FPS = 1080, 1920, 30
# 与 render_cards.py 的 9x16 安全区一致：底部 BOTTOM_SAFE 留给视频号 UI，卡片 footer 带高 FOOTER_H。
# footer 占 [H-BOTTOM_SAFE-FOOTER_H, H-BOTTOM_SAFE]；其下为空白带，字幕落此处不压版面。
BOTTOM_SAFE = 460
FOOTER_H = 78
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ───────────────────────── TTS（并行合成）─────────────────────────
async def _synth_all(jobs, rate_pct, sem_n=5):
    """jobs: [(text, voice, out_path), ...]，单事件循环内限流并发。"""
    sem = asyncio.Semaphore(sem_n)

    async def one(text, voice, out):
        async with sem:
            await edge_tts.Communicate(text, voice, rate=rate_pct).save(str(out))

    await asyncio.gather(*(one(t, v, o) for (t, v, o) in jobs))


def synth_all(jobs, rate_pct, sem_n=5):
    asyncio.run(_synth_all(jobs, rate_pct, sem_n))


def audio_dur(path: Path) -> float:
    """用 ffmpeg 解析 Duration（不依赖 moviepy；ffmpeg 引擎路径不加载 moviepy）。"""
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out)
    if not m:
        raise RuntimeError(f"无法读取音频时长: {path}\n{out[-400:]}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


# ───────────────────────── 文本折行（两引擎共用）─────────────────────────
def _wrap_text(text: str, font: "ImageFont.FreeTypeFont", max_w: int) -> list:
    """按像素宽度贪心折行。**按词原子化**：连续拉丁/数字（含内部 . - + % /）当成不可拆 token，
    避免英文/数字单词中间断行（如 OpenAI 被拆成 Ope / nAI）。"""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9.\-+%/]*|\s+|.", text)
    lines, cur = [], ""
    for tok in tokens:
        if tok == "\n":
            lines.append(cur.rstrip())
            cur = ""
            continue
        if not cur or font.getlength(cur + tok) <= max_w:
            cur += tok
        else:
            lines.append(cur.rstrip())
            cur = "" if tok.isspace() else tok
    if cur.strip():
        lines.append(cur.rstrip())
    return lines or [""]


def _font_size_for(text: str) -> int:
    """字号按字数自适应（与旧 make_subtitle 一致）。"""
    n = len(text)
    return 48 if n <= 40 else (44 if n <= 60 else 38)


# ───────────────────────── ffmpeg 引擎：ASS 字幕 ─────────────────────────
def _ass_ts(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(segments, font_path: str, out_path: Path, sub_drop: int = 0):
    """复刻 make_subtitle 版式到 ASS：按字数选字号、PIL 像素预折行、顶锚 band_top、居中、白字黑描边 2px。
    segments: [(text, start_abs, dur), ...]（绝对时间轴，已含 cover 偏移）。
    用 \\an8(top-center)+\\pos 精确定位；WrapStyle 2 关闭 libass 自动折行（我们已预折）。"""
    family = ImageFont.truetype(font_path, 48).getname()[0]
    max_w = int(W * 0.88)
    # sub_drop: 绣像/古籍版式木刻底框在 ~1423(Ken Burns 峰值 ~1442)，传 ~40 让首行离框留 ~66px
    band_top = H - BOTTOM_SAFE + 8 + sub_drop  # footer 下沿再下 8px，顶锚
    head = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{family},48,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,"
        "100,100,0,0,1,2,0,8,0,0,0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    rows = []
    for text, start, dur in segments:
        fs = _font_size_for(text)
        wrapped = _wrap_text(text, ImageFont.truetype(font_path, fs), max_w)
        body = "\\N".join(wrapped)
        ov = f"{{\\an8\\fs{fs}\\pos({W // 2},{band_top})}}"
        rows.append(f"Dialogue: 0,{_ass_ts(start)},{_ass_ts(start + dur)},Default,,0,0,0,,{ov}{body}")
    out_path.write_text(head + "\n".join(rows) + "\n", encoding="utf-8")


# ───────────────────────── ffmpeg 引擎：视频编码（仅画面，无音轨）─────────────────────────
def codec_args(codec: str) -> list:
    if codec == "x264":
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-threads", "0"]
    # 默认 AMD AMF 硬件编码（本机 Radeon 860M，已实测可用）。
    # 码率 2M：画面是近静态卡片+轻微 zoom，2M 文字仍清晰（实测 1.5M libx264 帧目检锐利）；
    # 且保证 <60s 成片 ≈15MB——飞书 DM（手机端兜底）视频上限实测在 ~15–28MB 之间（28MB 被拒、
    # 14.8MB 通过），2M 留足余量。视频号对静态卡片片源 2M 也够清晰。
    return ["-c:v", "h264_amf", "-b:v", "2M", "-maxrate", "3M", "-bufsize", "6M",
            "-pix_fmt", "yuv420p"]


def encode_video_only(timeline, ass_rel, out_path: Path, work: Path, codec: str, kb_ss: int = 3):
    """timeline: [(img_path, dur, kenburns_bool), ...]（含 cover 在首，按最终顺序）。
    每张图单帧输入 → zoompan 生成对应时长(d 帧) → concat → ASS 烧字幕 → 编码（-an，无音轨）。
    kb_ss：Ken Burns 超采样倍率——zoompan 对 x/y 做整数像素取整，慢速缩放会逐帧"跳"出抖动；
    在 kb_ss× 分辨率上做 zoompan 再 lanczos 降采样，取整落到更细网格 + 降采样抗锯齿，抖动消失。"""
    inputs, segs, labels = [], [], []
    for i, (p, d, kb) in enumerate(timeline):
        inputs += ["-i", str(p)]
        frames = max(1, round(d * FPS))
        base = f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
        if not kb:
            seg = f"{base},zoompan=z='1':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p[v{i}]"
        else:
            inc = 0.04 / max(1, frames - 1)
            z = f"min(1+{inc:.8f}*on,1.04)"  # 线性放大到 +4%
            pan = f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            if kb_ss > 1:
                sw, sh = kb_ss * W, kb_ss * H
                seg = (f"{base},scale={sw}:{sh}:flags=bicubic,"
                       f"zoompan=z='{z}':d={frames}:{pan}:s={sw}x{sh}:fps={FPS},"
                       f"scale={W}:{H}:flags=lanczos,format=yuv420p[v{i}]")
            else:
                seg = (f"{base},zoompan=z='{z}':d={frames}:{pan}:s={W}x{H}:fps={FPS},"
                       f"format=yuv420p[v{i}]")
        segs.append(seg)
        labels.append(f"[v{i}]")
    concat = "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[vcat]"
    sub = f"[vcat]subtitles={ass_rel}:fontsdir=fonts[vout]" if ass_rel else "[vcat]copy[vout]"
    fc = ";".join(segs + [concat, sub])
    cmd = [FFMPEG, "-y", *inputs, "-filter_complex", fc, "-map", "[vout]", "-an",
           *codec_args(codec), "-r", str(FPS), str(out_path)]
    subprocess.run(cmd, cwd=str(work), check=True)


# ───────────────────────── ffmpeg 引擎：音轨 ─────────────────────────
_AFMT = "aformat=sample_rates=44100:channel_layouts=stereo"


def build_voice_audio(seg_mp3s, greeting_mp3, cover_dur, bgm_path, bgm_volume,
                      full_total, out_path: Path, work: Path):
    """问候(@0) + 旁白(@cover_dur) + BGM(贯穿、循环、尾部淡出) 混音 → m4a。复刻旧 CompositeAudioClip。"""
    inputs, parts, seg_labels = [], [], []
    idx = 0
    for s in seg_mp3s:
        inputs += ["-i", str(s)]
        parts.append(f"[{idx}:a]{_AFMT}[a{idx}]")
        seg_labels.append(f"[a{idx}]")
        idx += 1
    parts.append("".join(seg_labels) + f"concat=n={len(seg_labels)}:v=0:a=1[narr]")
    delay = int(round(cover_dur * 1000))
    parts.append(f"[narr]adelay={delay}|{delay}[narrd]")
    mix = ["[narrd]"]
    if greeting_mp3:
        inputs += ["-i", str(greeting_mp3)]
        parts.append(f"[{idx}:a]{_AFMT}[g]")
        mix.insert(0, "[g]")
        idx += 1
    if bgm_path:
        inputs += ["-i", str(bgm_path)]
        st = max(0.0, full_total - 3)
        parts.append(f"[{idx}:a]{_AFMT},volume={bgm_volume},aloop=loop=-1:size=2000000000,"
                     f"atrim=0:{full_total:.3f},afade=t=out:st={st:.3f}:d=3[bgmx]")
        mix.append("[bgmx]")
        idx += 1
    parts.append("".join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0[aout]")
    cmd = [FFMPEG, "-y", *inputs, "-filter_complex", ";".join(parts),
           "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(out_path)]
    subprocess.run(cmd, cwd=str(work), check=True)


def build_silent_audio(bgm_path, bgm_volume, full_total, out_path: Path, work: Path):
    """无人声版音轨：仅 BGM（无 BGM 时给等长静音轨，保证有 1 条音频流）。"""
    if bgm_path:
        st = max(0.0, full_total - 3)
        fc = (f"[0:a]{_AFMT},volume={bgm_volume},aloop=loop=-1:size=2000000000,"
              f"atrim=0:{full_total:.3f},afade=t=out:st={st:.3f}:d=3[aout]")
        cmd = [FFMPEG, "-y", "-i", str(bgm_path), "-filter_complex", fc,
               "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(out_path)]
    else:
        cmd = [FFMPEG, "-y", "-f", "lavfi", "-t", f"{full_total:.3f}",
               "-i", "anullsrc=r=44100:cl=stereo", "-c:a", "aac", "-b:a", "128k", str(out_path)]
    subprocess.run(cmd, cwd=str(work), check=True)


def mux(video_only: Path, audio: Path, out_path: Path, work: Path):
    """同一次编码的视频流 + 指定音轨 → 成片（-c:v copy，不重编码）。"""
    cmd = [FFMPEG, "-y", "-i", str(video_only), "-i", str(audio),
           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
           "-movflags", "+faststart", "-shortest", str(out_path)]
    subprocess.run(cmd, cwd=str(work), check=True)


def run_ffmpeg_engine(*, cards, durs, seg_mp3s, greeting_mp3, cover_dur, cover_path,
                      bgm_path, bgm_volume, font_path, work, out_dir, issue,
                      no_subtitle, no_kenburns, kb_ss, codec, make_voice, make_silent,
                      sub_drop=0):
    full_total = cover_dur + sum(durs)

    # 字幕：按各段绝对起止；onepage 帧免字幕（本身满字信息图）
    ass_rel = None
    if not no_subtitle:
        segments, t = [], cover_dur
        for line, d, card in zip(_lines_cache, durs, cards):
            if "onepage" not in card.name.lower():
                segments.append((line, t, d))
            t += d
        if segments:
            ass_path = work / "subs.ass"
            build_ass(segments, font_path, ass_path, sub_drop=sub_drop)
            # 字体放专用干净子目录：libass fontsdir 会把目录里每个文件当字体试解析，
            # 若指向 work/（混着 mp3/ass/m4a）会刷一堆 "Error opening memory font" 噪声。
            fonts_dir = work / "fonts"
            fonts_dir.mkdir(exist_ok=True)
            shutil.copy(font_path, fonts_dir / "subfont.ttc")
            ass_rel = "subs.ass"

    # 画面时间线：封面(静止) 在首，内容卡各自 ken_burns
    timeline = []
    if cover_path:
        timeline.append((cover_path, cover_dur, False))
    for card, d in zip(cards, durs):
        timeline.append((card, d, not no_kenburns))

    video_only = work / "video_only.mp4"
    ss_note = f"超采样x{kb_ss}" if not no_kenburns else "静帧"
    print(f"[i] 编码画面（zoompan {ss_note} + 字幕 + {codec}，一次编码两版复用）…")
    encode_video_only(timeline, ass_rel, video_only, work, codec, kb_ss=kb_ss)

    if make_voice:
        va = work / "voice_audio.m4a"
        build_voice_audio(seg_mp3s, greeting_mp3, cover_dur, bgm_path, bgm_volume, full_total, va, work)
        out = out_dir / f"{issue}-voice.mp4"
        mux(video_only, va, out, work)
        print(f"[done] {out}")
    if make_silent:
        sa = work / "silent_audio.m4a"
        build_silent_audio(bgm_path, bgm_volume, full_total, sa, work)
        out = out_dir / f"{issue}-silent.mp4"
        mux(video_only, sa, out, work)
        print(f"[done] {out}（-c:v copy 复用画面，未重编码）")


# ───────────────────────── moviepy 引擎（兜底，旧逐帧路径）─────────────────────────
def ken_burns(clip, dur):
    return clip.resized(lambda t: 1 + 0.04 * (t / max(0.01, dur)))


def make_subtitle(text, font_path, start, dur, sub_drop=0):
    from moviepy import TextClip
    fs = _font_size_for(text)
    max_w = int(W * 0.88)
    stroke = 2
    lines = _wrap_text(text, ImageFont.truetype(font_path, fs), max_w)
    wrapped = "\n".join(lines)
    line_h = int(fs * 1.45) + stroke * 2
    est_h = len(lines) * line_h + 28
    tc = TextClip(text=wrapped, font=font_path, font_size=fs, color="#FFFFFF",
                  stroke_color="#000000", stroke_width=stroke,
                  size=(max_w, est_h), method="caption", text_align="center")
    band_top = H - BOTTOM_SAFE + 8 + sub_drop
    y = band_top
    if y + est_h > H - 50:
        y = max(0, H - 50 - est_h)
    tc = tc.with_start(start).with_duration(dur)
    return tc.with_position(("center", y))


def run_moviepy_engine(*, cards, durs, seg_mp3s, greeting_mp3, greeting_dur, cover_dur,
                       cover_path, bgm_path, bgm_volume, font_path, out_dir, issue,
                       no_subtitle, silent, sub_drop=0):
    from moviepy import (AudioFileClip, CompositeAudioClip, CompositeVideoClip,
                         ImageClip, afx, concatenate_audioclips, concatenate_videoclips)
    audios = [AudioFileClip(str(s)) for s in seg_mp3s]
    total = sum(durs)
    vclips = [ken_burns(ImageClip(str(c)).with_duration(d), d) for c, d in zip(cards, durs)]
    video = concatenate_videoclips(vclips, method="compose")
    narration = concatenate_audioclips(audios)
    if silent:
        narration = narration.with_effects([afx.MultiplyVolume(0.0)])
    overlays = []
    if not no_subtitle:
        t = 0.0
        for line, d, card in zip(_lines_cache, durs, cards):
            if "onepage" not in card.name.lower():
                overlays.append(make_subtitle(line, font_path, t, d, sub_drop=sub_drop))
            t += d
    if overlays:
        video = CompositeVideoClip([video, *overlays])
    greeting_audio = AudioFileClip(str(greeting_mp3)) if greeting_mp3 else None
    if cover_path:
        cover_clip = ImageClip(str(cover_path)).with_duration(cover_dur)
        video = concatenate_videoclips([cover_clip, video], method="compose")
    full_total = cover_dur + total
    tracks = []
    if greeting_audio is not None:
        g = greeting_audio if not silent else greeting_audio.with_effects([afx.MultiplyVolume(0.0)])
        tracks.append(g.with_start(0))
    tracks.append(narration.with_start(cover_dur))
    if bgm_path:
        tracks.append(AudioFileClip(str(bgm_path)).with_effects([
            afx.MultiplyVolume(bgm_volume), afx.AudioLoop(duration=full_total), afx.AudioFadeOut(3)]))
    video = video.with_audio(CompositeAudioClip(tracks))
    mode = "silent" if silent else "voice"
    out = out_dir / f"{issue}-{mode}.mp4"
    video.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac",
                          audio_bitrate="192k", threads=4, logger=None,
                          ffmpeg_params=["-movflags", "+faststart"])
    print(f"[done] {out}")


# 模块级缓存：内容段文案（ASS / 字幕用），main 里填充
_lines_cache: list = []


def main() -> int:
    ap = argparse.ArgumentParser(description="精确同步短视频拼装器")
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--voice", default="zh-CN-YunjianNeural")
    ap.add_argument("--rate", type=float, default=1.1, help="语速倍率 → 转 edge-tts 百分比")
    ap.add_argument("--bgm", default="", help="MPT resource/songs/ 下的 BGM 文件名")
    ap.add_argument("--bgm-volume", type=float, default=0.32)
    ap.add_argument("--greeting-voice", default="zh-CN-XiaoxiaoNeural",
                    help="开场问候音色（默认晓晓·欢快女声；正文用 --voice 云健男声）")
    ap.add_argument("--cover-tail", type=float, default=0.6, help="问候念完后封面额外停留秒数")
    ap.add_argument("--no-cover", action="store_true", help="关闭开场封面")
    ap.add_argument("--also-silent", action="store_true",
                    help="额外出无人声版（复用同一次编码，-c:v copy 仅换音轨）")
    ap.add_argument("--silent", action="store_true", help="只出无人声版（旁白静音，留字幕+BGM）")
    ap.add_argument("--no-subtitle", action="store_true")
    ap.add_argument("--no-kenburns", action="store_true", help="关闭 Ken Burns 放大（静帧，最省算力、零抖动）")
    ap.add_argument("--kb-supersample", type=int, default=3,
                    help="Ken Burns 超采样倍率（越大越平滑越慢）：2≈快/3≈平衡(默认)/4≈最平滑；1=不超采样(会抖)")
    ap.add_argument("--engine", choices=["ffmpeg", "moviepy"], default="ffmpeg",
                    help="渲染引擎：ffmpeg(默认,快) / moviepy(兜底,旧逐帧)")
    ap.add_argument("--codec", choices=["amf", "x264"], default="amf",
                    help="ffmpeg 引擎编码器：amf(默认,AMD 硬件) / x264(libx264 veryfast)")
    ap.add_argument("--sub-drop", type=int, default=0,
                    help="字幕顶锚额外下移 px（绣像/古籍版式底框较高时用，建议 40；默认 0 不影响普通片源）")
    args = ap.parse_args()

    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    mpt_root = Path(inputs["mpt_root"]).resolve()
    out_dir = Path(args.inputs).resolve().parent
    local_videos = mpt_root / "storage" / "local_videos"
    font_path = str((mpt_root / "resource" / "fonts" / "STHeitiMedium.ttc"))
    if sys.platform == "win32":
        font_path = font_path.replace("\\", "/")

    voice = args.voice.replace("-Male", "").replace("-Female", "")
    rate_pct = f"{'+' if args.rate >= 1 else ''}{int(round((args.rate - 1) * 100))}%"

    lines = [ln.strip() for ln in inputs["script"].splitlines() if ln.strip()]
    cards = [local_videos / fn for fn in inputs["materials"]]
    n = min(len(lines), len(cards))
    if len(lines) != len(cards):
        print(f"[warn] 段数({len(lines)}) ≠ 卡片数({len(cards)})，按 {n} 对齐", file=sys.stderr)
    lines, cards = lines[:n], cards[:n]
    _lines_cache.clear()
    _lines_cache.extend(lines)

    work = out_dir / "_synth"
    work.mkdir(exist_ok=True)

    # 开场封面 / 问候
    greeting = inputs.get("greeting", "").strip()
    cover_path = inputs.get("cover", "")
    have_cover = bool(cover_path) and Path(cover_path).is_file() and not args.no_cover
    if cover_path and not have_cover and not args.no_cover:
        print(f"[warn] cover 路径无效，跳过开场: {cover_path}", file=sys.stderr)
    cover_path = str(Path(cover_path).resolve()) if have_cover else ""
    g_voice = (args.greeting_voice or args.voice).replace("-Male", "").replace("-Female", "")

    # 1. 并行合成所有 TTS（内容段 + 问候段）
    seg_mp3s = [work / f"seg{i:02d}.mp3" for i in range(1, n + 1)]
    jobs = [(line, voice, mp3) for line, mp3 in zip(lines, seg_mp3s)]
    greeting_mp3 = None
    if have_cover and greeting:
        greeting_mp3 = work / "seg00-greeting.mp3"
        jobs.append((greeting, g_voice, greeting_mp3))
    print(f"[i] 并行合成 {len(jobs)} 段 TTS …")
    synth_all(jobs, rate_pct)

    # 2. 量时长
    durs = [audio_dur(s) for s in seg_mp3s]
    for i, (line, d) in enumerate(zip(lines, durs), 1):
        print(f"[ok] 段{i}: {d:.1f}s · {line[:18]}…")
    total = sum(durs)
    greeting_dur = audio_dur(greeting_mp3) if greeting_mp3 else 0.0
    if have_cover:
        cover_dur = (greeting_dur + args.cover_tail) if greeting_mp3 else max(args.cover_tail, 1.5)
        if greeting_mp3:
            print(f"[ok] 开场问候: {greeting_dur:.1f}s · {greeting[:18]}…")
        else:
            print("[warn] inputs.greeting 为空，开场仅封面静止（建议每期写问候语）", file=sys.stderr)
    else:
        cover_dur = 0.0
    print(f"[i] 共 {n} 段 / {total:.1f}s（+ 开场 {cover_dur:.1f}s = {cover_dur + total:.1f}s）")

    bgm_path = None
    if args.bgm:
        bp = mpt_root / "resource" / "songs" / args.bgm
        if bp.is_file():
            bgm_path = str(bp.resolve())
        else:
            print(f"[warn] BGM 不存在: {bp}", file=sys.stderr)

    make_voice = not args.silent
    make_silent = args.also_silent or args.silent

    if args.engine == "moviepy":
        # 兜底路径：单版（默认 voice；--silent 出 silent）。--also-silent 在此引擎不复用，需另跑。
        run_moviepy_engine(cards=cards, durs=durs, seg_mp3s=seg_mp3s, greeting_mp3=greeting_mp3,
                           greeting_dur=greeting_dur, cover_dur=cover_dur,
                           cover_path=(cover_path or None), bgm_path=bgm_path,
                           bgm_volume=args.bgm_volume, font_path=font_path, out_dir=out_dir,
                           issue=inputs["issue"], no_subtitle=args.no_subtitle, silent=args.silent,
                           sub_drop=args.sub_drop)
        if args.also_silent and not args.silent:
            run_moviepy_engine(cards=cards, durs=durs, seg_mp3s=seg_mp3s, greeting_mp3=greeting_mp3,
                               greeting_dur=greeting_dur, cover_dur=cover_dur,
                               cover_path=(cover_path or None), bgm_path=bgm_path,
                               bgm_volume=args.bgm_volume, font_path=font_path, out_dir=out_dir,
                               issue=inputs["issue"], no_subtitle=args.no_subtitle, silent=True,
                               sub_drop=args.sub_drop)
        return 0

    run_ffmpeg_engine(cards=cards, durs=durs, seg_mp3s=seg_mp3s, greeting_mp3=greeting_mp3,
                      cover_dur=cover_dur, cover_path=(cover_path or None), bgm_path=bgm_path,
                      bgm_volume=args.bgm_volume, font_path=font_path, work=work, out_dir=out_dir,
                      issue=inputs["issue"], no_subtitle=args.no_subtitle, no_kenburns=args.no_kenburns,
                      kb_ss=args.kb_supersample, codec=args.codec,
                      make_voice=make_voice, make_silent=make_silent, sub_drop=args.sub_drop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())