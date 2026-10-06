# Visual plan: northwest-angle (research stage)

Rules: `channel/visual-style.md`. Check with:

```bash
python3 .claude/skills/geo-visuals/assets.py channel/videos/northwest-angle/visuals.md --credits
```

Stage: **asset research only** - beats are from the brief, not a script. License statuses are as
reported by each publisher's policy page (search-quoted; the pages themselves could not be opened from
this environment). Before the edit, open each item page and confirm there is no item-level rights
advisory - a site-wide policy does not cover an item that carries its own restriction.

Second pass (2026-10-06): of the asset hosts, only www2.census.gov (V5, V9) and history.state.gov /
avalon.law.yale.edu (V10, V11 - treaty text) were reachable. loc.gov, NASA, USGS and OSM are still
blocked, so V1-V4, V7 and V8 are unchanged and still need their item pages checked by hand. The
TIGER files listed under V5 were downloaded and opened; the geometry in claims C7, C20, C23-C25 was
computed from them, so the animated maps and the ledger use the same data.

| ID | Beat | Type | Description | Source | URL | License | Attribution | AI |
|---|---|---|---|---|---|---|---|---|
| V1 | 1783 / map reveal | archival | John Mitchell, "A Map of the British and French Dominions in North America", 1755 (LoC copy 1) - oval Lake of the Woods, Mississippi running under the inset | Library of Congress, Geography and Map Division, g3300.ar004401 | https://hdl.loc.gov/loc.gmd/g3300.ar004401 | public-domain | Library of Congress, Geography and Map Division | no |
| V2 | 1783 / map reveal | archival | Second LoC Mitchell copy for close-ups (resolution / condition choice) | Library of Congress, g3300.np000009 | https://www.loc.gov/resource/g3300.np000009/ | public-domain | Library of Congress, Geography and Map Division | no |
| V3 | today / locator | satellite | "An Unusual Angle" - Landsat 8 OLI, Sept 20, 2015, the Angle and Lake of the Woods | NASA Earth Observatory image 91258 | https://earthobservatory.nasa.gov/images/91258/an-unusual-angle | us-gov | NASA Earth Observatory image, Landsat data from USGS | no |
| V4 | today / locator | satellite | "Northwest Angle, Minnesota" - earlier NASA view of the same area | NASA Visible Earth image 6357 | https://visibleearth.nasa.gov/images/6357/northwest-angle-minnesota | us-gov | NASA | no |
| V5 | all map beats | animated-map | U.S. / Minnesota / county / township boundaries, roads (MN 313) - our own animated maps built from the data. Files used: tl_2025_us_state, tl_2025_27_cousub (Angle township, GEOID 2707701550). Pin the 1925 point at 49.384581°N, 95.153225°W [C24]; shade the township part north of 49°N for the Angle, not the whole township [C20] | U.S. Census Bureau TIGER/Line Shapefiles 2025 | https://www2.census.gov/geo/tiger/TIGER2025/ | us-gov | Source: U.S. Census Bureau, TIGER/Line Shapefiles | no |
| V6 | 1818 / 49th parallel | animated-map | Continental base map, lakes, rivers incl. the Mississippi to Lake Itasca, the 49th parallel graticule | Natural Earth (public-domain vector data) | https://www.naturalearthdata.com | public-domain | Made with Natural Earth | no |
| V7 | today / islands, winter | satellite | Additional Landsat scenes (open water vs winter ice) downloaded and processed by us | USGS EarthExplorer - Landsat | https://www.usgs.gov/faqs/are-landsat-data-cloud-still-considered-be-within-public-domain | us-gov | Landsat imagery courtesy of the U.S. Geological Survey | no |
| V8 | the drive | map | Manitoba road network (PR 12, PR 308, PR 525) for the route animation | OpenStreetMap data | https://www.openstreetmap.org | odbl | © OpenStreetMap contributors | no |
| V9 | 1783 due-west line vs the real Mississippi | map | The Mississippi's northernmost reach (47.457°N, Beltrami Co.) and Lake Itasca (47.19-47.24°N) against the due-west line at 49°23'N [C7]. Built from TIGER 2025 linear water (MN counties 001, 007, 021, 029, 035, 057, 061) and area water (029). Label Itasca as "the source" only if C9 verifies | U.S. Census Bureau TIGER/Line 2025 + Natural Earth | https://www2.census.gov/geo/tiger/TIGER2025/LINEARWATER/ | public-domain | Made with Natural Earth; U.S. Census Bureau | no |
| V10 | 1818 / the rule that makes the Angle | graphic | On-screen quote of Convention of 1818, Art. 2 ("...due North or South as the Case may be, until the said Line shall intersect the said Parallel...") typeset by us [C11] | Avalon Project, Yale Law School (treaty text) | https://avalon.law.yale.edu/19th_century/conv1818.asp | public-domain | Text: Convention of 1818, Art. 2 | no |
| V11 | 1925 / the new point and the 2.5-acre pockets | graphic | On-screen quote of the 1925 treaty, Art. I (five crossing points; "two small areas of United States waters ... two and one-half acres") typeset by us, over a V5 map [C19, C43] | U.S. Department of State, Office of the Historian - FRUS 1925 v1 doc 387 | https://history.state.gov/historicaldocuments/frus1925v01/d387 | us-gov | Text: Treaty of February 24, 1925, via Foreign Relations of the United States | no |

## Pending - license must be checked item by item before use

| Asset | Source | What it would illustrate | Why pending |
|---|---|---|---|
| Treaty of Paris (1783) original document image | National Archives / Library of Congress | the treaty wording on screen | NARA/LoC items are usually free to use, but confirm the specific item's rights statement |
| Tiarks / Thompson 1820s survey maps of Lake of the Woods | Archives of Ontario; possibly U.S. National Archives (RG 76) | the hunt for the "northwestern point" | rights unknown; Ontario Crown copyright may apply |
| Webster-Ashburton / Treaty of Ghent boundary sheets | Library of Congress (tile.loc.gov), NARA RG 76 | the 1820s-1842 line | item rights not yet checked |
| 1920 Minnesota state road map | MnDOT Digital Library (item m3463) | historical road context | item shows "No Copyright - United States" (search-quoted); confirm on the item page |
| CBP ROAM app / reporting-site images | U.S. CBP | the remote check-in | U.S. government work, but app screenshots and any third-party photos need checking |
| Angle Inlet School, resorts, ice-road footage | none found | human beats | **no licensed footage located** - needs stock purchase, a licensed photographer, or illustration |

## Rejected - do not use without written permission or human legal review

| Asset | Source | Reason |
|---|---|---|
| Official IBC boundary maps (Section D, Lake of the Woods) | International Boundary Commission | IBC terms: commercial redistribution requires prior written permission. A government/binational body is NOT automatically public domain. Use TIGER-derived boundaries instead. |
| David Rumsey Map Collection scans | davidrumsey.com | CC BY-NC-SA - our NC rule fails it, even though the collection defines "commercial" narrowly. Request permission or use LoC equivalents. |
| Minnesota Historical Society images | MNHS | permission required per use (one-time, one-project). Some MNopedia images are CC BY-SA - check each one individually if wanted. |
| MinnPost / news photos | publishers | copyrighted |
| Screenshots of other YouTube videos | - | never |

## Beat coverage (from the brief)

| Beat | Covered by | Weak spot |
|---|---|---|
| Locator / the bump | V3, V5 | - |
| The drive through Manitoba | V5, V8, V7 | no ground-level footage of the road or the check-in shed |
| 1755 map | V1, V2 | - |
| 1783 due-west line vs the real Mississippi | V6, V9 over V1 | V1 beat still depends on C3-C5 (UNVERIFIED) |
| 1818 parallel and the drop due south | V5, V6, V10 | - |
| 1825 Tiarks point | animated map | historic survey map pending; C14 still UNVERIFIED |
| 1925 point and the water pockets | V5, V11 | exact pocket outlines not available (IBC maps rejected) - show schematically and label as such |
| Life today (school, mail, fishing, COVID) | - | **no licensed visuals yet** - biggest gap |
| Ice road | V7 | no ground footage |

## Upload notes
- Altered/synthetic disclosure: not triggered by the assets above (no AI).
- Credits block: run `assets.py --credits`.
