# lino-local-vision — 本地视觉 Agent Skill

> 🎯 **DeepSeek 没有多模态？Reasonix 接 DeepSeek API 不能识图？**
> 这是给 DeepSeek / 文本大模型补上"眼睛"的本地方案：LM Studio + Qwen3-VL 视觉模型，**纯本地、不走网络、不需要 API key、无费用**。图片完全在本机推理，隐私安全，离线可用。

Local vision skill: run Qwen3-VL on your own machine via LM Studio. Fully offline, free, no API key, no data leaves your computer. **DeepSeek & other text-only LLMs can't see images — this gives them vision, locally.**

## 为什么要这个 / Why

- **DeepSeek V4 Flash 等文本模型没有多模态识图能力**——发图片只能"干瞪眼"，读 PDF/图片只是抽文字，图片本身看不了
- **Reasonix / Claude Code / Codex 接 DeepSeek API 也一样不能识图**——识图需要多模态模型
- 本 skill 用 **Qwen3-VL（阿里开源多模态模型）**补上这块：看图、OCR、图片描述全部本地完成
- 中文教学视频（B站）：[DeepSeek V4 Flash 刚发布，但还不能识图！用 Reasonix + LM Studio 本地跑 Qwen3-VL，免费离线](https://www.bilibili.com/video/BV1jT3R6jEZk/)

## 依赖 / Dependencies

1. **LM Studio**（https://lmstudio.ai ）—— 启动本地 OpenAI 兼容服务（默认端口 1234）
2. **视觉模型**（在 LM Studio 的 Model 搜索里下载，或从 ModelScope / HuggingFace 的 `lmstudio-community` 组织下载）：
   - 推荐：`qwen3-vl-8b-instruct`（官方指令版，无思维链、直接输出，识别更准）
   - 备选：`qwen3.5-9b-uncensored-hauhaucs-aggressive`（第三方社区模型，带思维链，需压 reasoning）
   - ⚠️ 坑：模型配套的 **mmproj 投影文件**一旦丢失，模型会退化为纯文本（报 `does not support image inputs`），需重新下载 mmproj 并 `lms unload --all` 后重载。
3. **Python 3.9+** + `pip install pillow`（脚本只用标准库 + Pillow）

## 启动 LM Studio / Start

```powershell
# 检查服务（端口 1234）
Test-NetConnection 127.0.0.1 -Port 1234 -WarningAction SilentlyContinue -InformationLevel Quiet

# 启动（lms CLI 默认在 $env:USERPROFILE\.lmstudio\bin\lms.exe，路径因安装方式而异）
& "$env:USERPROFILE\.lmstudio\bin\lms.exe" server start
& "$env:USERPROFILE\.lmstudio\bin\lms.exe" status   # 确认 Server: ON + 已加载模型
```

> LM Studio 设置里 `enableLocalService` 必须为 true（或使用 `lms server start`）。

## 用法 / Usage

```powershell
python scripts/analyze.py --image <图片路径> [选项]
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--image` | （必填） | 本地图片路径 |
| `--prompt` | `用一句话描述这张图片的内容` | 对图片的问题/指令 |
| `--max-tokens` | `2048` | 回答上限；思维链会先消耗 token，若"只有 thinking、正式回答为空"，调大它 |
| `--max-width` | `256` | 图片缩放最大宽度。默认省 token；识别游戏/UI/小字等细节用 `768-1024` |
| `--reasoning-effort` | `minimal` | `minimal\|low\|medium\|high`，或 `none` 完全关闭思维链（`enable_thinking=false`） |
| `--model` | `qwen3-vl-8b-instruct` | 模型 id |

输出为 JSON：`model` / `reply`（正式回答）/ `reasoning`（思维链，可忽略）/ `usage`。

## 提速下载大模型 / Fast model download

LM Studio 单条长连接下载大模型常被 CDN 限速。仓库自带分段并发下载脚本
（绕过长连接限速，实测 ModelScope 4.68GB 模型 95 秒下完，约 53 MB/s）：

```powershell
python scripts/chunk_download.py <URL> <输出路径> [--chunk-mb 200] [--concurrency 4]
```

- 源优先用 **ModelScope**（modelscope.cn 的 `lmstudio-community` 组织），国内直连快
- 下载完在 LM Studio 里导入该模型文件即可

## 与其他方案的取舍 / Local vs Cloud

- 需要精细、复杂视觉理解、能接受数据上云 → 用云端多模态 API（通义千问 qwen-vl 系列、OpenAI 等），模型更强
- 隐私 / 离线 / 免费 / 无 key → 本 skill（本地 9B，速度取决于本机 GPU/CPU，思维链较啰嗦）
