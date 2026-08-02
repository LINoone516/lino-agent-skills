#!/usr/bin/env python3
"""analyze.py — 调用本机 LM Studio 本地视觉模型分析图片（OpenAI 兼容接口）。

用法:
    python analyze.py --image <路径> [--prompt "问题"] [--max-tokens 2048] [--model <id>]

示例:
    python analyze.py --image shot.png --prompt "用一句话描述这张图片的内容"
"""
import argparse
import base64
import io
import json
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "qwen3-vl-8b-instruct"
BASE_URL = "http://127.0.0.1:1234/v1/chat/completions"


def image_to_data_uri(path: str, max_w: int = 256, quality: int = 80) -> str:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.size[0] > max_w:
        h = int(im.size[1] / im.size[0] * max_w)
        im = im.resize((max_w, h))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="本地图片路径")
    ap.add_argument("--prompt", default="用一句话描述这张图片的内容")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--max-width", type=int, default=256,
                    help="图片最大宽度（像素）。默认 256 省 token，但细节会丢；识别游戏/UI/小字等细节用 768-1024")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--reasoning-effort", default="minimal",
                    help="思维链强度：minimal|low|medium|high，或 none 完全关闭。默认 minimal（防思维链循环）")
    args = ap.parse_args()

    data_uri = image_to_data_uri(args.image, max_w=args.max_width)
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": args.prompt},
                ],
            }
        ],
        "max_tokens": args.max_tokens,
    }
    if args.reasoning_effort and args.reasoning_effort != "none":
        payload["reasoning_effort"] = args.reasoning_effort
    else:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
    except urllib.error.URLError as e:
        print(json.dumps({"ok": False, "error": f"无法连接 LM Studio（{BASE_URL}）：{e}。请先运行 lms server start 并加载模型。"}, ensure_ascii=False))
        return 1

    msg = d["choices"][0]["message"]
    out = {
        "ok": True,
        "model": d.get("model"),
        "reply": msg.get("content"),
        "reasoning": msg.get("reasoning_content"),
        "usage": d.get("usage"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not msg.get("content") and (d.get("usage") or {}).get("completion_tokens_details", {}).get("reasoning_tokens"):
        print("提示：正式回答为空——max_tokens 被思维链耗尽，请调大 --max-tokens 重试。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
