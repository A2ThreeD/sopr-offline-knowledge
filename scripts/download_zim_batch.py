#!/usr/bin/env python3
# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Download and publish Kiwix archives using a bounded worker pool.

import argparse
import fcntl
import json
import os
import re
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


MIRROR = "https://cdimage.debian.org/mirror/kiwix.org/zim/"
MIRROR_OPTIONS = Path(__file__).resolve().parents[1] / "catalog" / "zim-mirrors.json"
MIRROR_ROOTS = ("https://download.kiwix.org/zim/", *(item["url"] for item in json.loads(MIRROR_OPTIONS.read_text())["mirrors"]))


def response_details(log_path: Path) -> tuple[int, str]:
    log = log_path.read_text(errors="replace")
    responses = re.split(r"(?m)^ *HTTP/[^ ]+ ", log)
    if len(responses) == 1:
        return 0, ""
    last = responses[-1]
    status = last.partition("\n")[0].strip()
    size = re.search(r"(?im)^ *Content-Range: bytes [^/]+/(\d+)", last)
    if not size and status.startswith("200"):
        size = re.search(r"(?im)^ *Content-Length: (\d+)", last)
    return int(size[1]) if size else 0, status


def download(url: str, target: Path, index: int, total: int) -> bool:
    print(f"PROGRESS_DOWNLOAD_FILE|{index}|{total}|{target.name}", flush=True)
    print(f"Downloading {target.name}", flush=True)
    staging_dir = target.parent / ".sopr-download-tmp"
    staged_file = staging_dir / target.name
    try:
        with tempfile.NamedTemporaryFile(dir=staging_dir) as response_log:
            response_path = Path(response_log.name)
            with subprocess.Popen(
                ["wget", "--server-response", "--no-verbose", "-N", "-c", "--", url],
                stdout=response_log, stderr=subprocess.STDOUT,
                cwd=staging_dir,
                env={**os.environ, "TMPDIR": str(staging_dir)},
            ) as process:
                while True:
                    try:
                        return_code = process.wait(timeout=5)
                        break
                    except subprocess.TimeoutExpired:
                        try:
                            downloaded_bytes = staged_file.stat().st_size
                        except FileNotFoundError:
                            downloaded_bytes = 0
                        total_bytes, _ = response_details(response_path)
                        print(f"PROGRESS_DOWNLOAD_BYTES|{downloaded_bytes}|{total_bytes}|{target.name}", flush=True)
            _, status = response_details(response_path)
        if return_code == 0 and staged_file.is_file():
            staged_file.replace(target)
            print(f"Ready: {target.name}", flush=True)
            return True
        reason = status if status and not status.startswith(("200", "206")) else f"wget exited with code {return_code}"
        print(f"Failed: {target.name} ({reason})", flush=True)
    except OSError as exc:
        print(f"{target.name}: {exc}", flush=True)
    return False


def manifest_targets(manifest: Path, library: Path, wikipedia: Path, mirror: str = MIRROR) -> dict[Path, str]:
    targets = {}
    for line in manifest.read_text().splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        for prefix in MIRROR_ROOTS:
            if url.startswith(prefix):
                url = mirror + url.removeprefix(prefix)
                break
        name = url.rsplit("/", 1)[-1]
        directory = wikipedia if "/zim/wikipedia/" in url or name.startswith("wikipedia_") else library
        targets.setdefault(directory / name, url)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("library", type=Path)
    parser.add_argument("download_dir", type=Path)
    parser.add_argument("wikipedia_dir", type=Path)
    parser.add_argument("jobs", type=int, choices=range(1, 4))
    parser.add_argument("--mirror", default=MIRROR)
    args = parser.parse_args()
    mirror = args.mirror.rstrip("/") + "/"
    if mirror == MIRROR_ROOTS[0]:
        mirror = MIRROR

    targets = manifest_targets(args.manifest, args.download_dir.resolve(), args.wikipedia_dir.resolve(), mirror)
    total = len(targets)
    failures = []
    with (args.library / ".sopr-zim-download.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "Another ZIM download is already running.\n")
        print(f"PROGRESS_DOWNLOAD_TOTAL|{total}", flush=True)
        print(f"PROGRESS_DOWNLOAD_FINISHED|0|{total}|", flush=True)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            pending = {
                pool.submit(download, url, target, index, total): (target, url)
                for index, (target, url) in enumerate(targets.items(), 1)
            }
            for finished, task in enumerate(as_completed(pending), 1):
                target, url = pending[task]
                succeeded = task.result()
                if not succeeded:
                    failures.append(target.name)
                    print(f"PROGRESS_DOWNLOAD_FAILED|{target.name}", flush=True)
                print(f"PROGRESS_DOWNLOAD_FINISHED|{finished}|{total}|{target.name}", flush=True)
        print(f"PROGRESS_DOWNLOAD_COMPLETE|{total}", flush=True)

    if failures:
        print(f"WARNING: {len(failures)} ZIM download(s) failed. Retry the content download to try again:", flush=True)
        print("Failed files: " + ", ".join(failures), flush=True)


if __name__ == "__main__":
    main()
