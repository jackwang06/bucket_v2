#!/usr/bin/env python3
"""
Print dialogue turns from `medium_dialogues.json` for quick candidate review.

This script is useful during annotation and QA: given one or more `dialogue_id`
values, it prints the early turns, speakers, and any attached image payloads so
we can inspect local context without manually searching through the full source
json.

中文说明：
这个脚本用于按 `dialogue_id` 快速查看原始对话内容。它会打印前几轮对话、说话人
以及对应的图片字段，方便在标注或质检时快速理解上下文，而不用手动翻完整的
`medium_dialogues.json`。
"""

import argparse
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent


def get_turns(dialogue):
    return dialogue.get("dialogue") or dialogue.get("turns") or []


def get_text(turn):
    return turn.get("text") or turn.get("utterance") or turn.get("dialogue") or ""


def get_images(turn):
    return turn.get("image") or turn.get("images") or turn.get("shared_image") or []


def main():
    parser = argparse.ArgumentParser(description="Show dialogue turns for selected ids.")
    parser.add_argument("dialogue_ids", nargs="+", help="Dialogue ids such as persona:5298")
    parser.add_argument("--max-turns", type=int, default=6, help="How many turns to print per dialogue")
    args = parser.parse_args()

    data = json.load(open(BASE / "medium_dialogues.json"))
    lookup = {item["dialogue_id"]: item for item in data}

    for dialogue_id in args.dialogue_ids:
        print(f"\n### {dialogue_id}")
        item = lookup.get(dialogue_id)
        if not item:
            print("MISSING")
            continue
        for idx, turn in enumerate(get_turns(item)[: args.max_turns], 1):
            text = get_text(turn)
            images = get_images(turn)
            speaker = turn.get("speaker", "?")
            marker = " IMG" if images else ""
            print(f"{idx} {speaker} {text!r}{marker}")
            if images:
                print(f"    {images}")


if __name__ == "__main__":
    main()
