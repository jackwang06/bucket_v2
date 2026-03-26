#!/usr/bin/env python3
"""
Build the standalone v3 low-confidence rescue dataset for image memory anchors.

This script takes the manually selected turn-3 image candidates that were
rescued from the earlier low-confidence pool, copies their preview images into
the dedicated `image_lowconf_rescue_batch/` folder, writes the final
`multimodal_memory_anchor_v3_lowconf_rescue.json`, and packages the json plus
images into a zip file. It also emits a small stats json summarizing the replay
pool and the records that were kept.

中文说明：
这个脚本用于构建独立的 v3 低置信样本“二次抢救”数据集。它会把人工挑出的
turn-3 图片候选复制到专用图片目录，生成新的 json、zip 和统计文件，确保这批
新数据与旧版本数据集完全隔离。
"""

import json
import shutil
import zipfile
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
PREVIEW_DIR = Path("/tmp/lowrescue_preview")
OUT_DIR = BASE / "image_lowconf_rescue_batch"
OUT_JSON = BASE / "multimodal_memory_anchor_v3_lowconf_rescue.json"
OUT_ZIP = BASE / "multimodal_memory_anchor_v3_lowconf_rescue_with_images.zip"
OUT_STATS = BASE / "multimodal_memory_anchor_v3_lowconf_rescue_stats.json"


SELECTED = [
    {
        "dialogue_id": "bst:4734",
        "anchor_category": "location",
        "answer": "trail",
        "utterance": "Take a look at this one.",
        "description": "A dirt hiking trail winding through a dense green forest.",
        "indirect": "I like places where you can walk under lots of trees.",
        "wrong": "Was it a riverbank?",
        "query": "What kind of place was shown in the earlier image?",
    },
    {
        "dialogue_id": "bst:56",
        "anchor_category": "object_attribute",
        "answer": "salad",
        "utterance": "Here is one I had in mind.",
        "description": "A glass bowl filled with a colorful mixed salad.",
        "indirect": "Fresh vegetable dishes always look pretty inviting.",
        "wrong": "Was it a pasta dish?",
        "query": "What dish was shown in the earlier image?",
    },
    {
        "dialogue_id": "daily:1435",
        "anchor_category": "event_experience",
        "answer": "running",
        "utterance": "This is the kind of moment I meant.",
        "description": "A young runner sprinting along a blue track at a stadium.",
        "indirect": "Track events always make kids look full of energy.",
        "wrong": "Was he jumping?",
        "query": "What activity was happening in the earlier image?",
    },
    {
        "dialogue_id": "daily:1348",
        "anchor_category": "location",
        "answer": "beach",
        "utterance": "Here is the view I was talking about.",
        "description": "A sunny beach scene with people looking toward the ocean.",
        "indirect": "Coastal views are always relaxing to look at.",
        "wrong": "Was it a lake?",
        "query": "What kind of place was shown in the earlier image?",
    },
    {
        "dialogue_id": "daily:16526",
        "anchor_category": "location",
        "answer": "house",
        "utterance": "Here is the place I meant.",
        "description": "The exterior of a single-story house with a front yard.",
        "indirect": "I always notice the exterior before stepping inside.",
        "wrong": "Was it an apartment building?",
        "query": "What kind of place was shown in the earlier image?",
    },
    {
        "dialogue_id": "daily:1579",
        "anchor_category": "object_attribute",
        "answer": "computer",
        "utterance": "Here is the setup I was talking about.",
        "description": "A desktop computer setup on a desk with lamps on both sides.",
        "indirect": "Workspace photos usually center around one main device.",
        "wrong": "Was it a television setup?",
        "query": "What device was shown in the earlier image?",
    },
    {
        "dialogue_id": "persona:4186",
        "anchor_category": "event_experience",
        "answer": "meditating",
        "utterance": "This is the one I wanted to show you.",
        "description": "A woman sitting cross-legged and meditating beside a lake.",
        "indirect": "Quiet outdoor scenes can feel especially calming.",
        "wrong": "Was she fishing?",
        "query": "What activity was happening in the earlier image?",
    },
    {
        "dialogue_id": "persona:2280",
        "anchor_category": "object_attribute",
        "answer": "fish",
        "utterance": "Here is the shot I meant.",
        "description": "A person holding up a large fish they just caught.",
        "indirect": "Catching something sizeable always makes for a proud photo.",
        "wrong": "Was it a turtle?",
        "query": "What animal was shown in the earlier image?",
    },
    {
        "dialogue_id": "persona:5098",
        "anchor_category": "location",
        "answer": "trail",
        "utterance": "Take a look at this one.",
        "description": "A narrow trail stretching through green meadows and trees.",
        "indirect": "I really like being outdoors where there is plenty of open space.",
        "wrong": "Was it a campsite?",
        "query": "What kind of place was shown in the earlier image?",
    },
    {
        "dialogue_id": "bst:2650",
        "anchor_category": "event_experience",
        "answer": "pitching",
        "utterance": "Here is the action shot I meant.",
        "description": "A baseball pitcher throwing from the mound during a game.",
        "indirect": "Team sports photos usually capture one motion at the center.",
        "wrong": "Was he batting?",
        "query": "What activity was happening in the earlier image?",
    },
    {
        "dialogue_id": "persona:7355",
        "anchor_category": "location",
        "answer": "swimming pool",
        "utterance": "Here is the place I was thinking of.",
        "description": "A modern indoor swimming pool inside a large home.",
        "indirect": "Indoor leisure spaces can really define how a place feels.",
        "wrong": "Was it a home gym?",
        "query": "What kind of place was shown in the earlier image?",
    },
]


def get_turns(dialogue):
    return dialogue.get("dialogue") or dialogue.get("turns") or []


def get_images(turn):
    return turn.get("image") or turn.get("images") or turn.get("shared_image") or []


def classify_turn3(dialogue_id, dialogue, completed_ids):
    turns = get_turns(dialogue)
    if len(turns) < 3:
        return None
    turn = turns[2]
    images = get_images(turn)
    if not images:
        return None
    if dialogue_id in completed_ids:
        return "already_done"

    caption_blob = " ".join((img.get("caption") or "") for img in images).lower()
    meta_markers = [
        "illustration",
        "timeline",
        "guidebook",
        "guide",
        "itinerary",
        "book cover",
        "poster",
        "screen",
        "logo",
        "painting",
        "drawing",
        "map of",
        "encyclopedia",
    ]
    multi_markers = [
        "family",
        "group",
        "crowd",
        "people",
        "friends",
        "children",
        "kids",
        "parents",
        "couple",
        "pair of",
        "dogs ",
        "cats ",
        "horses ",
        "animals",
        "band members",
    ]
    if any(marker in caption_blob for marker in meta_markers):
        return "meta_or_textual"
    if any(marker in caption_blob for marker in multi_markers):
        return "multi_subject"
    return "lowconf_replay"


def main():
    medium_dialogues = json.load(open(BASE / "medium_dialogues.json"))
    dialogue_map = {item["dialogue_id"]: item for item in medium_dialogues}

    completed_ids = set()
    for name in [
        "multimodal_memory_anchor_v1_updated.json",
        "multimodal_memory_anchor_v2_multisubject.json",
    ]:
        path = BASE / name
        if path.exists():
            completed_ids |= {row["dialogue_id"] for row in json.load(open(path))}

    prior_stats = json.load(open(BASE / "multimodal_image_run_stats.json"))
    prior_lowconf_logged = prior_stats["stats"]["skip_no_high_confidence_rule"]

    replay_stats = {
        "turn3_image_candidates": 0,
        "already_done": 0,
        "meta_or_textual": 0,
        "multi_subject": 0,
        "lowconf_replay": 0,
    }
    for item in medium_dialogues:
        turns = get_turns(item)
        if len(turns) < 3:
            continue
        if not get_images(turns[2]):
            continue
        replay_stats["turn3_image_candidates"] += 1
        label = classify_turn3(item["dialogue_id"], item, completed_ids)
        if not label:
            continue
        replay_stats[label] += 1

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    skipped = {}
    category_counts = {}
    for config in SELECTED:
        dialogue = dialogue_map.get(config["dialogue_id"])
        if not dialogue:
            skipped[config["dialogue_id"]] = "missing_dialogue"
            continue

        turns = get_turns(dialogue)
        turn3 = turns[2]
        speaker = turn3.get("speaker") or turns[1].get("speaker") or "assistant"
        stem = config["dialogue_id"].replace(":", "_")
        image_name = stem + "_anchor.jpg"
        out_path = OUT_DIR / image_name
        preview_path = PREVIEW_DIR / f"{stem}.jpg"
        if preview_path.exists():
            shutil.copyfile(preview_path, out_path)
        else:
            skipped[config["dialogue_id"]] = "missing_preview_image"
            continue

        record = {
            "dialogue_id": config["dialogue_id"],
            "anchor_type": "image",
            "anchor_category": config["anchor_category"],
            "answer": config["answer"],
            "anchor_turns": [
                {
                    "utterance": config["utterance"],
                    "speaker": speaker,
                    "shared_image": [f"image_lowconf_rescue_batch/{image_name}"],
                    "description": config["description"],
                }
            ],
            "indirect_reference_turns": [
                {
                    "utterance": config["indirect"],
                    "speaker": "user",
                    "shared_image": [],
                    "description": "",
                }
            ],
            "wrong_override_turns": [
                {
                    "utterance": config["wrong"],
                    "speaker": "user",
                    "shared_image": [],
                    "description": "",
                }
            ],
            "query_turns": [
                {
                    "utterance": config["query"],
                    "speaker": "user",
                    "shared_image": [],
                    "description": "",
                }
            ],
        }
        records.append(record)
        category_counts[config["anchor_category"]] = category_counts.get(config["anchor_category"], 0) + 1

    records.sort(key=lambda item: item["dialogue_id"])
    with open(OUT_JSON, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT_JSON, OUT_JSON.name)
        for image_path in sorted(OUT_DIR.iterdir()):
            zf.write(image_path, f"{OUT_DIR.name}/{image_path.name}")

    stats = {
        "source_reference": str((BASE / "multimodal_image_run_stats.json").name),
        "logged_prior_lowconf_pool": prior_lowconf_logged,
        "replayed_lowconf_pool": replay_stats["lowconf_replay"],
        "replay_breakdown": replay_stats,
        "selected_for_manual_rescue": len(SELECTED),
        "kept": len(records),
        "skipped": skipped,
        "category_counts": category_counts,
        "selected_ids": [record["dialogue_id"] for record in records],
        "shared_image_all_local": all(
            record["anchor_turns"][0]["shared_image"][0].startswith("image_lowconf_rescue_batch/")
            for record in records
        ),
        "zip_exists": OUT_ZIP.exists(),
    }
    with open(OUT_STATS, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
