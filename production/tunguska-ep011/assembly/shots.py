"""EP011 shot list timed to the real Adam narration (voice/narration.voice.json, sentence starts).
Maps the 47 provisional beats of SHOT_LIST.csv onto the measured speech; never cuts a sentence.
(start_s, scene, params). Event times inside params are LOCAL to the shot. A0 = absolute time helper."""
Y, Wt = (255, 210, 63, 255), (255, 255, 255, 255)
END = 489.3   # narration ends 486.27 s
COVER_CAM = (1250, 640, 1.0)
COVER_E = 2.4  # event state shown on the approved cover A and on frame 0
COVER_TXT = [("NO CRATER?", Wt), ("SIBERIA, 1908", Y)]


def L(a, s):
    return round(a - s, 3)


SHOTS = [
    # S01 hook: exact cover A frame, headline leaves, scene state rewinds to a calm dawn, camera keeps pushing in
    (0.00, "forest", dict(ekeys=[(0, COVER_E), (1.7, COVER_E), (3.6, -12)], cam0=COVER_CAM, cam1=(1150, 700, 1.12), ct0=1.7, ct1=8.56,
                          rewind=(1.7, 3.6), shake=False, cover_grade=(1.7, 3.6), txt=[dict(lines=COVER_TXT, pos="cover", at=0, until=1.7, slide=-1700)])),
    # S08/S10 streak and blast, S11-S12 wave and trees snapping, wide devastated (same world, camera rises)
    (8.56, "forest", dict(ekeys=[(0, -3.7), (L(12.3, 8.56), 0.0), (L(25.41, 8.56), 12.0)], ease=False,
                          cam0=(1150, 700, 1.12), cam1=(1250, 640, 1.0), ct0=0, ct1=L(14, 8.56))),
    # S03 the strange part: an impact would leave a crater; erase it
    (25.41, "crater", dict(ev=dict(expect=0.4, crater=1.6, erase=L(30.0, 25.41)), fallen=True, erase_text="NO GIANT CRATER")),
    (33.85, "section", dict(ev=dict(entry=0.0, burst=3.2, shock=3.4, impact=0.2, impact_x=2.6),
                            impact_label="NO ROCK STRIKING THE GROUND?")),
    (40.03, "card", dict(bg="flat", lines=[dict(text="TUNGUSKA", size=150, col=Y, at=0.3), dict(text="THE MISSING CRATER", size=56, at=1.2)])),
    # S04 modern Landsat
    (45.56, "landsat", dict(z=(1.0, 1.25), c0=(0.5, 0.5), c1=(0.47, 0.62), stamp="LANDSAT 8 · JULY 6, 2024")),
    (55.95, "landsat", dict(z=(1.25, 1.6), c0=(0.47, 0.62), c1=(0.45, 0.72), stamp="LANDSAT 8 · JULY 6, 2024",
                            txt=[dict(lines=[("THE SCAR", Y), ("IS NO LONGER OBVIOUS", Wt)], pos="bl", at=L(62.3, 55.95))])),
    # S05 rewind 2024 -> 1908
    (65.57, "timeline", dict(bg="landsat", years=(2024, 1908), rewind=True, t0=0.6, t1=6.6, marks=[(1908, "JUNE 30, 1908", 5.6)])),
    # S06 where
    (73.42, "globe", dict()),
    # S07 the land
    (81.18, "forest", dict(e=(-14, -14), cam0=(700, 720, 1.18), cam1=(1000, 700, 1.1), tag="ILLUSTRATION · EVENKI HOMELAND, CENTRAL SIBERIA",
                           txt=[dict(lines=[("EVENKI", Y), ("HOMELAND", Wt)], pos="bl", at=0.5)])),
    # S09 witnesses
    (85.89, "forest", dict(ekeys=[(0, -3.5), (3.6, 0.2), (13.3, 1.0)], cam0=(1500, 760, 1.25), cam1=(1350, 700, 1.15),
                           txt=[dict(lines=[("REPORTED:", Y), ("LIGHT · THUNDER", Wt), ("HEAT · BLAST", Wt)], pos="bl", at=1.5, until=8.0),
                                dict(lines=[("MANY ACCOUNTS", Y), ("RECORDED YEARS LATER", Wt)], pos="bl", at=L(94.1, 85.89))])),
    # S10 the atmosphere becomes part of the disaster
    (99.18, "section", dict(ev=dict(entry=-2.0, burst=0.6, shock=1.0, compress=-1, frag=0.3))),
    # S11-S14 wave over the forest, pattern, scale
    (106.43, "radial", dict(ev=dict(wave=0.2), z=(1.0, 1.05))),
    (111.79, "radial", dict(fallen=True, ev=dict(outline=1.0, arrows=2.6), z=(1.05, 1.1))),
    (116.96, "radial", dict(fallen=True, ev=dict(outline=-1, area=0.6, onetree=L(122.0, 116.96)), z=(1.1, 0.92),
                            txt=[dict(lines=[("LANDSCAPE-SCALE", Y), ("DESTRUCTION", Wt)], pos="tl", at=L(126.4, 116.96))])),
    # S15 no camera
    (128.91, "card", dict(bg="flat", lines=[dict(text="NO CAMERA RECORDED IT", size=80, col=Wt, at=0.3),
                                            dict(text="EVERY MOVING IMAGE HERE IS A RECONSTRUCTION", size=46, col=Y, at=L(132.0, 128.91))])),
    # S16 the lost years
    (136.20, "timeline", dict(bg="flat", years=(1908, 1927), t0=0.5, t1=12.0,
                              marks=[(1914, "1914–18: WORLD WAR I", 4.5), (1917, "1917: REVOLUTION", 6.5), (1918, "1918–22: CIVIL WAR", 8.5)])),
    # S17 Kulik (portrait rights unverified -> original name card)
    (149.22, "card", dict(bg="forest", lines=[dict(text="LEONID KULIK", size=110, col=Y, at=0.3), dict(text="MINERALOGIST", size=46, at=0.9),
                                              dict(text="1921: COULD NOT REACH THE SITE", size=50, at=3.6)])),
    (157.43, "timeline", dict(bg="forest", years=(1921, 1927), t0=0.3, t1=4.5, marks=[(1921, "FIRST ATTEMPT", 0.4), (1927, "KULIK REACHES THE SITE", 3.0)])),
    # S19-S20 the 1929 photograph
    (163.75, "archive", dict(z=(1.0, 1.18), c0=(0.45, 0.55), c1=(0.6, 0.45))),
    (171.76, "archive", dict(z=(1.25, 1.4), c0=(0.35, 0.6), c1=(0.55, 0.5), txt=[dict(lines=[("MAY 1929", Y)], pos="bl", at=0.5)])),
    (178.11, "radial", dict(fallen=True, ev=dict(arrows=0.6), z=(1.0, 1.06))),
    (184.08, "treefall", dict(ev=dict(wave=0.3, labels=1.2, center=2.2))),
    (190.31, "radial", dict(fallen=True, ev=dict(outline=0.3, wave=-99), z=(1.06, 1.0))),
    (194.05, "radial", dict(ev=dict(wave=0.2), z=(1.0, 1.06))),
    # S22-S23 searching for a meteorite: what an impact would leave, and what was missing
    (199.61, "crater", dict(ev=dict(expect=L(202.6, 199.61), crater=L(207.3, 199.61), material=L(208.8, 199.61), surface=L(210.2, 199.61)))),
    (212.02, "crater", dict(fallen=True, ev=dict(expect=-5, crater=-5, material=-5, surface=-5, erase=0.4))),
    (219.21, "archive", dict(z=(1.1, 1.0), c0=(0.6, 0.45), c1=(0.5, 0.5),
                             txt=[dict(lines=[("FLATTENED FOREST", Wt), ("NO CRATER", Y)], pos="bl", at=L(222.7, 219.21))])),
    # S24-S30 the physics of an airburst
    (228.04, "section", dict(ev=dict(impact=0.5, impact_x=L(230.6, 228.04)), impact_label="DOES NOT HAVE TO HIT THE GROUND")),
    (235.07, "section", dict(ev=dict(entry=0.0, compress=2.5, stress=L(242.3, 235.07), frag=L(245.6, 235.07), burst=L(246.6, 235.07), shock=L(247.4, 235.07)),
                             txt=[dict(lines=[("AIRBURST", Y)], pos="tl", at=L(250.3, 235.07))])),
    (253.20, "section", dict(ev=dict(entry=L(261.1, 253.2), compress=L(263.4, 253.2), stress=L(263.6, 253.2), frag=L(264.8, 253.2),
                                     burst=L(266.7, 253.2), shock=L(270.6, 253.2)),
                             txt=[dict(lines=[("TENS OF METERS", Y), ("NOT A MOVIE ASTEROID", Wt)], pos="tl", at=1.0, until=L(261.0, 253.2))])),
    (275.54, "forest", dict(ekeys=[(0, 0.6), (L(282.41, 275.54), 9.0)], ease=False, cam0=(1250, 700, 1.15), cam1=(1250, 660, 1.0))),
    (282.41, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, here=0.6, impact=L(287.4, 282.41), impact_x=L(288.0, 282.41)),
                             impact_label="NO ENORMOUS CRATER REQUIRED")),
    # S31-S35 how powerful, how high, what is uncertain
    (290.02, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, energy=L(295.1, 290.02), notmeas=L(308.1, 290.02)),
                             txt=[dict(lines=[("HOW POWERFUL?", Y)], pos="tl", at=0.2, until=L(294.8, 290.02))])),
    (314.00, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, alt=0.5))),
    (321.06, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, unc=0.3))),
    # S33 the trees explain the physics
    (326.61, "treefall", dict(ev=dict(wave=L(331.0, 326.61), labels=L(335.6, 326.61), center=L(340.3, 326.61)))),
    (347.19, "radial", dict(fallen=True, ev=dict(survey=0.4, outline=4.6), z=(1.0, 1.05))),
    (356.38, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, here=L(364.2, 356.38)),
                             txt=[dict(lines=[("AN ABSENCE", Wt), ("AS EVIDENCE", Y)], pos="tl", at=0.3, until=L(364.0, 356.38))])),
    # S36-S37 other possibilities
    (367.65, "landsat", dict(z=(1.3, 1.9), c0=(0.45, 0.6), c1=(0.27, 0.15), cheko=L(373.4, 367.65), stamp="LANDSAT 8 · JULY 6, 2024")),
    (377.27, "card", dict(bg="flat", y=250, lines=[dict(text="STILL DEBATED", size=40, col=Y, at=0.2), dict(text="TINY PARTICLES", size=58, at=0.9),
                                                   dict(text="FOREST GROWTH HISTORY", size=58, at=1.8), dict(text="SIMULATED FLIGHT PATHS", size=58, at=3.0),
                                                   dict(text="LEADING EXPLANATION: AN AIRBURST", size=50, col=Y, at=L(390.1, 377.27))])),
    # S38-S39 Chelyabinsk 2013 (schematic, never Tunguska footage)
    (397.94, "city", dict(ev=dict(streak=L(401.7, 397.94), burst=L(405.5, 397.94), wave=L(409.5, 397.94)),
                          txt=[dict(lines=[("A RECENT AIRBURST", Y)], pos="tl", at=0.3, until=L(401.6, 397.94))])),
    (414.82, "city", dict(ev=dict(streak=-20, burst=-16, wave=-10),
                          txt=[dict(lines=[("NOT TUNGUSKA", Y), ("SAME PHYSICS, SMALLER SCALE", Wt)], pos="tl", at=0.3)])),
    # S42-S43 back to the 2024 image
    (427.19, "landsat", dict(z=(1.0, 1.35), c0=(0.5, 0.5), c1=(0.47, 0.72), epi=L(431.1, 427.19), stamp="LANDSAT 8 · JULY 6, 2024")),
    (439.77, "landsat", dict(z=(1.35, 1.1), c0=(0.47, 0.72), c1=(0.5, 0.6), epi=-1, stamp="LANDSAT 8 · JULY 6, 2024")),
    # S40-S41 planetary defense
    (442.21, "sky", dict(txt=[dict(lines=[("FIND THEM", Y), ("BEFORE THEY ARRIVE", Wt)], pos="tl", at=L(453.1, 442.21))])),
    # S44 back to the hook composition, then the full event once more
    (456.88, "forest", dict(ekeys=[(0, -2.5), (2.6, 0.0), (7.0, 6.0), (L(471.96, 456.88), 10.0)], ease=False,
                            cam0=(1150, 700, 1.12), cam1=COVER_CAM, ct0=0, ct1=6.5,
                            txt=[dict(lines=[("NO CRATER", Y), ("NEVER APPEARED", Wt)], pos="tl", at=L(461.3, 456.88), until=L(471.8, 456.88))])),
    # S45 central explanation
    (471.96, "section", dict(ev=dict(entry=-9, burst=-6, shock=-5.2, here=0.4), here_label="AN EXPLOSION IN THE SKY")),
    # S46-S47 last line on today's forest, credits
    (480.14, "landsat", dict(z=(1.2, 1.0), c0=(0.47, 0.7), c1=(0.5, 0.5), stamp="ORBITAL ATLAS",
                             txt=[dict(lines=[("THE SHOCK WAVE", Wt), ("DID THE DAMAGE", Y)], pos="bl", at=L(483.6, 480.14))])),
]
