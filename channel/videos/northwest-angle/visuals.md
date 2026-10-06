# Visual plan: northwest-angle (research stage)

Rules: `channel/visual-style.md`. Check with:

```bash
python3 .claude/skills/geo-visuals/assets.py channel/videos/northwest-angle/visuals.md --credits
```

Stage: **asset research only** - beats are from the brief, not a script. License statuses are as
reported by each publisher's policy page (search-quoted; the pages themselves could not be opened from
this environment). Before the edit, open each item page and confirm there is no item-level rights
advisory - a site-wide policy does not cover an item that carries its own restriction.

| ID | Beat | Type | Description | Source | URL | License | Attribution | AI |
|---|---|---|---|---|---|---|---|---|
| V1 | 1783 / map reveal | archival | John Mitchell, "A Map of the British and French Dominions in North America", 1755 (LoC copy 1) - oval Lake of the Woods, Mississippi running under the inset | Library of Congress, Geography and Map Division, g3300.ar004401 | https://hdl.loc.gov/loc.gmd/g3300.ar004401 | public-domain | Library of Congress, Geography and Map Division | no |
| V2 | 1783 / map reveal | archival | Second LoC Mitchell copy for close-ups (resolution / condition choice) | Library of Congress, g3300.np000009 | https://www.loc.gov/resource/g3300.np000009/ | public-domain | Library of Congress, Geography and Map Division | no |
| V3 | today / locator | satellite | "An Unusual Angle" - Landsat 8 OLI, Sept 20, 2015, the Angle and Lake of the Woods | NASA Earth Observatory image 91258 | https://earthobservatory.nasa.gov/images/91258/an-unusual-angle | us-gov | NASA Earth Observatory image, Landsat data from USGS | no |
| V4 | today / locator | satellite | "Northwest Angle, Minnesota" - earlier NASA view of the same area | NASA Visible Earth image 6357 | https://visibleearth.nasa.gov/images/6357/northwest-angle-minnesota | us-gov | NASA | no |
| V5 | all map beats | animated-map | U.S. / Minnesota / county / township boundaries, roads (MN 313) - our own animated maps built from the data | U.S. Census Bureau TIGER/Line Shapefiles (current year) | https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2025/TGRSHP2025_TechDoc.pdf | us-gov | Source: U.S. Census Bureau, TIGER/Line Shapefiles | no |
| V6 | 1818 / 49th parallel | animated-map | Continental base map, lakes, rivers incl. the Mississippi to Lake Itasca, the 49th parallel graticule | Natural Earth (public-domain vector data) | https://www.naturalearthdata.com | public-domain | Made with Natural Earth | no |
| V7 | today / islands, winter | satellite | Additional Landsat scenes (open water vs winter ice) downloaded and processed by us | USGS EarthExplorer - Landsat | https://www.usgs.gov/faqs/are-landsat-data-cloud-still-considered-be-within-public-domain | us-gov | Landsat imagery courtesy of the U.S. Geological Survey | no |
| V8 | the drive | map | Manitoba road network (PR 12, PR 308, PR 525) for the route animation | OpenStreetMap data | https://www.openstreetmap.org | odbl | © OpenStreetMap contributors | no |
| V9 | 1832 / the river's real source | map | Itasca / headwaters locator - built from V5/V6 data | Natural Earth + Census TIGER | https://www.naturalearthdata.com | public-domain | Made with Natural Earth; U.S. Census Bureau | no |

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
| 1783 due-west line vs the real Mississippi | V6, V9 over V1 | - |
| 1818 parallel and the drop due south | V5, V6 | - |
| 1825 Tiarks point | animated map | historic survey map pending |
| Life today (school, mail, fishing, COVID) | - | **no licensed visuals yet** - biggest gap |
| Ice road | V7 | no ground footage |

## Upload notes
- Altered/synthetic disclosure: not triggered by the assets above (no AI).
- Credits block: run `assets.py --credits`.
