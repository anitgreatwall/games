#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker · MoneyPrinterTurbo 调用器

读取 build_inputs.py 产出的 inputs.json，调 MPT 的 FastAPI（/api/v1）生成竖屏短视频。
默认产出两条：有口播版 + 无人声版（仅字幕+BGM）。两条用同一条流水线，仅 voice_volume 不同：
  - 有口播：voice_volume=1.0
  - 无人声：voice_volume=0.0 —— TTS 仍生成（用于字幕时间轴+定时长），但旁白被静音
    （依据 app/services/video.py: afx.MultiplyVolume(params.voice_volume)）

成片 = <mpt>/storage/tasks/<task_id>/final-1.mp4，复制到 output/short-videos/<issue>/。
不自动发布——视频号无第三方投稿 API，作者手动上传。

用法:
    python run_mpt.py --inputs output/short-videos/w23/inputs.json
    python run_mpt.py --inputs ... --voice zh-CN-XiaoxiaoNeural-Female --start-server
    python run_mpt.py --inputs ... --voice-only        # 只出有口播版
    python run_mpt.py --inputs ... --silent-only       # 只出无人声版
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# MPT 任务状态码（app/models/const.py）
STATE_FAILED, STATE_COMPLETE, STATE_PROCESSING = -1, 1, 4
# 中文 edge-tts 语速上界估计（字/秒）。偏大 → 估时偏小 → clip_dur 偏小，
# 保证 num_cards*clip_dur <= 真实音频时长，绝不丢卡（combine_videos 会到音频时长就停）。
CHARS_PER_SEC = 5.5


def api(base: str, path: str, method: str = "GET", body: dict | None = None, timeout: int = 60):
    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def server_up(base: str) -> bool:
    try:
        urllib.request.urlopen(f"{base}/openapi.json", timeout=5)
        return True
    except Exception:
        return False


def ensure_server(base: str, mpt_root: Path, start: bool) -> subprocess.Popen | None:
    if server_up(base):
        print(f"[ok] MPT 服务在线: {base}")
        return None
    if not start:
        print(f"[err] MPT 服务未启动: {base}\n"
              f"      先在 {mpt_root} 运行: uv run python main.py\n"
              f"      或本脚本加 --start-server 自动拉起。", file=sys.stderr)
        sys.exit(3)
    print(f"[..] 启动 MPT 服务: uv run python main.py（cwd={mpt_root}）")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    proc = subprocess.Popen(["uv", "run", "python", "main.py"], cwd=str(mpt_root),
                            creationflags=flags)
    for _ in range(90):
        if server_up(base):
            print(f"[ok] MPT 服务已就绪: {base}")
            return proc
        time.sleep(1)
    print("[err] MPT 服务启动超时（90s）", file=sys.stderr)
    proc.terminate()
    sys.exit(3)


def poll(base: str, task_id: str, label: str, timeout_s: int = 1200) -> dict:
    """轮询任务直到完成/失败，返回 task data。"""
    t0 = time.time()
    last = -1
    while time.time() - t0 < timeout_s:
        data = api(base, f"/api/v1/tasks/{task_id}").get("data", {})
        state, prog = data.get("state"), data.get("progress", 0)
        if prog != last:
            print(f"    [{label}] progress={prog}% state={state}")
            last = prog
        if state == STATE_COMPLETE:
            return data
        if state == STATE_FAILED:
            print(f"[err] 任务失败 [{label}] task_id={task_id}（查看 MPT 服务日志）", file=sys.stderr)
            sys.exit(4)
        time.sleep(3)
    print(f"[err] 任务超时 [{label}] task_id={task_id}", file=sys.stderr)
    sys.exit(4)


def build_params(inputs: dict, voice: str, voice_volume: float, clip_dur: int,
                 rate: float, bgm: str, bgm_volume: float) -> dict:
    """构造 /api/v1/videos 请求体（VideoParams，见 app/models/schema.py）。"""
    return {
        "video_subject": inputs.get("title") or inputs["issue"],  # 必填；占位用
        "video_script": inputs["script"],          # 自定义文案 → 跳过 LLM 生成
        "video_source": "local",                    # 用本地素材（贴图卡）
        "video_materials": [{"provider": "local", "url": fn, "duration": clip_dur}
                            for fn in inputs["materials"]],
        "video_aspect": "9:16",                     # 竖屏 1080x1920
        "video_concat_mode": "sequential",          # 按卡片顺序
        "video_clip_duration": clip_dur,            # 每张卡时长（也是 Ken Burns 时长）
        "video_count": 1,
        "voice_name": voice,
        "voice_volume": voice_volume,               # 1.0 有声 / 0.0 静音旁白
        "voice_rate": rate,                         # >1 更快更有精神
        "subtitle_enabled": True,
        "subtitle_position": "bottom",
        # 指定 bgm_file（科技/电音）则用它，否则 random 兜底（见 video.py get_bgm_file）
        "bgm_type": "random",
        "bgm_file": bgm,
        "bgm_volume": bgm_volume,
        "font_size": 60,
        "n_threads": 4,
    }


def run_mode(base: str, mpt_root: Path, inputs: dict, out_dir: Path,
             voice: str, clip_dur: int, mode: str, rate: float, bgm: str, bgm_volume: float) -> Path:
    voice_volume = 1.0 if mode == "voice" else 0.0
    print(f"\n[..] 生成「{mode}」版 (voice_volume={voice_volume}, clip={clip_dur}s, rate={rate})")
    params = build_params(inputs, voice, voice_volume, clip_dur, rate, bgm, bgm_volume)
    resp = api(base, "/api/v1/videos", method="POST", body=params)
    task_id = resp["data"]["task_id"]
    print(f"    task_id={task_id}")
    poll(base, task_id, mode)
    src = mpt_root / "storage" / "tasks" / task_id / "final-1.mp4"
    if not src.is_file():
        print(f"[err] 成片未找到: {src}", file=sys.stderr)
        sys.exit(4)
    dst = out_dir / f"{inputs['issue']}-{mode}.mp4"
    shutil.copyfile(src, dst)
    print(f"[ok] {mode} 版 → {dst}")
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description="short-video-maker MPT 调用器")
    ap.add_argument("--inputs", required=True, help="build_inputs.py 产出的 inputs.json")
    # 默认用云健（阳刚有力、科技/资讯口播），避免云希偏轻柔。可换 zh-CN-YunyangNeural（专业播报）
    ap.add_argument("--voice", default="zh-CN-YunjianNeural-Male", help="edge-tts 音色")
    ap.add_argument("--rate", type=float, default=1.1, help="语速倍率（>1 更快更有精神）")
    ap.add_argument("--bgm", default="", help="指定 BGM 文件名（放在 MPT resource/songs/），留空=随机")
    ap.add_argument("--bgm-volume", type=float, default=0.32, help="BGM 音量（0-1）")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--start-server", action="store_true", help="服务未起则自动拉起")
    ap.add_argument("--voice-only", action="store_true", help="只出有口播版")
    ap.add_argument("--silent-only", action="store_true", help="只出无人声版")
    args = ap.parse_args()

    inputs_path = Path(args.inputs).resolve()
    if not inputs_path.is_file():
        print(f"[err] inputs.json 不存在: {inputs_path}", file=sys.stderr)
        return 2
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    mpt_root = Path(inputs["mpt_root"]).resolve()
    out_dir = inputs_path.parent
    base = f"http://{args.host}:{args.port}"

    n_cards = len(inputs["materials"])
    est_audio = max(1.0, len(inputs["script"]) / CHARS_PER_SEC)
    # 向上取整：N 张卡铺满音频、单遍不回头循环到第 1 张（卡片切换跟着口播段落走）。
    # 略多一点 → 最后一张卡被音频结尾截短，而不是绕回首卡造成结尾错位。
    clip_dur = max(3, math.ceil(est_audio / max(1, n_cards)))
    print(f"[i] {n_cards} 张卡 · 文案 {len(inputs['script'])} 字 · 估时≈{est_audio:.0f}s · 每卡 {clip_dur}s")

    ensure_server(base, mpt_root, args.start_server)

    modes = ["voice", "silent"]
    if args.voice_only:
        modes = ["voice"]
    elif args.silent_only:
        modes = ["silent"]

    results = [run_mode(base, mpt_root, inputs, out_dir, args.voice, clip_dur, m,
                        args.rate, args.bgm, args.bgm_volume) for m in modes]

    # 写 meta.txt（标题/封面建议）
    meta = out_dir / "meta.txt"
    meta.write_text(
        f"issue: {inputs['issue']}\n"
        f"建议标题: {inputs.get('title') or '（待定）'}\n"
        f"封面建议: {inputs.get('cover') or '（无）'}\n"
        f"成片: {', '.join(p.name for p in results)}\n"
        f"发布: 手动上传至 视频号 / 抖音 / 小红书（无自动发布）\n",
        encoding="utf-8")
    print(f"\n[done] {len(results)} 条成片 + meta.txt → {out_dir}")
    print("       下一步：作者预览后手动上传。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())