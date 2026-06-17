# MoneyPrinterTurbo 环境配置（Windows）

短视频引擎是本地的 MoneyPrinterTurbo（MPT），位于 `e:\My-Studio\tools\MoneyPrinterTurbo`
（git clone，已 gitignore，不入版本库）。本 skill 只编排，不改 MPT 源码。

## 一次性安装

```powershell
# 1. clone（若尚未）
git clone --depth 1 https://github.com/harry0703/MoneyPrinterTurbo.git e:\My-Studio\tools\MoneyPrinterTurbo

# 2. 装 uv（若无）
python -m pip install uv

# 3. 同步依赖（uv 会按 .python-version 自动装 Python 3.11 + 建虚拟环境）
cd e:\My-Studio\tools\MoneyPrinterTurbo
uv sync
```

## 依赖说明（实测自 MPT 源码，非推断）

- **FFmpeg**：无需手动装。`app/services/video.py:get_ffmpeg_binary()` 在 PATH 找不到时，
  回退到 `imageio_ffmpeg.get_ffmpeg_exe()` 自动下载。仅当自动下载失败才需在 config.toml
  设 `ffmpeg_path`（反斜杠写成 `\\`）。
- **ImageMagick**：本版 MPT 用 MoviePy 2.x（`from moviepy import TextClip`，走 Pillow 渲染字幕），
  通常**不需要** ImageMagick。仅当字幕渲染报错时，再装 static 版并在 config.toml 设
  `imagemagick_path`。下载：https://imagemagick.org/archive/binaries/ （选 `*-static.exe`）。
- **LLM / Pexels key**：本 skill 全程用「自定义文案 + 本地素材」，
  `generate_script` 见 `video_script` 非空即跳过 LLM（`app/services/task.py:18`），
  `video_source=local` 跳过 Pexels（`task.py:270`）。**两类 key 都留空即可**。
- **edge-tts 联网**：口播用微软 edge-tts 在线服务，需可访问外网（国内可能需代理）。

## config.toml

首次启动时 MPT 自动从 `config.example.toml` 复制出 `config.toml`（`app/config/config.py:132`）。
默认值已满足本 skill：`subtitle_provider = "edge"`、`pexels_api_keys = []`、`listen_port = 8080`。
一般无需手动改。

## 启动 API 服务

```powershell
cd e:\My-Studio\tools\MoneyPrinterTurbo
uv run python main.py
# 监听 0.0.0.0:8080，文档 http://127.0.0.1:8080/docs
```

服务建议常驻（跨多期复用，省启动开销）。`run_mpt.py` 会先健康检查；
未启动时可加 `--start-server` 让脚本自动拉起（Popen，不随脚本退出而关闭）。

## API 契约（实测自 `app/controllers/v1/video.py` + `app/models/schema.py`）

- `POST /api/v1/videos` body=VideoParams → `{"data":{"task_id": "..."}}`
- `GET  /api/v1/tasks/{task_id}` → `{"data":{"state":1|-1|4,"progress":N,"videos":[...]}}`
  - state：1 完成 / -1 失败 / 4 处理中（`app/models/const.py`）
- 成片落盘：`<mpt>/storage/tasks/<task_id>/final-1.mp4`
- 本地素材落盘：`<mpt>/storage/local_videos/`（`video_materials[].url` 只传文件名）

## 关键 VideoParams 字段（本 skill 用到的）

| 字段 | 取值 | 说明 |
|------|------|------|
| `video_script` | 文案全文 | 非空 → 跳过 LLM |
| `video_source` | `"local"` | 用本地素材 |
| `video_materials` | `[{provider:"local",url:"w23-01.png",duration:N}]` | 有序卡片 |
| `video_aspect` | `"9:16"` | → 1080×1920 |
| `video_concat_mode` | `"sequential"` | 保卡片顺序 |
| `video_clip_duration` | 整数秒 | 每卡时长（含 Ken Burns 缩放） |
| `voice_name` | `zh-CN-YunxiNeural-Male` 等 | edge-tts 音色 |
| `voice_volume` | `1.0` / `0.0` | 1.0 有口播；0.0 静音旁白（字幕+BGM 仍在） |
| `subtitle_enabled` | `true` | 字幕开 |
| `bgm_type` | `"random"` | 取 resource/songs；空目录→无 BGM，不报错 |

## 故障排除

| 现象 | 原因 | 处理 |
|------|------|------|
| 任务 state=-1，日志提 audio | edge-tts 联网失败 | 开代理 / 检查网络 |
| 成片有上下黑边 | 用了 3:4 卡 | 用 `render_cards.py --ratio 9x16` 重出卡 |
| 字幕渲染异常 | MoviePy 字体/ImageMagick | 装 static ImageMagick 并配 `imagemagick_path` |
| `RuntimeError: No ffmpeg` | 自动下载失败 | 手动下 ffmpeg，config.toml 设 `ffmpeg_path` |
| 后面的卡没出现 | 文案过短、clip 过长 | run_mpt 已按估时分配 clip，正常不会发生；若发生缩短 clip_dur |