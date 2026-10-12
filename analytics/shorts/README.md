# analytics/shorts - published Shorts results (append-only)

Nothing here is collected automatically. A person exports numbers from YouTube Studio (or saves an Analytics API response) and the tools in
`.claude/skills/yt-shorts-feedback/` validate and store them. Unknown values are `null`; they are never estimated.

| file | content | edit rule |
|---|---|---|
| `measurements.jsonl` | one JSON object per reading of a video's numbers | append only (`feedback.py add` / `import-*`); a correction is a new record with a new `measurement_timestamp` and a note |
| `videos.json` | static facts per Short: duration, production file hash, caption-derived structure, annotations | add entries; fill `publication_date` / `youtube_video_id` when known |
| `hypotheses.json` | falsifiable statements with a pre-registered test block | written before the data exists; the `test` block is never edited afterwards, only `status` and `decision` |
| `experiments.json` | pre-registered experiment plans (factor, variants, seeded assignment, window) | never rewritten (`plan-experiment --write` refuses duplicates) |

## Measurement fields (`.claude/skills/yt-shorts-feedback/schema/measurement.schema.json`, generated from `feedback.py`)

| field | unit / type | notes |
|---|---|---|
| `video_id` | string | internal production id (file stem), required |
| `youtube_video_id` | string or null | the 11-character id once known |
| `publication_date` | `YYYY-MM-DD` or null | |
| `duration_seconds` | number | length of the published file |
| `views` | integer | YouTube `views` |
| `engaged_views` | integer or null | YouTube `engagedViews` (past the first frame or tap-to-play). **Not** the same metric as `views` |
| `stayed_to_watch_percent` / `swiped_away_percent` | 0-100 or null | Studio "viewed vs swiped away" |
| `average_view_duration` | seconds or null | can exceed `duration_seconds` when playbacks repeat |
| `average_percentage_viewed` | percent or null | above 100 means repeated playback is included |
| `subscribers_gained` | integer or null | |
| `measurement_timestamp` | ISO 8601 or null | when the numbers were read; null = window unknown |
| `experiment_variant` | `EXP-id:variant`, `baseline_unplanned` or null | |
| `source` | `manual_entry`, `studio_export_csv`, `analytics_api_json` | provenance |
| `metric_source` | `studio` or `analytics_api` or null | never compare across sources |
| `recorded_on`, `notes` | date, text | |

Derived values (`replay_ratio`, `engaged_views_per_view`, `subscribers_per_1000_views`, intervals) are computed by `feedback.py report` and are never stored.
