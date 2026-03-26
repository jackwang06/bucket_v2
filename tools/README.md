# Tools

This folder collects the reusable helper scripts that were used while
building and checking the DialogCC image memory anchor datasets.

Scripts:

- `build_lowconf_rescue_v3.py`
  Builds the independent `v3` low-confidence rescue dataset and package.

- `show_dialogue_turns.py`
  Prints the first turns of one or more dialogues from `medium_dialogues.json`
  so image candidates can be inspected together with local context.

- `compare_anchor_jsons.py`
  Compares two anchor json files and reports record count, id overlap, and
  record-level field differences.

- `verify_anchor_dataset.py`
  Verifies a generated anchor dataset: local image paths, image-file presence,
  category distribution, and optional zip structure.
