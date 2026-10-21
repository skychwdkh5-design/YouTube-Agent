# Free media sources: network access vs legal permission (measured 2026-10-21, build machine)

Two separate questions. **Network**: can this machine open the host (measured with `media.py probe`, curl GET). **Permission**: may we use the file (decided only by `rights_evidence` read on the source page).
Paid APIs and stock agencies are not used; no API key was requested.

| source | host | network from the build machine | rights text (read where) |
|---|---|---|---|
| NASA Scientific Visualization Studio | svs.gsfc.nasa.gov (pages and `/vis/...` files) | **OK** (HTTP 200, 50.6 MB file downloaded) | https://svs.gsfc.nasa.gov/help/ FAQ: "All of our content is in the public domain (unless otherwise noted)..."; licensed music is excluded and noted per item |
| NASA media guidelines | www.nasa.gov | **OK** | https://www.nasa.gov/nasa-brand-center/images-and-media/ : NASA content generally not subject to copyright in the US; acknowledge NASA; do not imply endorsement; NASA insignia not public domain; third-party material is marked |
| NASA Earth Observatory pages | earthobservatory.nasa.gov -> science.nasa.gov | **pages OK** (301 -> 200) | same NASA guidelines; credit line on the page ("NASA Earth Observatory images by Jesse Allen, using ASTER data ... and Landsat data from the U.S. Geological Survey") |
| NASA Earth Observatory image files | assets.science.nasa.gov | **BLOCKED** (CONNECT tunnel failed, HTTP 403) | - |
| NASA Image and Video Library | images.nasa.gov, images-api.nasa.gov, images-assets.nasa.gov | **BLOCKED** (CONNECT 403 on all three) | - |
| Wikimedia Commons | commons.wikimedia.org, commons.m.wikimedia.org, upload.wikimedia.org | **BLOCKED** (CONNECT 403) | - |
| USGS pages | www.usgs.gov | **OK** (GET 200; HEAD 403) | USGS image credits (public domain unless a third party is credited) - not yet exercised |
| USGS files and publications | d9-wret.s3.us-west-2.amazonaws.com, pubs.usgs.gov, eros.usgs.gov | **BLOCKED** (CONNECT 403) | - |

## The real test (not simulated)
1. Candidate: NASA SVS 15085 "The Shrinking Salton Sea" (found by web search, status DISCOVERED).
2. `media.py svs --url https://svs.gsfc.nasa.gov/15085/` read the item page (credit: NASA's Goddard Space Flight Center; visualizer Ross K. Walter (SSAI); released 2026-08-30; no music or third-party note) and the SVS rights FAQ; the sentence above was found verbatim, so the entry carries it as `rights_evidence`.
3. `media.py fetch --confirm` downloaded `Salton_Sea_Shrinking_-_Web.mp4`: 50,599,735 bytes, H.264 1920x1080 30 fps, 39.9 s, **no audio stream** (so no licensed music). sha256 `56a9297ea3e108f51e114ea1fc2e80c9ccdc748c5e0645d4ed58123f17acfec1`. A second, independent run into a fresh folder gave the identical hash.
4. Result: status **VERIFIED** (class US_GOVERNMENT: credit NASA/Goddard SVS, do not imply endorsement). Ledger: `productions/v3-demo-salton/media/ledger.json`; the file itself is not in git (media rule).
Blocked in the same session, with the exact reason: NASA Image Library, Wikimedia Commons, EO image files, USGS image host: "CONNECT tunnel failed, response 403" = the environment's network policy, not a licence question.

## Allowed domains: what to add and where (only if the owner wants these sources)
In the Claude Code cloud environment: environment menu in the session title bar -> **Edit** -> **Network access** -> level **Limited** (or Custom) -> **Allowed domains**, then add (keep "Allow package managers" ticked):
`assets.science.nasa.gov`, `images-api.nasa.gov`, `images-assets.nasa.gov`, `images.nasa.gov`, `commons.wikimedia.org`, `upload.wikimedia.org`, `d9-wret.s3.us-west-2.amazonaws.com`, `pubs.usgs.gov`.
Already reachable and needed for nothing more: svs.gsfc.nasa.gov, science.nasa.gov, www.nasa.gov, www.usgs.gov. Docs: https://code.claude.com/docs/en/cloud-environments#network-access . The change applies to the environment (a new session may be needed).
After it is saved: `python3 .claude/skills/yt-media-research/media.py probe` must show those rows as OK.
