"""分段并发下载大文件（绕过长连接限速）。

用法:
    python chunk_download.py <URL> <输出路径> [--chunk-mb 200] [--concurrency 4]

原理: 单条长连接会被 CDN 限速，拆成多个短 Range 连接并发下载后拼接。
实测: ModelScope 4.68GB 模型 95 秒下完（~53 MB/s）。
"""
import argparse
import os
import subprocess
import sys
import time

def get_total(url, timeout=30):
    devnull = "NUL" if os.name == "nt" else "/dev/null"
    cmd = ["curl", "-s", "-L", "-D", "-", "-o", devnull, "-r", "0-0", "-m", str(timeout), url]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "content-range" in line.lower():
            return int(line.split("/")[-1].strip())
    raise RuntimeError("未获取到 Content-Range: " + out[:500])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--chunk-mb", type=int, default=200)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    total = get_total(args.url)
    print(f"文件总大小: {total} bytes = {total/1024**3:.2f} GB", flush=True)
    chunk = args.chunk_mb * 1024 * 1024
    ranges = []
    start = 0
    while start < total:
        end = min(start + chunk - 1, total - 1)
        ranges.append((start, end))
        start = end + 1
    print(f"分 {len(ranges)} 段，每段 {args.chunk_mb}MB，并发 {args.concurrency}", flush=True)

    tmpdir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(tmpdir, exist_ok=True)
    done = [False] * len(ranges)
    next_i = 0
    active = []
    downloaded = 0
    t0 = time.time()
    last_report = 0

    while next_i < len(ranges) or active:
        while len(active) < args.concurrency and next_i < len(ranges):
            i = next_i
            next_i += 1
            s, e = ranges[i]
            dest = os.path.join(tmpdir, f"_chunk_{i:04d}.bin")
            if os.path.exists(dest) and os.path.getsize(dest) == (e - s + 1):
                done[i] = True
                downloaded += e - s + 1
                continue
            cmd = ["curl", "-s", "-L", "-r", f"{s}-{e}", "-o", dest, "-m", str(args.timeout),
                   "-A", "Mozilla/5.0", args.url]
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            active.append((p, i, dest, s, e))
        still = []
        for (p, i, dest, s, e) in active:
            if p.poll() is not None:
                sz = os.path.getsize(dest) if os.path.exists(dest) else 0
                if p.returncode == 0 and sz == (e - s + 1):
                    done[i] = True
                    downloaded += e - s + 1
                else:
                    print(f"段 {i} 失败(rc={p.returncode} size={sz}/{e-s+1})，重试", flush=True)
                    next_i = min(next_i, i)
            else:
                still.append((p, i, dest, s, e))
        active = still
        el = time.time() - t0
        done_cnt = sum(done)
        if done_cnt and int(el) != last_report:
            last_report = int(el)
            print(f"进度: {done_cnt}/{len(ranges)} 段, {downloaded/1024**3:.2f}GB, {el:.0f}s, {downloaded/1024**2/el:.1f}MB/s", flush=True)
        time.sleep(0.5)

    print("拼接中...", flush=True)
    with open(args.out, "wb") as out:
        for i in range(len(ranges)):
            dest = os.path.join(tmpdir, f"_chunk_{i:04d}.bin")
            with open(dest, "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
            os.remove(dest)
    print(f"完成: {args.out} = {os.path.getsize(args.out)/1024**3:.2f} GB, 总用时 {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
