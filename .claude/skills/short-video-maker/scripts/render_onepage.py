#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker · onepage 速览图渲染器（HTML/CSS → Playwright PNG，零图像额度）

在封面和正文卡片之间插一张"一张图看懂"的速览信息图，提升纯文字卡的可读性。
与 render_cards.py 同源（同一套深蓝#0b1d3a + 红#e63946 编辑风、同样的 9x16 安全区），
**非 AI 风**——文字/数字精确，靠版式而非插画。

内容类型通用：靠 spec 的 block 类型组合，适配
  · 投资逻辑 onepage（stats + versus + compare + actions）
  · 科技速览 onepage（stats + list + actions）
  · 故事人物 onepage（people）

用法:
    python render_onepage.py <onepage.json> --out <dir/xx.png> [--ratio 9x16] [--scale 1]

block 类型（spec.blocks[] 每项一个 type）:
  {"type":"stats","title":..,"items":[{"value","label","tone":up|down|none}]}
  {"type":"versus","left":{"title","items":[]},"right":{...},"verdict":".."}
  {"type":"compare","title":..,"bars":[{"label","pct":0-100,"value"}],"note":..}
  {"type":"actions","title":..,"items":[{"k","v"}]}
  {"type":"list","title":..,"items":["..", {"title","detail"}]}
  {"type":"people","title":..,"items":[{"name","role","note"}]}
"""
import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RATIOS = {"3x4": (1080, 1440), "9x16": (1080, 1920)}
W, H = RATIOS["9x16"]
# 与 render_cards.py 9x16 安全区一致：顶部避刘海、底部留给字幕+视频号 UI
TOP_SAFE = 150
BOTTOM_SAFE = 420


def _esc(s: str) -> str:
    return str(s)


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _stats(b: dict) -> str:
    cells = ""
    for it in b.get("items", []):
        tone = it.get("tone", "none")
        cls = {"up": "v-up", "down": "v-down"}.get(tone, "")
        cells += (f'<div class="stat"><div class="stat-v {cls}">{it.get("value","")}</div>'
                  f'<div class="stat-l">{it.get("label","")}</div></div>')
    title = f'<div class="b-title">{b["title"]}</div>' if b.get("title") else ""
    return f'<div class="block">{title}<div class="stats">{cells}</div></div>'


def _versus(b: dict) -> str:
    def col(side, cls):
        items = "".join(f'<li>{x}</li>' for x in side.get("items", []))
        return f'<div class="vs-col {cls}"><div class="vs-h">{side.get("title","")}</div><ul>{items}</ul></div>'
    left = col(b.get("left", {}), "vs-left")
    right = col(b.get("right", {}), "vs-right")
    verdict = f'<div class="verdict">{b["verdict"]}</div>' if b.get("verdict") else ""
    return f'<div class="block"><div class="versus">{left}<div class="vs-x">VS</div>{right}</div>{verdict}</div>'


def _compare(b: dict) -> str:
    bars = ""
    for bar in b.get("bars", []):
        pct = max(2, min(100, int(bar.get("pct", 0))))
        bars += (f'<div class="bar-row"><div class="bar-label">{bar.get("label","")}</div>'
                 f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%">'
                 f'<span class="bar-val">{bar.get("value","")}</span></div></div></div>')
    title = f'<div class="b-title">{b["title"]}</div>' if b.get("title") else ""
    note = f'<div class="b-note">{b["note"]}</div>' if b.get("note") else ""
    return f'<div class="block">{title}<div class="compare">{bars}</div>{note}</div>'


def _actions(b: dict) -> str:
    rows = ""
    for it in b.get("items", []):
        rows += (f'<div class="act-row"><span class="act-k">{it.get("k","")}</span>'
                 f'<span class="act-v">{it.get("v","")}</span></div>')
    title = f'<div class="b-title">{b["title"]}</div>' if b.get("title") else ""
    return f'<div class="block">{title}<div class="actions">{rows}</div></div>'


def _list(b: dict) -> str:
    rows = ""
    for it in b.get("items", []):
        if isinstance(it, dict):
            d = f'<div class="li-d">{it.get("detail","")}</div>' if it.get("detail") else ""
            rows += f'<div class="li-row"><div class="li-t">{it.get("title","")}</div>{d}</div>'
        else:
            rows += f'<div class="li-row"><div class="li-t">{it}</div></div>'
    title = f'<div class="b-title">{b["title"]}</div>' if b.get("title") else ""
    return f'<div class="block">{title}<div class="list">{rows}</div></div>'


def _people(b: dict) -> str:
    rows = ""
    for i, it in enumerate(b.get("items", []), 1):
        note = f'<div class="pp-note">{it.get("note","")}</div>' if it.get("note") else ""
        rows += (f'<div class="pp-row"><div class="pp-idx">{i}</div>'
                 f'<div class="pp-main"><div class="pp-name">{it.get("name","")}'
                 f'<span class="pp-role">{it.get("role","")}</span></div>{note}</div></div>')
    title = f'<div class="b-title">{b["title"]}</div>' if b.get("title") else ""
    return f'<div class="block">{title}<div class="people">{rows}</div></div>'


_RENDERERS = {"stats": _stats, "versus": _versus, "compare": _compare,
              "actions": _actions, "list": _list, "people": _people}


def _html(spec: dict) -> str:
    kicker = spec.get("kicker", "ONE-PAGE · 一张图看懂")
    title = spec.get("title", "")
    brand = spec.get("brand", "")
    blocks = "".join(_RENDERERS[b["type"]](b) for b in spec.get("blocks", []) if b.get("type") in _RENDERERS)
    head_pad = 64 + TOP_SAFE
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
.page{{width:{W}px;height:{H}px;background:#fff;font-family:'Microsoft YaHei',sans-serif;
  color:#13243f;display:flex;flex-direction:column;overflow:hidden}}
.head{{flex:0 0 auto;padding:{head_pad}px 72px 30px;
  background:linear-gradient(135deg,#0b1d3a 0%,#13315c 55%,#1d4e89 100%);color:#fff}}
.kicker{{font-size:28px;font-weight:700;color:#7fb0e6;letter-spacing:3px;text-transform:uppercase}}
.head h1{{font-size:72px;font-weight:900;line-height:1.1;margin-top:14px}}
.accent{{width:110px;height:10px;background:#e63946;border-radius:5px;margin-top:22px}}
/* 正文区：在安全带内垂直分布 */
.body{{flex:1;display:flex;flex-direction:column;justify-content:space-evenly;
  padding:30px 64px;margin-bottom:{BOTTOM_SAFE}px}}
.block{{}}
.b-title{{font-size:34px;font-weight:800;color:#1d4e89;margin-bottom:18px;
  padding-left:20px;border-left:8px solid #e63946}}
.b-note{{font-size:27px;color:#5a6472;margin-top:14px}}
/* stats */
.stats{{display:flex;gap:18px}}
.stat{{flex:1;background:#f3f6fb;border-radius:18px;padding:24px 10px;text-align:center}}
.stat-v{{font-size:50px;font-weight:900;color:#13243f;font-family:'Arial Black',sans-serif}}
.stat-v.v-up{{color:#c0392b}} .stat-v.v-down{{color:#1e7d4f}}
.stat-l{{font-size:25px;color:#5a6472;margin-top:8px}}
/* versus */
.versus{{display:flex;align-items:stretch;gap:16px;position:relative}}
.vs-col{{flex:1;border-radius:18px;padding:26px 26px}}
.vs-left{{background:#eaf6ef}} .vs-right{{background:#fdecee}}
.vs-h{{font-size:34px;font-weight:800;margin-bottom:14px}}
.vs-col ul{{list-style:none}} .vs-col li{{font-size:29px;line-height:1.5;color:#33405a;
  padding-left:26px;position:relative;margin:8px 0}}
.vs-col li:before{{content:"·";position:absolute;left:6px;color:#e63946;font-weight:900}}
.vs-x{{align-self:center;font-family:'Arial Black',sans-serif;font-size:40px;color:#0b1d3a;
  background:#fff;border:6px solid #0b1d3a;border-radius:50%;width:92px;height:92px;
  display:flex;align-items:center;justify-content:center;position:absolute;left:50%;top:50%;
  transform:translate(-50%,-50%);z-index:2}}
.verdict{{margin-top:20px;background:#0b1d3a;color:#fff;font-size:32px;font-weight:700;
  border-radius:14px;padding:20px 28px;text-align:center}}
/* compare bars */
.compare{{display:flex;flex-direction:column;gap:20px}}
.bar-row{{display:flex;align-items:center;gap:20px}}
.bar-label{{flex:0 0 300px;font-size:31px;font-weight:700;text-align:right;color:#13243f}}
.bar-track{{flex:1;background:#eef1f6;border-radius:12px;height:62px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#e63946,#b71c2c);border-radius:12px;
  display:flex;align-items:center;justify-content:flex-end;padding-right:20px;min-width:90px}}
.bar-val{{color:#fff;font-size:32px;font-weight:900;font-family:'Arial Black',sans-serif}}
/* actions */
.actions{{display:flex;flex-direction:column;gap:16px}}
.act-row{{display:flex;align-items:center;gap:22px;background:#f3f6fb;border-radius:14px;padding:22px 26px}}
.act-k{{flex:0 0 auto;background:#13315c;color:#fff;font-size:27px;font-weight:700;
  border-radius:999px;padding:8px 22px}}
.act-v{{flex:1;font-size:31px;font-weight:700;color:#13243f}}
/* list */
.list{{display:flex;flex-direction:column;gap:16px}}
.li-row{{border-bottom:2px solid #eef1f6;padding-bottom:14px}}
.li-t{{font-size:34px;font-weight:800;color:#13243f}} .li-t b{{color:#1d4e89}}
.li-d{{font-size:28px;color:#5a6472;margin-top:8px}}
/* people */
.people{{display:flex;flex-direction:column;gap:18px}}
.pp-row{{display:flex;gap:22px;align-items:flex-start}}
.pp-idx{{flex:0 0 auto;width:58px;height:58px;border-radius:14px;background:#13315c;color:#fff;
  font-family:'Arial Black',sans-serif;font-size:30px;display:flex;align-items:center;justify-content:center}}
.pp-name{{font-size:36px;font-weight:800;color:#13243f}}
.pp-role{{font-size:27px;color:#e63946;font-weight:700;margin-left:14px}}
.pp-note{{font-size:28px;color:#5a6472;margin-top:6px}}
/* 头部右上角轻量品牌签，替代底部 footer（避免与正文末块重叠） */
.brandtag{{float:right;font-size:25px;font-weight:700;color:#9ec1e8;letter-spacing:1px;margin-top:6px}}
</style></head><body>
<div class="page">
  <div class="head"><span class="brandtag">{brand}</span><div class="kicker">{kicker}</div>
    <h1>{title}</h1><div class="accent"></div></div>
  <div class="body">{blocks}</div>
</div></body></html>"""


def render(spec_path: Path, out: Path, scale: int):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
        page.set_content(_html(spec), wait_until="load")  # 内联 base64 无网络可等，networkidle 是空转
        page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": W, "height": H})
        browser.close()
    print(f"[ok] {out}")


def main():
    ap = argparse.ArgumentParser(description="onepage 速览图渲染器")
    ap.add_argument("spec", help="onepage.json 路径")
    ap.add_argument("--out", required=True, help="输出 PNG 路径")
    ap.add_argument("--ratio", choices=sorted(RATIOS), default="9x16")
    ap.add_argument("--scale", type=int, default=1)
    args = ap.parse_args()
    global W, H
    W, H = RATIOS[args.ratio]
    render(Path(args.spec).resolve(), Path(args.out).resolve(), args.scale)


if __name__ == "__main__":
    main()