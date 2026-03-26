#!/usr/bin/env python3
"""
Verify that an anchor dataset package is locally consistent.

This script checks whether every `shared_image` entry points to a local file,
whether those files actually exist on disk, how categories are distributed in
the json, and optionally whether a packaged zip contains the expected entries.
It is intended as a final delivery check before handing off a dataset.

中文说明：
这个脚本用于检查一个 anchor 数据集是否可交付。它会验证 `shared_image` 是否都是
本地路径、图片文件是否实际存在、类别分布是否正常，并可额外检查 zip 包的内容结构。
"""

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Verify an anchor dataset package.")
    parser.add_argument("json_path", help="Dataset json to verify")
    parser.add_argument("--zip-path", help="Optional zip package to inspect")
    args = parser.parse_args()

    json_path = Path(args.json_path).resolve()
    base = json_path.parent
    data = json.load(open(json_path))

    local_path_failures = []
    missing_files = []
    categories = Counter()
    for item in data:
        categories[item["anchor_category"]] += 1
        for image_path in item["anchor_turns"][0].get("shared_image", []):
            if image_path.startswith("http://") or image_path.startswith("https://"):
                local_path_failures.append((item["dialogue_id"], image_path))
            full_path = base / image_path
            if not full_path.exists():
                missing_files.append((item["dialogue_id"], image_path))

    print("records", len(data))
    print("categories", dict(categories))
    print("has_remote_paths", bool(local_path_failures))
    print("missing_files", missing_files)

    if args.zip_path:
        zip_path = Path(args.zip_path).resolve()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        print("zip_entries", len(names))
        print("zip_first_entries", names[:20])


if __name__ == "__main__":
    main()
