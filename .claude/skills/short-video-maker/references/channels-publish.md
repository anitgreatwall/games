# 视频号助手 自动上传（publish_channels.py）

脚本：`tools/wechat-data/publish_channels.py`（与公众号发布器同处，复用 cookie 目录约定）。
用 Playwright 驱动登录态的视频号助手后台 `channels.weixin.qq.com`，自动上传短视频并保存草稿。
**视频号没有开发者投稿 API**，但后台可被浏览器自动化驱动——同 `wechat-data/publisher.py` 驱动公众号的做法。

## 用法

```
# 默认：上传 + 填描述/短标题 + 保存草稿
python tools/wechat-data/publish_channels.py \
    --video output/short-videos/w23/w23-voice.mp4 \
    --title "本周科技前沿三个信号" \
    --desc "本周海内外科技前沿，三个值得留意的信号。#科技 #AI"

--publish        # 直接发表（默认只存草稿）
--manual-save    # 只上传+填字段，不点任何按钮，作者手动点
--desc-file f    # 从文件读视频描述
--inspect        # 仅登录并 dump 页面诊断（不上传），用于选择器校准
```

## 登录与会话

- 首次/会话失效时弹浏览器扫码（`headless=False`）。
- **别把"cookie 名义寿命"当成"会话有效期"——两回事**：
  - 扫码存下的 `sessionid`/`wxuin` 这两个鉴权 cookie，`expires` 在 ~400 天后（微信服务器设的名义寿命）。
  - 但服务端 session 在自动化复用下并不可靠：storage_state 跨浏览器实例重放、或有并发/二次登录时，
    微信常把服务端 session **立即作废**——这时 cookie 文件还在、`expires` 还是 400 天，但服务器已不认。
  - 所以实践上经常**每次发布都要重扫**。这是视频号的限制，不是 bug。
- 注意：**不要同时开多个浏览器实例**用同一登录态，会触发视频号单会话失效。
- **不在电脑边时**：`tools/wechat-data/qr_login_channels.py` 无头开登录页、把二维码经 Go fishing 发作者手机扫。
  二维码有时效——脚本在等待期持续重截当前码，页面里的码一变就重发"最新码"（旧码作废）；
  重发上限 `MAX_QR_SENDS=4`、整体 `LOGIN_TOTAL_S=600s` 超时即停。stdout：`SENT #n`/`LOGIN_OK`/`QR_SEND_CAP`/`LOGIN_TIMEOUT`。
  **单进程自管刷新，别在外层循环重跑发码**；要停就杀这个进程。
- 因此脚本**不靠任何时间阈值判断 cookie 是否有效**：`cookie_valid()` 只看文件是否存在，
  能否复用以 `editor_ready()` 实探为准（见下条）。失效就自动回退扫码。
- 登录判断用**内容**（编辑器是否出现"上传提示"/「保存草稿」按钮），不能用 URL——
  未登录时 URL 仍是 `/platform/post/create` 但渲染的是二维码登录页。

## 页面真实结构（实测，改脚本前必读）

- 编辑器外层 `channels.weixin.qq.com/platform/post/create`，内嵌 iframe `/micro/content/post/create`。
- **真正的 `<input type=file>` 在主框架（/platform/...），不在 /micro iframe**。
  所以 `do_upload` 逐个 frame 尝试 `set_input_files`（主框架优先），再退回 file_chooser。
- **视频描述是 contenteditable**（属性可能是 `contenteditable=""`，不是 `"true"`）——
  用 `[contenteditable]:not([contenteditable="false"])` 定位，点击后 `keyboard.insert_text` 输入。
- 短标题是普通 `<input>`，placeholder = `填写短标题有机会获得更多流量`。
- 按钮：`保存草稿` / `发表` / `直接发表`（发表后可能的确认）。
- **上传完成信号 = 「取消上传」按钮消失**。不要用"上传提示文字消失"——那在上传刚开始(0%)就触发，
  会导致在视频没传完时就保存空草稿（踩过坑：草稿箱 0）。

## 调试

- 关键步骤截图：`tools/wechat-data/_channels_shots/0*.png`（01-loaded / 02-after-upload / 03-after-fill / 04-after-save）。
- 任一步定位失败 → 转储 `tools/wechat-data/_channels_probe.json`（遍历 iframe + shadow DOM 的按钮/placeholder/input 清单），据此校准 `SEL`。
- 两者都在 `.gitignore` 里，不进版本库。