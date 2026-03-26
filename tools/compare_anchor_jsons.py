#!/usr/bin/env python3
"""
Compare two anchor dataset json files at the record level.

This script reports record counts, ids that only appear on one side, and the
main field-level differences for shared records, such as `answer`,
`anchor_category`, local image paths, anchor utterances, and descriptions.
It is mainly for version-to-version auditing when we update or expand a dataset.

中文说明：
这个脚本用于比较两个 anchor 数据集 json 的差异。它会输出记录数、只存在于某一边
的 `dialogue_id`，以及共同记录里几个关键字段的变化，适合做版本更新前后的核对。
"""

import argparse
import json
from pathlib import Path
import sys


def load_records(path):
    return {item["dialogue_id"]: item for item in json.load(open(path))}


def main():
    parser = argparse.ArgumentParser(description="Compare two anchor dataset json files.")
    parser.add_argument("left", help="Path to the older/original json")
    parser.add_argument("right", help="Path to the newer/updated json")
    args = parser.parse_args()

    left_path = Path(args.left)
    right_path = Path(args.right)
    missing = [str(path) for path in (left_path, right_path) if not path.exists()]
    if missing:
        print("missing_files", missing)
        sys.exit(1)

    left = load_records(left_path)
    right = load_records(right_path)

    print(f"{left_path.name} count={len(left)}")
    print(f"{right_path.name} count={len(right)}")
    print("only_in_right", sorted(set(right) - set(left)))
    print("only_in_left", sorted(set(left) - set(right)))

    common = sorted(set(left) & set(right))
    tracked_fields = [
        ("answer", lambda row: row.get("answer")),
        ("anchor_category", lambda row: row.get("anchor_category")),
        ("shared_image", lambda row: row["anchor_turns"][0].get("shared_image")),
        ("anchor_utterance", lambda row: row["anchor_turns"][0].get("utterance")),
        ("description", lambda row: row["anchor_turns"][0].get("description")),
    ]

    for dialogue_id in common:
        diffs = []
        for label, getter in tracked_fields:
            left_value = getter(left[dialogue_id])
            right_value = getter(right[dialogue_id])
            if left_value != right_value:
                diffs.append((label, left_value, right_value))
        if diffs:
            print(f"\n{dialogue_id}")
            for diff in diffs:
                print(diff)


if __name__ == "__main__":
    main()
