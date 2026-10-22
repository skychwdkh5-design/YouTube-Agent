# EP005 Sentinel-2 scene verification

Checked 2026-10-22 against Microsoft Planetary Computer (STAC `sentinel-2-l2a`, item lookup by id + data API renders). Nothing here is assumed:
every id below was looked up and returned an item.

## The two lists

The EP005 description (draft) and the evidence pipeline recorded **different** scene ids. Both lists are real scenes (tile T36RYS, relative orbit 78,
cloud 0-1 %), so the description was not wrong about existence, only about which scenes the video uses.

| Year | Description draft (not used by the video) | Evidence provenance = used by the video and cover |
|---|---|---|
| 2020 | S2A_..._20200929T080731 | **S2A_MSIL2A_20201019T080951_R078_T36RYS_20201021T025651** |
| 2021 | S2B_..._20210929T080719 | **S2A_MSIL2A_20211004T080801_R078_T36RYS_20211004T192027** |
| 2022 | S2A_..._20221009T080841 | **S2B_MSIL2A_20221014T080909_R078_T36RYS_20221015T012054** |
| 2023 | S2A_MSIL2A_20231014T080901 | **S2A_MSIL2A_20231014T080901_R078_T36RYS_20231014T131051** (same) |
| 2024 | S2A_..._20241008T080831 | **S2B_MSIL2A_20241013T080809_R078_T36RYS_20241013T094345** |
| 2025 | S2B_..._20251008T080729 | **S2C_MSIL2A_20251013T080911_R078_T36RYS_20251013T114721** |
| 2026 | S2C_..._20261018T080931 | **S2C_MSIL2A_20261008T080821_R078_T36RYS_20261008T115058** |

## Which set the video and the cover use

- The video's year frames (`y2020`...`y2026`) and the comparison graphics come from the yt-geo stack whose provenance file
  (`evidence_s2/provenance.json` on branch `ep005/neom-research`) lists the right-hand column; the comparison graphic labels its panels
  "Oct 14, 2022" and "Oct 8, 2026", which are exactly those two scenes.
- **Cover (`thumbnail_v2.jpg`)**: left half = 2022-10-14 scene, right half = 2026-10-08 scene (same ground, grid origin 706200 / 3116000, EPSG:32636).
- Independent pixel check: the comparison panels were located in fresh renders of the AOI (best match at the same offset and ~0.94 scale for both years).
  For 2026 the panel agrees with the 2026-10-08 scene over the 2026-10-18 scene in 11 of the 12 areas that changed most between the two dates.
  For 2022 the two candidate scenes are five days apart over unchanged desert, so the pixels cannot tell them apart (5 of 12): for 2022 the evidence is
  the provenance record and the panel label, not the pixels.

## Applied

The description in `publish/queue.json` (and `publish/assets/ep005/description.txt`) now lists the right-hand column and says "October each year".
The old list is kept only in this file.
