#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""short-video-maker 配套 · 封面背景图自动取（免费图源，零 API key，禁用 nano）

按主题关键词在 Openverse（CC 授权聚合，免 key）搜最相关的免费图片下载当封面底图；
Openverse 不可用时回退 Wikimedia Commons 搜索。**不调用 nano-banana / 任何付费图像 API。**
（放在 tools/ 而非 .claude/skills/scripts/ 是因该机器对技能目录写入需单独授权。）

用法:
    python fetch_cover_bg.py --query "stock market finance skyline" --out <path.jpg> [--orientation landscape] [-n 8]

返回（stdout 末行）: PICKED <url> | <license> ——便于文末署名/留档。
退出码 0 成功 / 非 0 失败（失败不写文件，调用方应回退本地 assets 或纯色渐变）。
"""
import argparse
import hashlib
import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "my-studio-shortvideo/1.0 (cover bg fetch; sheng.chang@pangeo.com)"
OPENVERSE = "https://api.openverse.org/v1/images/"
WIKI_API = "https://commons.wikimedia.org/w/api.php"
# 命中缓存避免重复联网（按 query+orientation）；落仓库 output/_tmp/，遵守临时落盘约定。
# parents: scripts→short-video-maker→skills→.claude→<repo root>
CACHE_DIR = Path(__file__).resolve().parents[4] / "output" / "_tmp" / "cover-cache"


def _get(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _download(url, out):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=15).read()
        if len(data) < 8000:
            return False
        with open(out, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"[warn] 下载失败 {url[:60]}: {e}", file=sys.stderr)
        return False


def _cache_key(query, orientation):
    return hashlib.sha1(f"{query}|{orientation}".encode("utf-8")).hexdigest()[:16]


def _cache_get(key, out):
    img = CACHE_DIR / f"{key}.img"
    if img.is_file() and img.stat().st_size >= 8000:
        shutil.copy(img, out)
        meta = CACHE_DIR / f"{key}.txt"
        return meta.read_text(encoding="utf-8").strip() if meta.is_file() else "cache"
    return None


def _cache_put(key, out, attribution):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(out, CACHE_DIR / f"{key}.img")
        (CACHE_DIR / f"{key}.txt").write_text(attribution, encoding="utf-8")
    except Exception as e:
        print(f"[warn] 缓存写入失败: {e}", file=sys.stderr)


def from_openverse(query, out, orientation, n):
    q = urllib.parse.urlencode({"q": query, "page_size": n, "orientation": orientation,
                                "license_type": "all-cc", "mature": "false"})
    try:
        data = json.loads(_get(f"{OPENVERSE}?{q}"))
    except Exception as e:
        print(f"[warn] Openverse 失败: {e}", file=sys.stderr)
        return None
    for r in data.get("results", []):
        url = r.get("url") or ""
        if url and _download(url, out):
            lic = f"{r.get('license','')} {r.get('license_version','')}".strip()
            return url, f"Openverse · {r.get('source','')} · {lic}"
    return None


def from_wikimedia(query, out, n):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search",
                                "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": "6",
                                "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size", "iiurlwidth": "1600"})
    try:
        data = json.loads(_get(f"{WIKI_API}?{q}"))
    except Exception as e:
        print(f"[warn] Wikimedia 失败: {e}", file=sys.stderr)
        return None
    pages = (data.get("query", {}) or {}).get("pages", {})
    cands = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        u = ii.get("thumburl") or ii.get("url")
        w, h = ii.get("width", 0), ii.get("height", 0)
        if u and w >= h:
            cands.append((w, u, p.get("title", "")))
    cands.sort(reverse=True)
    for _, u, title in cands:
        if _download(u, out):
            return u, f"Wikimedia Commons · {title}"
    return None


def main():
    ap = argparse.ArgumentParser(description="封面背景图自动取（免费图源，禁用 nano）")
    ap.add_argument("--query", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--orientation", default="landscape", choices=["landscape", "portrait", "square"])
    ap.add_argument("-n", type=int, default=8)
    args = ap.parse_args()
    # 0. 缓存命中即时返回（避免重复联网；同 query+orientation 重跑秒出）
    key = _cache_key(args.query, args.orientation)
    cached = _cache_get(key, args.out)
    if cached:
        print(f"[ok] 缓存命中 → {args.out}")
        print(f"PICKED cache | {cached}")
        return 0
    # 本机 Openverse 常超时 → Wikimedia 为主、Openverse 兜底
    got = from_wikimedia(args.query, args.out, args.n)
    if not got:
        print("[i] 回退 Openverse …", file=sys.stderr)
        got = from_openverse(args.query, args.out, args.orientation, args.n)
    if not got:
        print("[err] 未取到免费图，回退本地 assets/纯色渐变。", file=sys.stderr)
        return 3
    url, attribution = got
    _cache_put(key, args.out, attribution)
    print(f"[ok] 已下载 → {args.out}")
    print(f"PICKED {url} | {attribution}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
