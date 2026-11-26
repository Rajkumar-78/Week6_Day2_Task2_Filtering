# Task 2 — Filtering and Collection Management
Run Qdrant and install requirements as described in `docker_commands.txt` and `requirements.txt`, then run `python task2_filtering.py`.

Expected key output:
```
Points before re-upsert: 30
Filtered search (category=HR): 4 results
Points after re-upsert: 30
Points after deleting category=Marketing: 28
```
The script combines exact category match and page range `gte=3`, creates a keyword payload index, re-upserts the same IDs with revised text, and deletes Marketing points.
