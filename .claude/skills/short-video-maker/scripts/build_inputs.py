#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker · 输入桥接器

把"现有产出"（一期简报的 9:16 贴图卡 + Claude 写好的竖屏口播文案）整理成
MoneyPrinterTurbo(MPT) 可直接消费的输入：

1. 把卡片 PNG 按序复制进 MPT 的本地素材目录 <mpt>/storage/local_videos/，
   命名为 <issue>-01.png, <issue>-02.png ...（前缀避免多期共用目录时撞名）。
   依据：MPT preprocess_video() 要求素材落在 storage/local_videos/ 内，
   且 FILE_TYPE_IMAGES 含 png（app/services/video.py / app/models/const.py）。
2. 跳过 00-cover.png（留作封面建议，不进正文画面）。
3. 写出 inputs.json（issue / title / script / 有序素材文件名 / 封面路径），
   供 run_mpt.py 读取后调 MPT API。

用法:
    python build_inputs.py --cards <9x16卡目录> --script <script.txt> --issue w23 \
        [--title "标题"] [--mpt <MPT根目录>] [--out <输出目录>]

注意:
    --cards 必须是 9:16(1080x1920) 的卡目录（用 render_cards.py --ratio 9x16 生成）。
    3:4 卡也能跑，但 MPT 会用黑边补齐到 9:16（app/services/video.py combine_videos），成片有上下黑条。
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

DEFAULT_MPT = Path(r"e:\My-Studio\tools\MoneyPrinterTurbo")
DEFAULT_OUT_ROOT = Path(r"e:\My-Studio\output\short-videos")


def collect_card_pngs(cards_dir: Path) -> list[Path]:
    """取卡目录里的正文 PNG（按文件名排序，排除 00-cover*）。"""
    pngs = sorted(p for p in cards_dir.glob("*.png"))
    body = [p for p in pngs if not p.stem.startswith("00") and "cover" not in p.stem.lower()]
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description="short-video-maker 输入桥接器")
    ap.add_argument("--cards", required=True, help="9:16 贴图卡目录")
    ap.add_argument("--script", required=True, help="Claude 写好的竖屏口播文案 .txt")
    ap.add_argument("--issue", required=True, help="期号/标识，如 w23")
    ap.add_argument("--title", default="", help="建议标题（≤~20字），可空")
    ap.add_argument("--greeting", default="", help="开场问候语（一句活力问候，封面期间口播），可空")
    ap.add_argument("--greeting-file", default="", help="从文件读开场问候语（与 --greeting 二选一）")
    ap.add_argument("--onepage", default="", help="可选：onepage 速览图 PNG，插在封面后/正文卡前作第一张画面；"
                                                  "此时 script 第一行应为对应的速览口播（段数 = onepage + 卡片数）")
    ap.add_argument("--mpt", default=str(DEFAULT_MPT), help="MoneyPrinterTurbo 根目录")
    ap.add_argument("--out", default="", help="输出目录（默认 output/short-videos/<issue>）")
    args = ap.parse_args()

    cards_dir = Path(args.cards).resolve()
    script_path = Path(args.script).resolve()
    mpt_root = Path(args.mpt).resolve()
    out_dir = Path(args.out).resolve() if args.out else (DEFAULT_OUT_ROOT / args.issue)

    # —— 校验 ——
    if not cards_dir.is_dir():
        print(f"[err] 卡目录不存在: {cards_dir}", file=sys.stderr)
        return 2
    if not script_path.is_file():
        print(f"[err] 文案文件不存在: {script_path}", file=sys.stderr)
        return 2
    script_text = script_path.read_text(encoding="utf-8").strip()
    if not script_text:
        print(f"[err] 文案为空: {script_path}", file=sys.stderr)
        return 2
    greeting_text = args.greeting.strip()
    if args.greeting_file:
        gpath = Path(args.greeting_file).resolve()
        if not gpath.is_file():
            print(f"[err] 问候语文件不存在: {gpath}", file=sys.stderr)
            return 2
        greeting_text = gpath.read_text(encoding="utf-8").strip()
    local_videos = mpt_root / "storage" / "local_videos"
    if not mpt_root.is_dir():
        print(f"[err] MPT 根目录不存在: {mpt_root}（先 git clone + uv sync）", file=sys.stderr)
        return 2

    cards = collect_card_pngs(cards_dir)
    if not cards:
        print(f"[err] 卡目录里没有正文 PNG（已排除封面）: {cards_dir}", file=sys.stderr)
        return 2

    # —— 复制素材进 MPT local_videos，按 <issue>-NN.png 命名 ——
    local_videos.mkdir(parents=True, exist_ok=True)
    # 先清掉本期旧素材，避免上一次运行的残留串进来
    for stale in local_videos.glob(f"{args.issue}-*.png"):
        stale.unlink()
    material_files: list[str] = []
    # onepage 速览图（若提供）作为封面后的第一张画面，前置进 materials
    if args.onepage:
        op_src = Path(args.onepage).resolve()
        if not op_src.is_file():
            print(f"[err] onepage 不存在: {op_src}", file=sys.stderr)
            return 2
        op_name = f"{args.issue}-00onepage.png"
        shutil.copyfile(op_src, local_videos / op_name)
        material_files.append(op_name)
        print(f"[ok] onepage {op_src.name} → storage/local_videos/{op_name}（首张正文画面）")
    for i, src in enumerate(cards, start=1):
        name = f"{args.issue}-{i:02d}.png"
        shutil.copyfile(src, local_videos / name)
        material_files.append(name)
        print(f"[ok] 素材 {src.name} → storage/local_videos/{name}")

    # —— 封面建议：复制 00-cover 到输出目录（若存在）——
    out_dir.mkdir(parents=True, exist_ok=True)
    cover_src = next((p for p in sorted(cards_dir.glob("*.png"))
                      if p.stem.startswith("00") or "cover" in p.stem.lower()), None)
    cover_out = ""
    if cover_src:
        cover_out = str(out_dir / "cover.png")
        shutil.copyfile(cover_src, cover_out)
        print(f"[ok] 封面建议 → {cover_out}")

    # —— 写 inputs.json ——
    inputs = {
        "issue": args.issue,
        "title": args.title,
        "greeting": greeting_text,     # 开场问候语（封面期间口播），空则开场仅封面静止
        "script": script_text,
        "materials": material_files,   # 仅文件名；MPT 在 storage/local_videos/ 内解析
        "cover": cover_out,
        "mpt_root": str(mpt_root),
    }
    inputs_path = out_dir / "inputs.json"
    inputs_path.write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[done] {len(material_files)} 张素材就绪，inputs.json → {inputs_path}")
    print(f"       下一步: python run_mpt.py --inputs \"{inputs_path}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())