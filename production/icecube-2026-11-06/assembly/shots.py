"""IceCube long-form shot list, timed to the real Adam narration (narration.voice.json).
Each shot: start second (sentence starts from the provider word timings), kind, source, in-point, options.
mi=True: motion-compensated 23.976->30 fps for camera-move shots (judder fix). kind: live (V01 field footage), anim (own schematics A01-A04 or NASA visualizations), photo (P01/P02).
Options: z=(zoom0, zoom1), c0/c1=(x, y) crop centre 0..1, rev=True plays the clip backwards,
txt=[overlay items], split=(srcB, inB) side-by-side, contain=True whole-photo inset (P01, unmodified)."""

END = 337.40  # narration ends 334.65 s; ~2.7 s of air on the last shot

CR_V01 = "ANTARCTIC FIELD FOOTAGE · NASA 88-SOUTH TRAVERSE, 2019 · NOT ICECUBE CONSTRUCTION"
CR_V01s = "NASA FIELD FOOTAGE · ANTARCTICA, 2019"
CR_VIS = "VISUALIZATION: NASA GODDARD / CONCEPTUAL IMAGE LAB"
CR_P01 = "ICECUBE LAB, SOUTH POLE · PHOTO: CHRISTOPHER MICHEL, CC BY-SA 4.0 · UNMODIFIED"
CR_P02 = "ICECUBE OPTICAL MODULE · PHOTO: DESY, CC BY 4.0 · CROPPED"

def cr(t):  # credit tag, top-left
    return {"tag": t, "pos": "tl"}

def big(lines, pos="tr"):  # headline overlay: list of (text, colour) lines
    return {"big": lines, "pos": pos}

W_, Y_ = "#FFFFFF", "#FFD23F"

SHOTS = [
    # 01 hook: the visible building, then straight under the snow
    # 0.00 approved cover B, exact frame; 0.3 s camera heads for the lab (headline leaves left),
    # then curves down the yellow arrow into the ice; cut on the downward move into A01 with the depth scale
    (0.00,   "photo", "C01", 0.0,  dict(bez=dict(t0=0.3, t1=2.6, P=((0.5, 0.5), (0.95, 0.05), (0.73, 0.75)), zmax=2.0, zt=0.55))),
    (2.60,   "anim",  "A01", 7.8,  dict(z=(1.4, 1.0), c0=(0.62, 0.36), c1=(0.5, 0.5), ease="out")),
    (10.86,  "anim",  "V03", 0.0,  dict(txt=[cr(CR_VIS)])),
    (16.63,  "live",  "V01", 200.5, dict(txt=[cr(CR_V01)])),
    (19.59,  "anim",  "A03", 0.0,  dict(z=(1.0, 1.06), txt=[big([("NEUTRINOS", Y_), ("PASS STRAIGHT THROUGH", W_)], "br")])),
    (24.46,  "live",  "V01", 3.0,  dict(txt=[cr(CR_V01s)])),
    (26.11,  "live",  "V01", 162.0, dict(mi=True, txt=[cr(CR_V01s)])),
    # 02 reveal the instrument
    (30.89,  "anim",  "A02", 0.0,  dict(z=(1.0, 1.06))),
    (34.83,  "anim",  "A01", 4.0,  dict(z=(1.0, 1.45), c1=(0.62, 0.5))),
    (43.11,  "anim",  "A01", 11.0, dict(z=(1.3, 1.0), c0=(0.45, 0.55),
                                       txt=[big([("86 CABLES", Y_), ("5,160 OPTICAL MODULES", W_)], "tr")])),
    (48.87,  "live",  "V01", 181.0, dict(txt=[cr(CR_V01)])),
    (52.94,  "anim",  "A01", 9.0,  dict(z=(1.8, 2.0), c0=(0.45, 0.55), c1=(0.45, 0.57))),
    (58.03,  "photo", "P01", 0.0,  dict(contain=True, z=(1.035, 1.0), txt=[cr(CR_P01)])),
    (61.24,  "live",  "V01", 100.0, dict(txt=[cr(CR_V01s)])),
    # 03 why the target is difficult
    (64.33,  "live",  "V01", 238.0, dict(txt=[cr(CR_V01s), big([("NEUTRINOS", Y_), ("NO ELECTRIC CHARGE", W_), ("ALMOST NO MASS", W_)], "br")])),
    (69.09,  "live",  "V01", 141.0, dict(mi=True, txt=[cr(CR_V01s)])),
    (74.20,  "anim",  "V03", 3.25,  dict(txt=[cr(CR_VIS), big([("~100 TRILLION", Y_), ("NEUTRINOS THROUGH YOU", W_), ("EVERY SECOND", W_)], "br")])),
    (79.63,  "live",  "V01", 43.0, dict(txt=[cr(CR_V01s)])),
    (83.42,  "anim",  "A03", 0.0,  dict(z=(1.0, 1.06))),
    (89.15,  "anim",  "A01", 6.0,  dict(z=(1.8, 1.0), c0=(0.45, 0.55))),
    (95.17,  "live",  "V01", 62.0, dict(txt=[cr(CR_V01s)])),
    (99.98,  "anim",  "V02", 0.5,  dict(txt=[cr(CR_VIS)])),
    (103.62, "live",  "V01", 243.0, dict(txt=[cr(CR_V01s)])),
    # 04 how to build it
    (107.65, "anim",  "A02", 0.0,  dict(z=(1.0, 1.06))),
    (113.13, "anim",  "A02", 6.0,  dict(z=(1.0, 1.06))),
    (119.44, "anim",  "A02", 18.0, dict(z=(1.0, 1.06), rev=True, txt=[big([("IN REVERSE", Y_)], "br")])),
    (121.71, "photo", "P02", 0.0,  dict(z=(1.0, 1.12), c1=(0.5, 0.62), txt=[cr(CR_P02)])),
    (124.56, "anim",  "A02", 15.0, dict(z=(1.0, 1.06), rev=True)),
    (126.78, "live",  "V01", 150.0, dict(mi=True, txt=[cr(CR_V01s)])),
    (132.25, "live",  "V01", 80.0, dict(txt=[cr(CR_V01), big([("BUILT 2004–2010", Y_), ("ANTARCTIC SUMMERS ONLY", W_)], "br")])),
    (138.28, "anim",  "A01", 12.0, dict(z=(1.0, 1.06), txt=[big([("86 × 60", Y_), ("= 5,160", W_)], "tr")])),
    (144.39, "live",  "V01", 21.0, dict(txt=[cr(CR_V01s)])),
    (149.49, "live",  "V01", 224.0, dict(txt=[cr(CR_V01s)])),
    (153.08, "anim",  "A02", 13.4, dict(z=(1.0, 1.06))),
    # 05 what a detection means
    (157.57, "anim",  "A03", 0.0,  dict(z=(1.0, 1.06))),
    (162.42, "anim",  "A03", 4.85, dict(z=(1.0, 1.06))),
    (166.74, "anim",  "A03", 9.17, dict(z=(1.0, 1.06),
                                       txt=[big([("CHERENKOV LIGHT", Y_), ("FAINT BLUE GLOW IN ICE", W_)], "tr")])),
    (174.20, "live",  "V01", 52.0, dict(txt=[cr(CR_V01s)])),
    (177.42, "live",  "V01", 121.0, dict(mi=True, 
                                       txt=[big([("FASTER THAN LIGHT IN ICE", Y_), ("NOT FASTER THAN LIGHT IN A VACUUM", W_)], "tr")])),
    (181.41, "anim",  "A04", 0.0,  dict(z=(1.0, 1.06))),
    (188.21, "anim",  "A04", 6.8,  dict(z=(1.0, 1.06))),
    (193.99, "anim",  "A01", 8.6,  dict(z=(1.0, 1.06))),
    (198.52, "live",  "V01", 75.0, dict(txt=[cr(CR_V01s)])),
    (202.79, "anim",  "A03", 5.6,  dict(z=(1.0, 1.06))),
    (208.97, "photo", "P02", 0.0,  dict(z=(1.25, 1.1), c0=(0.5, 0.7), txt=[cr(CR_P02)])),
    (213.03, "anim",  "A04", 3.0,  dict(z=(1.06, 1.0))),
    # 06 a message and a direction
    (216.90, "live",  "V01", 30.0, dict(txt=[cr(CR_V01s)])),
    (220.90, "live",  "V01", 10.0, dict(txt=[cr(CR_V01s)] + [big([("2013", Y_), ("HIGH-ENERGY NEUTRINOS", W_), ("FROM BEYOND THE SOLAR SYSTEM", W_)], "tr")])),
    (225.15, "anim",  "V02", 3.0,  dict(txt=[cr(CR_VIS)])),
    (228.52, "live",  "V01", 89.0, dict(txt=[cr(CR_V01s)])),
    (233.58, "anim",  "A03", 4.0,  dict(z=(1.0, 1.06), txt=[big([("SEPT 22, 2017", Y_), ("ONE HIGH-ENERGY EVENT", W_)], "tr")])),
    (238.50, "anim",  "A04", 0.0,  dict(z=(1.0, 1.06), txt=[big([("ALERT SENT", Y_), ("TO ASTRONOMERS", W_)], "tr")])),
    (243.56, "anim",  "A04", 6.0,  dict(z=(1.0, 1.06))),
    (248.33, "live",  "V01", 228.5, dict(txt=[cr(CR_V01s)])),
    (251.44, "anim",  "V04", 0.0,  dict(txt=[cr(CR_VIS), big([("FERMI SEES GAMMA RAYS", Y_), ("NOT THE NEUTRINO", W_)], "br")])),
    (257.00, "anim",  "V02", 6.0,  dict(txt=[cr(CR_VIS), big([("BLAZAR TXS 0506+056", Y_), ("FLARING IN GAMMA RAYS", W_)], "br")])),
    (263.72, "anim",  "V02", 12.0, dict(txt=[cr(CR_VIS), big([("BLAZAR", Y_), ("ACTIVE GALAXY · JET AIMED NEAR US", W_)], "br")])),
    (269.31, "anim",  "V03", 2.0,  dict(split=("V04", 3.5), txt=[cr(CR_VIS)])),
    (275.67, "anim",  "A04", 12.0, dict(z=(1.0, 1.06), txt=[big([("2018", Y_), ("EVIDENCE LINKING THE TWO", W_)], "br")])),
    (279.32, "live",  "V01", 233.0, dict(txt=[cr(CR_V01s)])),
    (283.50, "anim",  "A04", 13.5, dict(z=(1.0, 1.06))),
    (287.65, "anim",  "A03", 9.0,  dict(z=(1.0, 1.06), txt=[big([("ICECUBE", Y_), ("THE PARTICLE CLUE", W_)], "br")])),
    (290.55, "anim",  "V04", 5.5,  dict(txt=[cr(CR_VIS), big([("TELESCOPES", Y_), ("THE LIGHT", W_)], "br")])),
    # 07 return to the ice
    (292.48, "live",  "V01", 47.0, dict(txt=[cr(CR_V01s)])),
    (295.32, "live",  "V01", 206.0, dict(txt=[cr(CR_V01s)])),
    (300.12, "live",  "V01", 170.0, dict(txt=[cr(CR_V01s)])),
    (305.16, "anim",  "A01", 14.0, dict(z=(1.0, 1.06), txt=[big([("ORIGINAL ARRAY", Y_), ("COMPLETED 2010", W_)], "tr")])),
    (310.16, "anim",  "A02", 0.0,  dict(z=(1.0, 1.06), txt=[big([("ICECUBE UPGRADE", Y_), ("DEPLOYED 2026", W_)], "br")])),
    (314.88, "anim",  "A01", 11.5, dict(z=(1.06, 1.0), txt=[big([("5,160 MODULES", Y_), ("= ORIGINAL ARRAY ONLY", W_)], "tr")])),
    (320.30, "photo", "P01", 0.0,  dict(contain=True, z=(1.0, 1.035), txt=[cr(CR_P01)])),
    (323.27, "anim",  "A01", 0.0,  dict(z=(1.0, 1.06))),
    (328.91, "anim",  "A03", 0.0,  dict(z=(1.0, 1.06))),
    (331.42, "anim",  "A04", 12.0, dict(z=(1.0, 1.06))),
    (333.90, "live",  "V01", 251.0, dict(fadeout=1.2)),
]
