---
name: short-video-maker
description: 把现有产出（公众号简报文章 + 贴图图集）转成竖屏短视频（9:16, 1080×1920），基于本地 MoneyPrinterTurbo 引擎，并可自动上传到视频号助手保存草稿。当用户说"做成短视频"、"竖屏视频"、"这期转个视频"、"生成短视频"、"short video"、"把简报做成视频"、"发个视频号/抖音/小红书的视频"时触发。整期内容产出一条 <60s 视频，口播音轨可开关（有 AI 口播 / 仅字幕+BGM 两种）。默认自动存到视频号草稿，作者确认后发布；同期文章同步推公众号【图片消息】草稿（视频号 + 公众号双通道）。
---

# short-video-maker · 竖屏短视频生成

把"已经做好的内容"（一期 `tech-frontier-briefing` 简报，或任意 md 文章 + 配套贴图卡）
转成可直接发视频号/抖音/小红书的**竖屏短视频**。视频引擎用本地开源的
**MoneyPrinterTurbo（MPT）**，本 skill 只负责"喂料 + 编排"。

## 定位与边界
- **复用现有产出**：画面 = 现成的贴图卡；文案 = 现成文章浓缩。不凭空生成新内容。
- **整期一条**竖屏视频。**时长不卡 60s**（作者 2026-06-05 明确：不必 <60s，60–90s 为常态，按内容定）。
- **口播可开关**：默认只出「有口播版」；需要无人声版（仅字幕+BGM）时加 `--also-silent`（复用同一次编码，`-c:v copy` 仅换音轨，近乎免费）。
- **可自动上传视频号草稿**：视频号没有开发者 API，但可用 Playwright 驱动登录态后台
  （同公众号做法）自动上传+填描述/短标题+保存草稿；**默认只存草稿，作者确认后发布**。
  抖音/小红书仍需手动上传成片。
- **视频号 + 公众号双通道**：推完视频号草稿后，把**同一期文章**同步推成公众号【图片消息】草稿
  （复用 `tools/wechat-data/image_post_publisher.py` + 现成 3x4 贴图卡，见 step 8）。两通道各自登录态、各自兜底，互不阻塞。
- 首次使用需一次性环境配置，见 `references/mpt-setup.md`、`references/channels-publish.md`。

## 内容生产标准（MUST · 2026-06 作者定，每条视频都遵守）

1. **封面背景图 = 联网搜免费图，禁用 nano。** nano-banana 这台机器无 API、仅占位，**默认绝不调用**。用 `scripts/fetch_cover_bg.py --query "<主题英文关键词>" --out <bg.jpg>` 取最相关免费图（**Wikimedia 主、Openverse 兜底**，本机 Openverse 常超时），把路径写进 spec.json 的 `cover.background` 再 render_cards。免费搜命中质量不稳时，取多张候选拼联系表人工挑最相关那张。取不到才回退本地 `assets/backgrounds/` 或纯色渐变。
2. **同系列封面按话题分类统一。** 话题类：投资 / 科技 / 故事 / 健康 / 生活 …… 同类同款观感（masthead_en 命名 + tag 文案 + 背景图方向一致）。预设：投资＝金融天际线 bg、tag「投资简报 · …」；科技＝数据中心/电路；**故事＝绣像古籍版**（走 `cards-dongzhou-02-9x16/_src/build_frames_ch.py`，暖褐底，不用 stock 图）；健康＝wellness；生活＝lifestyle。署名统一「英诺为新工坊」。
3. **画面固定三段式：封面 → onepage 汇总页 → 文字卡片页。** onepage 见 step 2.5（`render_onepage.py` 出 `00b-onepage.png`、build_inputs 加 `--onepage`、script 第一行写速览口播、onepage 帧免字幕）。
4. **双音色：封面欢快女声 → 正文清爽男声。** `assemble_synced.py` 已把 `--greeting-voice` 默认设为 `zh-CN-XiaoxiaoNeural`（晓晓），`--voice` 默认 `zh-CN-YunjianNeural`（云健）。

**连带经验（同样 MUST）：**
- **口播每段 ~55 字、字幕最多 2–3 行**，别让段子长到折成 4–5 行（乱）；也别压到只剩几个字（太碎、时长不足）。整片节奏 `--rate 1.05–1.1`。
- **BGM 不强制、可随机**（作者 2026-06-04 放宽）。偏好有节奏的（如 `output007.mp3`）；抒情类（003/006/012/018）作者不太偏好，但非硬性禁用——随机选到也行。
- **贴图文章正文（公众号图片消息）**：浓缩配文 **100–500 字**（作者 2026-06-13 改：下限 100、上限 500，不再顶 1000 塞满），写一段精炼短稿、别截断留"…"。字段「推荐语」技术上限仍约 1000，但内容目标 ≤500。见 memory `wechat-image-post-guide-words-limit`。
- **视频号推草稿**：会话无稳定时效（cookie 名义 ~400 天但服务端常立即作废，以实探为准），多半每次都要重扫；在电脑前屏幕扫，或 `tools/wechat-data/qr_login_channels.py` 把二维码发飞书手机扫（码过期自动重发最新码、上限 4 次、10 分钟超时即停，单进程可停）；扫码超时 `publish_channels.py` 自动经 Go fishing 把成片发作者飞书兜底。

## 前置：MPT 引擎就绪
引擎在 `e:\My-Studio\tools\MoneyPrinterTurbo`（git clone，已 gitignore）。
首次需 `uv sync`，并启动服务。详见 `references/mpt-setup.md`。

## 工作流（8 步）

### 1. 定位源内容
拿到本期 md（如 `content/00 it/01 ai/20260531-tech-frontier-briefing-w23.md`）
和它的贴图卡 spec（`output/wechat-drafts/cards-<issue>/spec.json`）。

### 2. 渲染 9:16 卡
用现有渲染器加 `--ratio 9x16` 重出满帧竖屏卡（避免成片上下黑边）。
**视频用 `--scale 1`**（= 1080×1920，正好是视频帧）——别用 scale 2：
2160×3840 的图进 MoviePy 做 Ken Burns 会慢 ~4 倍（实测每张约 64s vs ~16s），
而成片最终就是 1080×1920，scale 2 是白烧算力。
```
python .claude/skills/tech-frontier-briefing/scripts/render_cards.py \
    output/wechat-drafts/cards-<issue>/spec.json \
    --out output/wechat-drafts/cards-<issue>-9x16 --ratio 9x16 --scale 1
```
目检：1080×1920、文字不溢出。（公众号图片消息仍用 scale 2 出高清，互不影响。）
> **9x16 已内置安全区**：`--ratio 9x16` 时 `render_cards.py` 自动给顶部留 ~160px（避 iPhone 刘海/状态栏）、
> 底部留 ~420px（避视频号账号名/点赞评论分享栏），正文要点在中间安全带垂直分布填满、不再大片留白。
> 注意：这是**烧进视频的静态 PNG 帧**，CSS `env(safe-area-inset-*)`/`viewport-fit=cover` 在 headless
> Chromium 截图里恒为 0、对成片像素无效——安全区只能硬编码进版面，别想当然改回 env()。3x4 不受影响。

### 2.5 onepage 速览图（可选但推荐，提升纯文字卡可读性）
在封面和正文卡之间插一张"一张图看懂"的速览信息图（**HTML/CSS 渲染，零图像额度，非 AI 风**）。
内容类型通用，靠 block 组合适配：投资逻辑（stats+versus+compare+actions）、科技速览（stats+list+actions）、
故事人物（people，如东周列国一篇故事 = 一张人物 onepage）。写 `onepage.json`（block 类型见脚本 docstring），再：
```
python .claude/skills/short-video-maker/scripts/render_onepage.py \
    output/wechat-drafts/cards-<issue>/onepage.json \
    --out output/wechat-drafts/cards-<issue>-9x16/00b-onepage.png --ratio 9x16 --scale 1
```
目检：四块内容在安全带内不溢出、底部留白给字幕。与 render_cards 同套安全区（顶 ~150 / 底 ~420）。
> 用了 onepage：**script 第一行要写对应的速览口播**（段数 = onepage + 卡片数），build_inputs 加 `--onepage`。

### 3. 写竖屏口播文案 + 开场问候（Claude 亲自写，关键步）
读源 md，把 top 要点浓缩成竖屏口播文案，存为 `script.txt`（每段 ~55 字 × 段数；**整片时长不必压进 60s**，60–90s 为常态，按内容定——作者 2026-06-05 明确）。
另写**一行欢快问候开场白**（如"嘿！本周科技圈有三个信号值得你知道——"），存为 `greeting.txt`
——成片以封面 + 这句问候 + 欢快 BGM 开场，再切正文。问候独立于 script.txt，不占正文段落。
写法见 `references/script-writing.md`（前 3 秒钩子、口语化、每段 ~55 字；时长不卡 60s；问候 1 句 2–3 秒）。
**结尾 CTA 必须点名公众号「英诺为新工坊」**——不能只说"关注公众号"（已知易漏，写完检查）。
**不要**交给 MPT 的 LLM 生成——会偏离已核实、带来源的简报内容。

### 4. 构建输入
```
python .claude/skills/short-video-maker/scripts/build_inputs.py \
    --cards output/wechat-drafts/cards-<issue>-9x16 \
    --script <script.txt> --issue <issue> --title "<建议标题>" \
    --greeting-file <greeting.txt> \
    --onepage output/wechat-drafts/cards-<issue>-9x16/00b-onepage.png   # 可选，有 onepage 时加
```
卡片复制进 MPT 素材目录，产出 `output/short-videos/<issue>/inputs.json`（含 `greeting` 字段）。
`--onepage` 会把速览图作为封面后的第一张正文画面前置（materials[0]），对应 script 第一行口播。

### 5. 生成视频（精确同步，默认）
**用 `assemble_synced.py`**——逐段 edge-tts 合成（**并行**，不再逐段串行）、量出每段真实时长、
每张卡精确停留那么久，**画面切换 = 口播分段，不会累积漂移**（这是 v1 用 MPT 均匀切换踩坑后的正解）。
渲染走**原生 ffmpeg 引擎**（`--engine ffmpeg`，默认）：zoompan 做 Ken Burns、ASS(libass) 烧字幕、
AMD `h264_amf` 硬件编码——整片秒级出片（实测 7 段 / 72s 视频，含并行 TTS + 编码 + 口播/无声双版复用 ≈ 25s，
旧 MoviePy 逐帧路径每版要数分钟）。无需启 MPT 服务。必须在 MPT venv 里跑（用其 edge_tts / 字体；ffmpeg 用 imageio-ffmpeg 自带）：
```
cd tools/MoneyPrinterTurbo
# 默认只出口播版
uv run python ../../.claude/skills/short-video-maker/scripts/assemble_synced.py \
    --inputs ../../output/short-videos/<issue>/inputs.json --voice zh-CN-YunjianNeural --rate 1.1
# 需要无人声版（仅字幕+BGM）：加 --also-silent，复用同一次编码（-c:v copy 仅换音轨，近乎免费）
uv run python ../../.claude/skills/short-video-maker/scripts/assemble_synced.py \
    --inputs ../../output/short-videos/<issue>/inputs.json --voice zh-CN-YunjianNeural --rate 1.1 --also-silent
```
出 `<issue>-voice.mp4`（加 `--also-silent` 再多出 `<issue>-silent.mp4`）。BGM：`--bgm <文件名>`；换音色：`--voice`；
卡片本身有字觉得字幕多余：`--no-subtitle`。
**Ken Burns 缓慢放大**默认开、且做 **3 倍超采样**消抖（zoompan 对 x/y 整数取整，1x 会逐帧跳出抖动）：
`--kb-supersample 2`（更快、可能微抖）/ `3`（默认，平衡，<60s 片约 80s 出片）/ `4`（最平滑、最慢）；
`--no-kenburns` 完全静帧（零抖动、最省算力，~25s 出片）。
**编码器**：默认 `--codec amf`（AMD 硬件）；画质异常时 `--codec x264`（libx264 veryfast，吃满 16 线程）。
**兜底引擎**：`--engine moviepy`（旧逐帧路径）留作 ffmpeg 引擎出问题时对照/回退（此引擎 `--also-silent` 不复用、需另渲一遍）。
**开场封面**：自动取 `inputs.json` 的 `cover`，以封面 + 问候口播开场，再切正文——
`--greeting-voice`（问候单独换活泼音色，如 `zh-CN-XiaoxiaoNeural`）、`--cover-tail`（问候后封面多停留秒数，默认 0.6）、`--no-cover`（关闭开场封面）。
**开场欢快感靠 `--bgm` 指定一首欢快曲**（BGM 现已贯穿开场+正文整片）。
> **码率/体积**：默认 2M 码率（静态卡片足够清晰），<60s 成片 ≈15MB——确保能走飞书 DM 手机端兜底
> （视频上限实测 ~15–28MB，超限上传被拒）。要更高画质发视频号可临时 `--codec x264`（CRF 20 文件略大）。
> 前提：script.txt **一行=一段=一张卡**，行数 = 卡片数（见 step 3 / script-writing.md）。
> 旧的 `run_mpt.py`（MPT 均匀切换、需启服务）保留为备用，但**默认用 assemble_synced.py**。

### 6. 交付成片
成片在 `output/short-videos/<issue>/`，附 `meta.txt`（建议标题/封面）+ `cover.png`。
成片以**封面 + 问候口播 + 欢快 BGM 开场**，随后切正文（封面已烧进首帧，无需手动加）。
向作者报告：路径、两版差异、建议标题与封面。

### 7. 上传视频号草稿（默认存草稿，作者确认发布）
```
python tools/wechat-data/publish_channels.py \
    --video output/short-videos/<issue>/<issue>-voice.mp4 \
    --title "<短标题>" --desc "<视频描述，可含 #话题>"
```
弹出浏览器后**作者扫码登录**（视频号会话无稳定时效，多半每次发布都要重扫一次码），脚本自动：
上传视频 → 等"取消上传"消失（真完成）→ 填描述+短标题 → 点「保存草稿」。
作者去 视频号助手 → 草稿箱 确认后发布。`--publish` 可直接发表；`--manual-save` 只填不点。
详见 `references/channels-publish.md`。抖音/小红书暂无自动化，用成片手动传。

**📱 手机端兜底（不在电脑边、扫不了码时）**：成片经 **Go fishing 飞书机器人**直接 DM 给作者，
手机上即可查看/转发，或对照描述手动在视频号 App 发布。两种触发：
- **主动直发**（已知在手机上）：加 `--to-feishu`，跳过浏览器、不扫码，直接发飞书。
  ```
  python tools/wechat-data/publish_channels.py \
      --video output/short-videos/<issue>/<issue>-voice.mp4 \
      --title "<短标题>" --desc "<描述>" --to-feishu
  ```
- **自动兜底**（默认开）：正常跑上传命令，若扫码超时（3 分钟未登录），自动把成片发飞书；
  `--no-feishu-fallback` 可关闭。封面默认取视频同级 `cover.png`，飞书里以可播放视频呈现（失败降级文件附件）。

> 发送器：`tools/feishu-bridge/send_media.py`（复用 Go fishing 的 `.env` 凭证，scope: im:resource +
> im:message:send_as_bot）。收件人默认取 `.env` 的 `FEISHU_ALLOWED_OPEN_IDS` 首个（即作者）。
> 也可单独调用：`python tools/feishu-bridge/send_media.py --video <mp4> --cover <png> --text "<描述>"`。

### 8. 同步推公众号图片消息草稿（视频号 + 公众号双通道）
**⚡ 与 step 7 并行（省串行空等）**：step 8（公众号，cookie 自动、无需人工）与 step 7（视频号，需人工扫码）
各自登录态、互不阻塞——把 step 8 放**后台并发**启动，作者扫视频号码的同时公众号已在上传。
（编排：step 7 命令前台跑等扫码，step 8 命令以 `run_in_background` 同时起；两边各自兜底，互不阻塞。）

把**同一期文章**推成公众号【图片消息】草稿，用现有
`tools/wechat-data/image_post_publisher.py`（零新代码，复用 `tech-frontier-briefing` 的发布链）。
- **复用既有产物**：图集用 **3x4 高清卡** `output/wechat-drafts/cards-<issue>`（tech-frontier-briefing
  Step 3 `--scale 2` 产出，首张 `00-cover.png` 即封面）——**别用 9x16 的视频卡**；正文用
  `output/wechat-drafts/cards-<issue>/body.txt`（tech-frontier-briefing Step 4 产出）。
- **前置缺失就先补**：若 3x4 卡 / body.txt 还没生成（纯从视频侧起步），先出 3x4 卡、由源 md 整理 body.txt：
```
python .claude/skills/tech-frontier-briefing/scripts/render_cards.py \
    output/wechat-drafts/cards-<issue>/spec.json \
    --out output/wechat-drafts/cards-<issue> --scale 2
```
- **推草稿**：
```
cd tools/wechat-data
python image_post_publisher.py \
    --images ../../output/wechat-drafts/cards-<issue> \
    --title "<公众号标题 ≤20字>" \
    --body-file ../../output/wechat-drafts/cards-<issue>/body.txt
```

**要点（易错，写完检查）：**
- **公众号标题 ≤20字**，与视频短标题是两个文案，别直接复用视频短标题。
- **正文 100–500字**：浓缩成精炼短稿（作者 2026-06-13 改，下限 100 上限 500，不再顶 1000 塞满），别截断留"…"（memory `wechat-image-post-guide-words-limit`，同 step 标准第 31 行）。
- **推前核账号**：确认登录的是 `nick_name=英诺为新工坊`、用活动 cookie，不路由不 Banner（memory `wechat-image-post-account-routing`）。
- **默认只存草稿**：`image_post_publisher.py` 默认即建草稿，不要加任何直发标志。
- **推完独立验证**：登录"英诺为新工坊"后台，确认草稿箱确有一条【图片消息】草稿（不是文章）、图集与标题正确，再向作者报告（参照 tech-frontier-briefing Step 5 验证纪律）。

## 模式二：--auto-footage（关键词自动配画，独立于上面的贴图卡模式）

上面 8 步是【贴图卡模式】（画面=现成卡，靠 `assemble_synced.py` 出片）——**仍是默认、主线**。
本模式是**另一条独立路径**：没有现成卡、口播偏氛围/空镜时，给关键词 + 口播稿，
让 MPT 联网搜 Pexels 免费 HD 竖屏素材自动配画。脚本 `scripts/auto_footage.py`
**不改动**贴图卡流水线的任何代码（`build_inputs` / `assemble_synced` / `run_mpt` / `render_cards` 原样不动），
两条路径互不影响——其它几类已定专门模式（投资/科技/故事绣像/健康…）照旧。

**何时用**：科技、情绪、自然、城市等**氛围/空镜**主题。
**何时别用**：靠具体食材/人物/数据说话的主题——Pexels 是英文 stock 库，
「黑豆」会被搜成咖啡豆、「当归」根本没有（实测）。这类**仍走贴图卡模式**。

**字幕安全区（本模式已内置）**：MPT 原生 `subtitle_position="bottom"` 把字幕压到距底仅 ~96px
（`video.py:762`：`y=0.95*1920-clip_h`），会被视频号账号名/点赞栏盖住；本模式强制
`subtitle_position="custom" + custom_position=72`（`video.py:765-774`：`y=(1920-clip_h)*P/100`），
字幕底边落在距底 ~500px，避开视频号底部 UI，与贴图卡 9x16 渲染器预留的 ~420px 底部安全区对齐。

**醒目封面标题（本模式已内置）**：`--title` 非空时，开头 `--cover-seconds`（默认 3s）叠一张
**大号粗黑体标题**（PIL 渲染、半透明圆角衬底 + 白字粗描边、自动折行、上中部 ~33% 处，
避开顶部刘海与底部字幕带），淡入淡出后自动消失——既是开场钩子，也是平台**封面缩略帧**。
`--no-cover-title` 关闭。实现：PIL 出透明 PNG → ffmpeg `-loop 1 -t` 成时长流再 overlay（整片重编码、音轨 copy）。

**用法**（必须在 MPT venv 里跑；zero-LLM，只需 config.toml 已注入的 pexels key）：
```
cd tools/MoneyPrinterTurbo
uv run python ../../.claude/skills/short-video-maker/scripts/auto_footage.py \
    --issue <issue> \
    --terms "city night, technology, neon city skyline, future" \
    --script ../../output/short-videos/<issue>/script.txt \
    --title "<建议标题>" --voice zh-CN-YunjianNeural-Male --rate 1.05
# 需要无人声版：加 --also-silent（MoviePy 路径需再完整渲一遍，不像 ffmpeg 能 -c:v copy 复用）
```
出 `output/short-videos/<issue>/<issue>-autofootage.mp4`（+meta.txt）。
其它参数：`--concat random|sequential`、`--clip-duration`、`--custom-position`（字幕位，默认 72）、
`--cover-seconds`（封面标题时长，默认 3）、`--no-cover-title`（关掉封面标题）、
`--bgm <名>`/`--bgm-volume`、`--no-subtitle`、`--also-silent`、`--out-dir`。

**速度（实测）**：走 MPT 原生 MoviePy（非本项目 ffmpeg 快路），约一半时间在联网下载 HD 素材、
另一半在 MoviePy。16s 成片 ~154s、20s 成片 ~190s；更长成片下载+渲染两头都线性上涨。要快/要精确同步仍用贴图卡模式。

**配图必核**：关键词自动抓的素材**只蹭氛围、不保证语义对**（每个词 Pexels 返回 15-20 条，MPT 默认抓前几条不挑）。
出片后**务必抽帧目检**，错配明显就换搜索词重跑或改走贴图卡模式。

## 默认参数
- 画幅 9:16 (1080×1920)；字幕 `edge`（在 MPT config.toml 配，无需 GPU）。
- 默认音色 `zh-CN-YunjianNeural-Male`（**云健，阳刚有力，科技/资讯口播**，避免轻柔）；
  语速 `--rate 1.1`（更有精神）。专业播报换 `zh-CN-YunyangNeural`，女声 `zh-CN-XiaoxiaoNeural-Female`。
- **BGM 求科技感**：默认随机库不够"科技"。把一首免版权电音/科技 BGM 放进
  `tools/MoneyPrinterTurbo/resource/songs/`，用 `run_mpt.py --bgm <文件名>` 指定（音量 `--bgm-volume`，默认 0.32）。
  来源：Pixabay Music / YouTube 音频库 搜 "tech / electronic / corporate"。
- 每卡时长按文案估时自动分配（run_mpt.py 内置，保证每张卡都出镜、不丢卡）。
- **结尾必报公众号名「英诺为新工坊」**（见 step 3 / script-writing.md，已知易漏点）。
- **开场**：封面 + 问候口播（`inputs.greeting`）+ 欢快 BGM；问候时长实测、封面随之停留（+`--cover-tail` 0.6s）；内容旁白延后开场时长起播，音画同步不受影响。
- **字幕自适应**：长句自动缩字号（块高 ≤ 画面 30%）并按真实高度底部锚定（距底 10%），多行不裁切。

## 关键实现事实（改脚本前先读，避免想当然）
- 静音版 = `voice_volume=0.0`：TTS 仍跑（提供字幕时间轴+定时长），旁白被静音；
  字幕、BGM 照常。**不要**用 `custom_audio_file` 做静音——它会连字幕一起禁掉
  （`tools/MoneyPrinterTurbo/app/models/schema.py` 注释）。
- 本地图片素材必须落在 `<mpt>/storage/local_videos/`，`video_materials[].url` 只传文件名。
- API：`POST /api/v1/videos` → 轮询 `GET /api/v1/tasks/{id}`（state: 1 完成 / -1 失败）
  → 成片 `<mpt>/storage/tasks/{id}/final-1.mp4`。
- 提供 `video_script` 时跳过 LLM；`video_source=local` 时跳过 Pexels/关键词——**无需任何 API key**。
