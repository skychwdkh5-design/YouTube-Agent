#!/usr/bin/env python3
"""Render a scene range with sub-frame motion blur.  python3 render_v4.py ground out.mp4 t0 t1 nsub [shutter]"""
import sys, subprocess, time
import numpy as np
import engine as E
name, out, t0, t1, n = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
shutter = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
mod = __import__(name + "_v4"); scene = mod.scene
VIG = E.vignette_map(0.30)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30", out], stdin=subprocess.PIPE)
f0, f1 = round(t0 * 30), round(t1 * 30); T = time.time()
for i in range(f0, f1):
    c = E.render_frame(scene, i / 30.0, n, shutter)
    p.stdin.write(E.finish(c, i, VIG).tobytes())
    if (i - f0) % 30 == 0: print(f"{i - f0}/{f1 - f0} {time.time() - T:.0f}s", flush=True)
p.stdin.close(); p.wait()
