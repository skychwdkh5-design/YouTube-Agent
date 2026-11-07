"""EP012 storyboard as data: narration phrase -> source file -> source interval -> on-screen action.
Shot starts are anchored to word times of the real narration (timeline.word), mapped to film time with V()."""
from timeline import V, word, END, NDUR

C_UA = "NASA/Goddard/University of Arizona"
C_CIL = "NASA Goddard Space Flight Center Conceptual Image Lab"
C_M03 = "NASA/Goddard/CI Lab"
C_SVS = "NASA SVS · data: NASA/University of Arizona/CSA/York University/Open University/MDA"
C_GSFC = "NASA Goddard Space Flight Center"
C_NAV = "NASA Goddard Space Flight Center · NASA/Goddard/University of Arizona"

M08_REG = (240, 0, 1680, 1080)
M09_REG = (240, 0, 1680, 1080)
M11_REG = (0, 16, 1280, 720)

W_ = word  # shorthand

# event reveal times on the contact HUD (narration -> film)
EV = [V(W_("touches Nightingale.")), V(W_("About one second later")), V(W_("At about six seconds")),
      V(W_("Only at about nine")), V(W_("Around sixteen seconds")), V(W_("And at about thirty"))]
CONTACT_FILE_T = 10.6  # M04 file time of contact (gas puff onset ~1 s later, thrusters visible at 16.6 s)


def S(n_start, kind, **p):
    return dict(t0=V(n_start) if n_start > 0 else 0.0, kind=kind, **p)


def clip(src, a, b, **k):
    return dict(src=src, a=a, b=b, **k)


SHOTS = [
    # ---- HOOK: cover composition comes alive (real SamCam photos, sped up)
    S(0.0, "open", **clip("M01", 4.4, 6.93, label=("real", "SAMCAM · STILL PHOTOS, SPED UP"), credit=C_UA)),
    S(W_("touch the surface,"), "clip", **clip("M01", 6.93, 8.55, fit="fit", zoom=(1.0, 1.06), fc=(500, 560),
                                              label=("real", "SAMCAM · STILL PHOTOS, SPED UP"), credit=C_UA)),
    S(W_("But the surface barely"), "clip", **clip("M04", 11.6, 21.6, zoom=(1.0, 1.18), fc=(1020, 700),
                                                  label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL,
                                                  chips=[(V(W_("The sampler's arm kept")), "THE SAMPLER ARM KEEPS SINKING", 960, 120, 42, "y")])),
    S(W_("So why did a world"), "clip", **clip("M08", 1.8, 10.6, fit="fit", region=M08_REG,
                                              label=("real", "NAVCAM 2 · 10 FPS IMAGE SEQUENCE"), credit=C_NAV)),
    # ---- WHY GO
    S(W_("The spacecraft was OSIRIS-REx,"), "clip", **clip("M03", 0.0, 6.5, zoom=(1.0, 1.1), fc=(860, 300),
                                                          label=("anim", ""), credit=C_M03,
                                                          chips=[(V(W_("The spacecraft was OSIRIS-REx,")) + 0.4, "OSIRIS-REx", 960, 860, 56, "y"),
                                                                 (V(W_("back to Earth,")), "GOAL: BRING A SAMPLE BACK TO EARTH", 960, 960, 34, None)])),
    S(W_("Up close, Bennu"), "clip", **clip("M08", 19.0, 30.0, fit="fit", region=M08_REG, zoom=(1.0, 1.08),
                                           label=("real", "NAVCAM 2 · 10 FPS IMAGE SEQUENCE"), credit=C_NAV,
                                           chips=[(V(W_("crowded with boulders.")), "CROWDED WITH BOULDERS", 960, 120, 42, None),
                                                  (V(W_("a site they named")), "TARGET SITE: NIGHTINGALE", 960, 120, 46, "y")])),
    S(W_("The tool for the job"), "clip", **clip("M03", 6.5, 20.3, label=("anim", "TAGSAM"), credit=C_M03,
                                                chips=[(V(W_("The tool for the job")) + 0.3, "TAGSAM", 960, 110, 56, "y"),
                                                       (V(W_("Touch-And-Go")), "TOUCH-AND-GO SAMPLE ACQUISITION MECHANISM", 960, 110, 36, None),
                                                       (V(W_("It's not a drill,")), "NOT A DRILL · THE SPACECRAFT DOES NOT LAND", 960, 110, 36, None),
                                                       (V(W_("It's a round head")), "ROUND HEAD ON A LONG ARM", 960, 110, 40, "y"),
                                                       (V(W_("The head touches the surface,")), "GAS PUSHES LOOSE MATERIAL INTO THE COLLECTOR", 960, 110, 34, None)])),
    # ---- AUTONOMOUS
    S(W_("On October 20,"), "clip", **clip("M04", 0.0, 4.9, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL,
                                          chips=[(V(W_("On October 20,")) + 0.2, "OCTOBER 20, 2020", 960, 120, 56, "y")])),
    S(W_("But nobody on Earth"), "signal", t_delay=V(W_("Before the event,")), t_slow=V(W_("That's far too slow")),
      t_auto=V(W_("So the whole approach"))),
    S(W_("The spacecraft lowered itself"), "clip", **clip("M08", 30.2, 36.4, fit="fit", region=M08_REG,
                                                         label=("real", "NAVCAM 2 · 10 FPS IMAGE SEQUENCE"), credit=C_NAV,
                                                         chips=[(V(W_("met the surface")), "≈ 10 CM/S AT CONTACT", 960, 120, 48, "y"),
                                                                (V(W_("That's about four inches")), "≈ 4 INCHES PER SECOND", 960, 230, 34, None)])),
    # ---- SECOND BY SECOND (M04 clock: T = file - 10.6)
    S(W_("Here's what happened next,"), "clip", **clip("M04", 5.0, 10.0, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True)),
    S(W_("Zero seconds."), "clip", **clip("M04", 10.0, 11.0, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True, cut=True,
                                         zoom=(1.0, 1.25), fc=(1000, 640))),
    S(W_("Not the spacecraft's body."), "clip", **clip("M04", 11.0, 11.55, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True,
                                                      callouts=[("ring", 880, 640, 130, V(W_("Just the head,")))],
                                                      chips=[(V(W_("Not the spacecraft's body.")), "ONLY THE SAMPLER HEAD TOUCHES", 960, 130, 42, "y")])),
    S(W_("About one second later,"), "clip", **clip("M04", 11.6, 14.6, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True, cut=True)),
    S(W_("That bright burst"), "clip", **clip("M02", 0.0, 7.0, fit="fit", label=("real", "SAMCAM · STILL PHOTOS"), credit=C_UA,
                                              chips=[(V(W_("Not fire,")), "GAS-LIFTED DUST AND GRAVEL · NOT FIRE", 960, 120, 38, "y")])),
    S(W_("At about six seconds,"), "clip", **clip("M04", 16.3, 19.4, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True,
                                                 zoom=(1.05, 1.15), fc=(1000, 640))),
    S(W_("Only at about nine"), "clip", **clip("M04", 19.4, 21.2, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True,
                                              zoom=(1.15, 1.2), fc=(1000, 640), cut=True)),
    S(W_("By then, the sampler's"), "cross", mode="depth"),
    S(W_("Around sixteen seconds,"), "clip", **clip("M04", 25.6, 29.6, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud=True)),
    S(W_("And at about thirty"), "clip", **clip("M04", 51.2, 57.6, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud="noclock")),
    # ---- WHY SO SOFT
    S(W_("So why so little"), "cross", mode="pit", t_loose=V(W_("loosely packed,")), t_weak=V(W_("weakly bound")),
      t_balls=V(W_("a lot like the plastic"))),
    S(W_("NASA's animation shows"), "clip", **clip("M06", 3.0, 8.9, label=("anim", "CONCEPT COMPARISON"), credit=C_CIL)),
    S(W_("On the Moon,"), "clip", **clip("M06", 8.9, 11.4, label=("anim", "CONCEPT COMPARISON"), credit=C_CIL, cut=True)),
    S(W_("On Bennu, the grains"), "clip", **clip("M06", 18.4, 21.6, label=("anim", "CONCEPT COMPARISON"), credit=C_CIL)),
    S(W_("The boulders on top"), "cross", mode="notsolid", t_ghost=V(W_("And according to NASA's analysis,"))),
    S(W_("That doesn't make Bennu"), "clip", **clip("M02", 11.0, 19.5, fit="fit", label=("real", "SAMCAM · STILL PHOTOS AFTER CONTACT"), credit=C_UA,
                                                   chips=[(V(W_("That doesn't make Bennu")) + 0.3, "NOT LIQUID · NOT HOLLOW", 960, 120, 44, "y"),
                                                          (V(W_("It means the surface")), "A LOOSE LAYER OF WEAKLY BOUND PARTICLES", 960, 120, 36, None)])),
    # ---- THE MARK
    S(W_("The site itself shows"), "ba", t_before=V(W_("March 7,")), t_after=V(W_("and again on April")),
      t_flip=V(W_("Flip between them,")), t_moved=V(W_("Material has been moved.")), t_ruler=V(W_("NASA described the hollow"))),
    S(W_("In this elevation model"), "clip", **clip("M05", 9.6, 20.3, label=("model", "SURFACE HEIGHT CHANGE"), credit=C_SVS,
                                                  callouts=[("ring", 120, 72, 46, V(W_("Blue is where")))],
                                                  chips=[(V(W_("Blue is where")), "BLUE = LARGEST DROP IN HEIGHT", 960, 960, 36, "y")])),
    S(W_("Three things disturbed"), "clip", **clip("M05", 28.0, 37.6, label=("model", "SURFACE HEIGHT CHANGE"), credit=C_SVS,
                                                  chips=[(V(W_("Three things disturbed")), "THREE CAUSES", 960, 120, 44, "y"),
                                                         (V(W_("the sampler head pressing")), "1  SAMPLER HEAD PRESSING IN", 960, 760, 34, None),
                                                         (V(W_("the nitrogen gas")), "2  NITROGEN GAS", 960, 845, 34, None),
                                                         (V(W_("and the thrusters firing")), "3  BACK-AWAY THRUSTERS", 960, 930, 34, None)])),
    # ---- SECOND TWIST
    S(W_("Then came a second problem."), "clip", **clip("M09", 0.0, 6.7, label=("real", "SPACECRAFT CAMERA · OCT 2020"), credit=C_GSFC,
                                                       chips=[(V(W_("Then came a second problem.")) + 0.2, "SECOND PROBLEM", 960, 120, 46, "r")])),
    S(W_("Something was off."), "leak", t_rock=V(W_("The team's interpretation:")), src="M09", a=6.7, b=9.7),
    S(W_("The next step mattered."), "clip", **clip("M09", 10.4, 15.9, fit="fit", region=M09_REG, label=("real", "SPACECRAFT CAMERA · OCT 2020"), credit=C_GSFC,
                                                   chips=[(V(W_("was placed into the return")), "HEAD STOWED IN THE RETURN CAPSULE", 960, 120, 38, None)])),
    S(W_("And on October 28,"), "clip", **clip("M09", 19.6, 23.8, fit="fit", region=M09_REG, label=("real", "SPACECRAFT CAMERA · OCT 2020"), credit=C_GSFC,
                                              chips=[(V(W_("And on October 28,")) + 0.3, "OCTOBER 28, 2020 · CAPSULE CLOSED", 960, 120, 42, "y")])),
    # ---- HOME
    S(W_("The spacecraft itself never"), "release"),
    S(W_("It reached Earth on"), "clip", **clip("M11", 21.0, 24.8, region=M11_REG, zoom=(1.7, 1.8),
                                               track=[(21.0, 712, 400), (22.5, 686, 346), (23.5, 588, 315), (24.5, 566, 305), (25.0, 540, 318)],
                                               label=("video", "CAPSULE ON THE GROUND"), credit=C_GSFC,
                                               chips=[(V(W_("It reached Earth on")) + 0.3, "SEPTEMBER 24, 2023", 960, 120, 50, "y")])),
    S(W_("Inside, NASA measured"), "mass", t_oz=V(W_("That's about four ounces.")), t_min=V(W_("The mission needed")),
      t_twice=V(W_("It brought back about twice"))),
    S(W_("And the sample delivered."), "chem", t_jan=V(W_("In January 2025,")), t_nuc=V(W_("plus five nucleobases.")),
      t_dec=V(W_("In December 2025,")), t_not=V(W_("None of this is evidence")), t_noorg=V(W_("No organisms,")),
      t_ingr=V(W_("These are chemical ingredients."))),
    # ---- CLOSE
    S(W_("And it all came from one"), "clip", **clip("M04", 11.6, 22.0, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL, hud="replay",
                                                    zoom=(1.0, 1.1), fc=(1000, 640),
                                                    chips=[(V(W_("on a surface so loose")), "A LOOSE, WEAKLY BOUND SURFACE", 960, 120, 42, "y")])),
    S(W_("On an asteroid like Bennu,"), "clip", **clip("M04", 58.0, 68.4, label=("anim", "DATA-DRIVEN RECONSTRUCTION"), credit=C_CIL)),
    dict(t0=V(NDUR) + 0.35, kind="end"),
]

for i, s in enumerate(SHOTS):
    s["t1"] = SHOTS[i + 1]["t0"] if i + 1 < len(SHOTS) else END
    assert s["t1"] > s["t0"], (i, s)
