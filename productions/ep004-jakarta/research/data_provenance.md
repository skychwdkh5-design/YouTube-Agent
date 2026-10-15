# Data provenance (EP004, 2026-10-15)

Everything below was fetched in this session unless marked otherwise. Heavy files live in `/tmp` scratch (not committed); hashes are recorded for re-fetch checks.

| id | what | URL / route | fetched | notes |
|---|---|---|---|---|
| P1 | ESA 2024 ground-motion JPG | https://www.esa.int/var/esa/storage/images/esa_multimedia/images/2024/11/ground_motion_over_jakarta_indonesia/26468681-1-eng-GB/Ground_motion_over_Jakarta_Indonesia.jpg | 2026-10-15 | 2112x1188, 1,710,070 B, sha256 cb0052047ae918631a48ace04b44ea674178205c358f147194699d877aa11595 |
| P2 | ESA 2019 JPG | https://www.esa.int/var/esa/storage/images/esa_multimedia/images/2019/07/ground_motion_in_jakarta/19487713-1-eng-GB/Ground_motion_in_Jakarta.jpg | 2026-10-15 | 7012x3946, sha256 8a207bd46473cc1629bfe8ab3724263c52e15df9796099512f09d3f11162ec45 (permission needed, see licence audit) |
| P3 | ESA page texts (both) | esa.int ... via `curl` | 2026-10-15 | captions/credits/licence quoted in the dossier |
| P4 | Data in Brief full text | https://pmc.ncbi.nlm.nih.gov/articles/PMC13380226/ | 2026-10-15 | read-only; PMC bot check blocks other PMC articles |
| P5 | Crossref metadata (3 DOIs) | https://api.crossref.org/works/<doi> | 2026-10-15 | titles, dates, licences |
| P6 | NASA EO article text | https://science.nasa.gov/earth/earth-observatory/as-jakarta-grows-so-do-the-water-issues-148303/ | 2026-10-15 | images not downloadable (assets host blocked) |
| P7 | Landsat 9/8 L1 scene 2026-09-14 (LC08_L1TP_122064_20260914_20260924_02_T1, cloud 3 %) | USGS M2M `download-bands` | 2026-10-15 | bands B4,B3,B2 (30 m); see manifest |
| P8 | Landsat 5 TM scene 1990-07-09 (LT05_L1TP_122064_19900709_20200915_02_T1, cloud 4 %) | USGS M2M | 2026-10-15 | bands B3,B2,B1 |
| P9 | Natural Earth 1:10M/50M/110M GeoJSON | `tools/fetch_natural_earth.sh` (GitHub pinned commit) | 2026-10-15 | sha256 manifest OK |
| P10 | YouTube metrics/thumbnails | youtube.com search cards, i.ytimg.com | 2026-10-15 05:3x-05:4x UTC | study only |

Not obtainable here: Sentinel-1 SLC/GRD from Copernicus Data Space (catalogue host blocked + account needed), COMET-LiCS frames, the Zenodo raster, Hakim 2025 full text,
RSASE 2026 abstract. Dating rule kept: every asset is labelled with its acquisition/study period, never with the download date.

## Landsat band checksums (scratch copies, not committed)
```
df910c8843caab2fd6938d1d71e1d053fa0186567abc327bf57c4679729b7798  1990/LT05_L1TP_122064_19900709_20200915_02_T1_B1.TIF
2620c10332d2a2541ce82818810ee428d53ff8ab2cc17406916c03f930635824  1990/LT05_L1TP_122064_19900709_20200915_02_T1_B2.TIF
40643cd3fd59001c34f8315aaa82fe39481c119cc12d727fa2b5368a5d1b0fd0  1990/LT05_L1TP_122064_19900709_20200915_02_T1_B3.TIF
174e7f6e3fe0169ea4ae4d6eab122bdd2947c3c5bf9bf1d1f87691c54fd62ac1  2026/LC08_L1TP_122064_20260914_20260924_02_T1_B2.TIF
96b4978d31a81f8fe4425b34d8c17c86de0426db315b1a95815ef2149bfeadb3  2026/LC08_L1TP_122064_20260914_20260924_02_T1_B3.TIF
a4ef4121b2144719f444acb010d7befe0b0857a08e0e5f62d226f192d83070f8  2026/LC08_L1TP_122064_20260914_20260924_02_T1_B4.TIF
```
