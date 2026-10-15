# Licence audit (EP004, 2026-10-15) - what was READ vs ASSUMED

| item | licence evidence | status | decision |
|---|---|---|---|
| ESA "Ground motion over Jakarta" 2024 JPG | page text: **CC BY-SA 3.0 IGO or ESA Standard Licence (either)**; credit "Contains modified Copernicus Sentinel data (2019), processed by ESA, GEP, CNR-IREA & BRGM" | READ | usable with credit. Open point: CC BY-SA ShareAlike on adaptations - the ESA Standard Licence page was not read; **owner/legal decision before any adaptation (recolouring, cropping with overlays)**. Safe default: show unmodified with credit; our graphics as separate, labelled layers. |
| ESA "Ground motion in Jakarta" 2019 JPG (7012x3946, inset on harbour) | page text: **ESA Standard Licence; "additional permission may be required (spaceinimages@esa.int)"** | READ | **not used in a monetised video** until permission is obtained (owner can email; I won't send). 2024 image shows the same map without the inset. |
| Data in Brief 2026 (Shabrina et al.) text/figures | Crossref + PMC: **CC BY 4.0** | READ | figures reusable with attribution; processed raster dataset on Zenodo (doi 10.5281/zenodo.19456870) - licence **not read** (zenodo.org blocked) |
| Hakim et al. 2025 GIScience & RS | Crossref licence field: **CC BY 4.0** (start 2025-02-12) | READ (metadata); full text not accessed | figures reusable with attribution once seen; check each figure's own credit |
| Yunus et al. 2026 RSASE | Elsevier TDM / user-licence only (no CC) | READ (metadata) | **no figures** |
| Other papers (Harintaka, Abidin, Chaussard, EGU, SSRN) | not read | UNKNOWN | not used for imagery |
| Sentinel-1/2 raw data | Copernicus legal notice not fetched (dataspace.copernicus.eu root reachable, catalogue/legal host blocked); generally free incl. commercial | ASSUMED | not needed for the plan; the ESA/paper products cover Sentinel-1 evidence |
| Landsat (USGS M2M) | USGS credit policy page not read (registry: ASSUMED public domain) | ASSUMED | credit "Landsat imagery courtesy of NASA/USGS"; re-read policy page when reachable |
| NASA Earth Observatory images | NASA reproduction guidelines (registry: confirm before monetised release); image host currently blocked | UNREAD | do not use EO JPGs; use our own Landsat renders |
| Natural Earth | LICENSE.md fetched from github.com/nvkelso/natural-earth-vector (public domain), sha256 verified | READ | usable |
| Synthesised SFX | repo CC0 | VERIFIED in repo | usable |
| YouTube competitor thumbnails/footage | proprietary | - | **study only; never in the video** |


## Update 2026-10-15 - owner decision on ESA material
Owner rule: CC BY-SA 3.0 IGO is chosen only for materials where it is explicitly stated; if a specific map cannot be safely included in a monetised video, do not use it, and do not wait for ESA's permission on the 2019 map.

| item | licence statement on its ESA page | decision |
|---|---|---|
| ESA 2024 "Ground motion over Jakarta" (A01) | explicit: "CC BY-SA 3.0 IGO or ESA Standard Licence (content can be used under either licence)" | **eligible under CC BY-SA 3.0 IGO, conditions below; NOT in the proof** (no unlicensed/uncleared ESA frame is distributed) |
| ESA 2019 "Ground motion in Jakarta" (A02) | ESA Standard Licence; "additional permission may be required" | **excluded** (no permission will be awaited) |

Conditions for A01 if used later (from the licence's terms as commonly stated for CC BY-SA 3.0 IGO; the legal code itself was not fetched - hosts blocked - so read it before release):
1. **Attribution**: creator/credit line exactly as ESA gives it ("Contains modified Copernicus Sentinel data (2019), processed by ESA, GEP, CNR-IREA & BRGM"), licence name + link, and an indication if we changed the image.
2. **ShareAlike**: an *adaptation* (recoloured, cropped with burned-in annotations, re-projected) must be released under the same or a compatible licence. Whether a documentary that merely shows the image is an adaptation or a collective work is a legal question I cannot settle. Practical design that keeps us outside the question: show the **whole, unaltered image** in its own full frame with a visible credit; put every annotation **outside** the image pixels (side callouts, frame, legend text) or on a separate dimmed layer after the image is shown clean; never recolour it.
3. **No endorsement** by ESA/IGO implied; the IGO 3.0 text also carries a dispute-resolution clause (mediation) - not a blocker, but note it.
4. **Third-party processing**: the credit names GEP, CNR-IREA and BRGM as processors; ESA's licence statement is for the image as published by ESA. Residual risk: LOW-MEDIUM, not zero.
5. **Monetisation**: CC licences permit commercial use unless "NC" is present (it is not).
**Verdict:** A01 is *not safe for heavy adaptation* (hook sequence with snap-zoom rings drawn on the pixels would arguably be an adaptation). For S1 prefer an **original visualisation built from lawfully reusable data** (CC BY 4.0 Data in Brief / Zenodo dataset, once its figures or raster can be fetched), and keep A01 as an optional, unaltered, credited full-frame shot.

## Data in Brief figures (CC BY 4.0): path to a legal measured map
Figures gr1-gr13 are on cdn.ncbi.nlm.nih.gov (blocked from this container; the proxy refuses the host) and the Zenodo raster (zenodo.org) is also blocked. CC BY 4.0 has no ShareAlike, so recolouring/cropping/annotating is allowed with attribution and a change note.
Unblocking: allow `cdn.ncbi.nlm.nih.gov` and `zenodo.org` (or send the files). Until then the proof uses **EVIDENCE MAP PENDING**.
