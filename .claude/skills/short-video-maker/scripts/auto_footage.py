#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker · --auto-footage 模式（关键词自动配画）

与本 skill 的【贴图卡模式】(build_inputs + assemble_synced) 是**两条独立路径**，
互不影响：本脚本不 import、不修改任何贴图卡流水线代码，只复用 MoneyPrinterTurbo
引擎本身（Pexels 素材搜索 + MoviePy 合成）。

适用：没有现成贴图卡、口播偏氛围/空镜的主题（科技、情绪、自然、城市…）。
   ——「给关键词 + 口播稿 → 联网搜免费 HD 竖屏素材 → 出片」。
不适用：靠具体食材/人物/数据说话的主题（黑豆会被搜成咖啡豆）——那类仍走贴图卡模式。

字幕安全区（核心改进）：
   MPT 原生 subtitle_position="bottom" 把字幕压到 y≈1824（距底仅 ~96px），
   会被视频号账号名/点赞评论栏盖住。本模式强制 subtitle_position="custom" +
   custom_position（默认 72），字幕底边落在 y≈1416 一带（距底 ~500px），
   稳稳避开视频号底部 UI 安全带（与贴图卡渲染器预留的 ~420px 底部安全区对齐）。
   依据：app/services/video.py:765-774  custom_y=(1920-clip_h)*P/100，再做边界钳制。

zero-LLM：口播稿(--script)与搜索词(--terms)都直接给，不调任何 LLM，无需 LLM key；
仅需 config.toml 里已注入的 pexels_api_keys。

用法（必须在 MPT venv 里跑，用其 edge_tts / 字体 / imageio-ffmpeg）：
    cd tools/MoneyPrinterTurbo
    uv run python ../../.claude/skills/short-video-maker/scripts/auto_footage.py \
        --issue demo \
        --terms "city night, technology, neon city skyline, future" \
        --script ../../output/short-videos/demo/script.txt \
        --title "本周科技三个信号" --voice zh-CN-YunjianNeural-Male --rate 1.05
    # 需要无人声版（仅字幕+BGM，旁白静音）：加 --also-silent（会再完整渲一遍）
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# 本脚本在 .claude/skills/short-video-maker/scripts/ 下；app 包在 MPT 根目录。
# parents: [0]=scripts [1]=short-video-maker [2]=skills [3]=.claude [4]=My-Studio(repo root)
REPO_ROOT = Path(__file__).resolve().parents[4]
MPT_ROOT = REPO_ROOT / "tools" / "MoneyPrinterTurbo"
sys.path.insert(0, str(MPT_ROOT))

from app.models.schema import VideoParams  # noqa: E402
from app.services import task as task_svc  # noqa: E402

import imageio_ffmpeg  # noqa: E402  （MPT venv 自带，提供 ffmpeg 可执行）
from PIL import Image, ImageDraw, ImageFont  # noqa: E402  （moviepy 依赖 Pillow，必在）

# 封面标题用粗黑体（比正文字幕的 STHeitiMedium 更醒目）；缺失则回退。
COVER_FONT = MPT_ROOT / "resource" / "fonts" / "MicrosoftYaHeiBold.ttc"
COVER_FONT_FALLBACK = MPT_ROOT / "resource" / "fonts" / "STHeitiMedium.ttc"
W, H = 1080, 1920  # 9:16


def parse_terms(raw: str) -> list[str]:
    """'a, b，c' → ['a','b','c']（中英文逗号都切）。"""
    import re
    return [t.strip() for t in re.split(r"[,，]", raw) if t.strip()]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    path = COVER_FONT if COVER_FONT.is_file() else COVER_FONT_FALLBACK
    return ImageFont.truetype(str(path), size)


def _wrap_cn(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """按像素宽贪心折行（中文无空格，逐字累计）。"""
    lines, cur = [], ""
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        trial = cur + ch
        if measure.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def make_cover_title_png(title: str, out_png: Path) -> None:
    """渲染醒目封面标题到 1080x1920 透明 PNG：上中带、半透明衬底 + 白字粗描边。
    位置在顶部安全区(避开~150px刘海)与底部字幕带(~y1416)之间的上中部。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    max_w = 920                       # 文字最大宽（左右各留 ~80px）
    font_size = 100
    # 字号自适应：折行后超过 3 行就缩字，直到 ≤3 行或到下限
    while font_size >= 60:
        font = _load_font(font_size)
        lines = _wrap_cn(title, font, max_w)
        if len(lines) <= 3:
            break
        font_size -= 8
    font = _load_font(font_size)
    lines = _wrap_cn(title, font, max_w)

    line_h = int(font_size * 1.30)
    block_h = line_h * len(lines)
    # 文字块竖直中心放在画面 ~33% 处（上中部）
    block_top = int(H * 0.33 - block_h / 2)

    # 半透明圆角衬底
    pad_x, pad_y = 56, 40
    widths = [draw.textlength(ln, font=font) for ln in lines]
    band_w = int(min(max_w + pad_x * 2, max(widths) + pad_x * 2))
    band_x0 = (W - band_w) // 2
    band_y0 = block_top - pad_y
    band_x1 = band_x0 + band_w
    band_y1 = block_top + block_h + pad_y
    draw.rounded_rectangle([band_x0, band_y0, band_x1, band_y1], radius=28,
                           fill=(0, 0, 0, 130))

    # 居中白字 + 粗黑描边
    y = block_top
    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = (W - w) / 2
        draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255),
                  stroke_width=5, stroke_fill=(0, 0, 0, 230))
        y += line_h
    img.save(out_png)


def burn_cover_title(video_in: Path, title: str, video_out: Path, seconds: float) -> None:
    """把封面标题叠加到开头 seconds 秒（淡入淡出），整片重编码，音轨原样复制。"""
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    fade = 0.4
    with tempfile.TemporaryDirectory() as td:
        overlay = Path(td) / "cover_title.png"
        make_cover_title_png(title, overlay)
        st_out = max(0.0, seconds - fade)
        # 关键：静态 PNG 必须 -loop 1 -t 成 seconds 长的视频流，否则只有 t=0 一帧、叠加不持续。
        fc = (
            f"[1:v]format=rgba,fade=t=in:st=0:d={fade}:alpha=1,"
            f"fade=t=out:st={st_out:.2f}:d={fade}:alpha=1[ov];"
            f"[0:v][ov]overlay=0:0:eof_action=pass[v]"
        )
        cmd = [ff, "-y",
               "-i", str(video_in),
               "-loop", "1", "-framerate", "30", "-t", f"{seconds:.2f}", "-i", str(overlay),
               "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "copy", str(video_out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not video_out.is_file():
            print(f"[err] 封面标题叠加失败:\n{r.stderr[-1500:]}", file=sys.stderr)
            sys.exit(5)


def run_pass(task_id: str, params: VideoParams, mode: str) -> Path:
    """跑一遍完整流水线，返回成片 final-1.mp4 路径。每遍前清掉旧 task 目录避免脏状态
    （cache_videos 不清——已下素材按 URL 复用）。"""
    task_dir = MPT_ROOT / "storage" / "tasks" / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir, ignore_errors=True)
    print(f"\n[..] 生成「{mode}」版 (voice_volume={params.voice_volume}) task={task_id}", flush=True)
    t0 = time.time()
    result = task_svc.start(task_id, params, stop_at="video")
    if not result or not result.get("videos"):
        print(f"[err] 「{mode}」版生成失败，result={result}（看上面 MPT 日志：network/pexels/moviepy）",
              file=sys.stderr)
        sys.exit(4)
    print(f"[ok] 「{mode}」版完成，用时 {time.time()-t0:.0f}s，素材 {len(result.get('materials', []) or [])} 段",
          flush=True)
    src = Path(result["videos"][0])
    if not src.is_file():
        print(f"[err] 成片未找到: {src}", file=sys.stderr)
        sys.exit(4)
    return src


def build_params(script_text: str, terms: list[str], voice: str, voice_volume: float,
                 rate: float, clip_dur: int, concat: str, custom_position: float,
                 bgm: str, bgm_volume: float, font_size: int, no_subtitle: bool) -> VideoParams:
    return VideoParams(
        video_subject="auto-footage",            # 占位（提供 video_script 即跳过 LLM）
        video_script=script_text,                # 直接给口播稿 → 跳过 LLM 写稿
        video_terms=terms,                       # 直接给搜索词 → 跳过 LLM 生成 terms
        video_source="pexels",                   # 联网搜素材（自动配画的关键）
        video_aspect="9:16",                     # 竖屏 1080x1920
        video_concat_mode=concat,                # random=多样 / sequential=按词序
        video_clip_duration=clip_dur,            # 单段素材最长秒数
        video_count=1,
        voice_name=voice,
        voice_volume=voice_volume,               # 1.0 有声 / 0.0 静音旁白（仍出字幕）
        voice_rate=rate,
        subtitle_enabled=not no_subtitle,
        subtitle_position="custom",              # ← 安全区核心：不用 bottom
        custom_position=custom_position,         # ← y=(1920-clip_h)*P/100，72≈距底 500px
        bgm_type="random",
        bgm_file=bgm,
        bgm_volume=bgm_volume,
        font_size=font_size,
        n_threads=4,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="short-video-maker --auto-footage（关键词自动配画）")
    ap.add_argument("--issue", required=True, help="期号/标识，决定输出目录与 task_id")
    ap.add_argument("--terms", required=True, help="Pexels 英文搜索词，逗号分隔，如 \"city night, technology\"")
    ap.add_argument("--script", required=True, help="口播稿文本文件（驱动 TTS + 字幕时间轴）")
    ap.add_argument("--title", default="", help="标题：写进 meta.txt，且默认作为开头醒目封面标题叠在画面上")
    ap.add_argument("--voice", default="zh-CN-YunjianNeural-Male", help="edge-tts 音色")
    ap.add_argument("--rate", type=float, default=1.05, help="语速倍率（>1 更有精神）")
    ap.add_argument("--clip-duration", type=int, default=4, help="单段素材最长秒数")
    ap.add_argument("--concat", default="random", choices=["random", "sequential"], help="素材拼接顺序")
    ap.add_argument("--custom-position", type=float, default=72.0,
                    help="字幕纵向位置（%%，距顶；越小越靠上）。默认 72≈距底 500px，避开视频号底部 UI")
    ap.add_argument("--bgm", default="", help="指定 BGM 文件名（MPT resource/songs/），留空=随机")
    ap.add_argument("--bgm-volume", type=float, default=0.3, help="BGM 音量 0-1")
    ap.add_argument("--font-size", type=int, default=60, help="字幕字号")
    ap.add_argument("--no-subtitle", action="store_true", help="不烧字幕")
    ap.add_argument("--no-cover-title", action="store_true",
                    help="不叠加封面标题（默认：--title 非空就在开头叠醒目大标题，也是平台封面帧）")
    ap.add_argument("--cover-seconds", type=float, default=3.0, help="封面标题在开头停留秒数")
    ap.add_argument("--also-silent", action="store_true", help="额外出无人声版（旁白静音，会再完整渲一遍）")
    ap.add_argument("--out-dir", default="", help="输出目录，默认 output/short-videos/<issue>/")
    args = ap.parse_args()

    script_path = Path(args.script).resolve()
    if not script_path.is_file():
        print(f"[err] 口播稿不存在: {script_path}", file=sys.stderr)
        return 2
    script_text = script_path.read_text(encoding="utf-8").strip()
    if not script_text:
        print(f"[err] 口播稿为空: {script_path}", file=sys.stderr)
        return 2
    terms = parse_terms(args.terms)
    if not terms:
        print("[err] --terms 解析为空", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).resolve() if args.out_dir else \
        REPO_ROOT / "output" / "short-videos" / args.issue
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[i] auto-footage · issue={args.issue} · {len(terms)} 个搜索词 · 稿 {len(script_text)} 字 "
          f"· 字幕位 {args.custom_position}% · 输出 {out_dir}", flush=True)
    print(f"    terms: {terms}", flush=True)

    want_cover = bool(args.title.strip()) and not args.no_cover_title
    if want_cover:
        print(f"[i] 开头叠醒目封面标题: 「{args.title}」（{args.cover_seconds}s，也是平台封面帧）", flush=True)

    def deliver(src: Path, dst: Path) -> None:
        """有标题就叠封面标题（重编码），否则直接拷贝。"""
        if want_cover:
            burn_cover_title(src, args.title.strip(), dst, args.cover_seconds)
        else:
            shutil.copyfile(src, dst)
        print(f"[ok] → {dst}", flush=True)

    results: list[Path] = []
    # 有口播版
    p_voice = build_params(script_text, terms, args.voice, 1.0, args.rate, args.clip_duration,
                           args.concat, args.custom_position, args.bgm, args.bgm_volume,
                           args.font_size, args.no_subtitle)
    src = run_pass(f"autofootage-{args.issue}", p_voice, "voice")
    dst = out_dir / f"{args.issue}-autofootage.mp4"
    deliver(src, dst)
    results.append(dst)

    # 无人声版（可选，旁白静音；MoviePy 路径不能像 ffmpeg 那样 -c:v copy 复用，需再渲一遍）
    if args.also_silent:
        p_silent = build_params(script_text, terms, args.voice, 0.0, args.rate, args.clip_duration,
                                args.concat, args.custom_position, args.bgm, args.bgm_volume,
                                args.font_size, args.no_subtitle)
        src_s = run_pass(f"autofootage-{args.issue}-silent", p_silent, "silent")
        dst_s = out_dir / f"{args.issue}-autofootage-silent.mp4"
        deliver(src_s, dst_s)
        results.append(dst_s)

    meta = out_dir / "meta.txt"
    meta.write_text(
        f"mode: auto-footage (Pexels 关键词自动配画)\n"
        f"issue: {args.issue}\n"
        f"建议标题: {args.title or '（待定）'}\n"
        f"搜索词: {', '.join(terms)}\n"
        f"成片: {', '.join(p.name for p in results)}\n"
        f"封面标题: {('叠在开头 ' + str(args.cover_seconds) + 's') if want_cover else '（无）'}\n"
        f"字幕安全区: subtitle_position=custom, custom_position={args.custom_position}\n"
        f"发布: 手动上传视频号/抖音/小红书，或 publish_channels.py 推草稿\n",
        encoding="utf-8")
    print(f"\n[done] {len(results)} 条成片 + meta.txt → {out_dir}", flush=True)
    print(json.dumps({"videos": [str(p) for p in results], "terms": terms}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())