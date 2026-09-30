"""Trace the ring's band while it is still rising off the line (v = 4.4…4.9 s), before trace_ring.py's window applies.

From the same centre (800, 326.07), the band is the first bright run along each ray. Near the Milky Way inside the ring
(below y = 385) a run must also be brighter than the galaxy (max channel > 232). Rays heading down pass the galaxy's core
just above the dome's base, so for them the band is the last run above y = 528 within the dome's width (the base or a
wall), not the first."""
import subprocess, math, json, sys
W, H = 1600, 900
YMAX, CY, THR = 528, 326.07, 232
def frame(t):
    return subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.4f}', '-i', 'bh-journey.mp4', '-frames:v', '1',
                           '-vf', f'scale={W}:{H}:flags=bicubic', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
def bright(raw, x, y):
    xi, yi = int(x), int(y)
    if xi < 0 or yi < 0 or xi >= W - 1 or yi >= H - 1: return 0
    fx, fy = x - xi, y - yi
    def m(a, b):
        i = (b * W + a) * 3; return max(raw[i], raw[i + 1], raw[i + 2])
    return (m(xi, yi) * (1 - fx) + m(xi + 1, yi) * fx) * (1 - fy) + (m(xi, yi + 1) * (1 - fx) + m(xi + 1, yi + 1) * fx) * fy
ANG = list(range(0, 360, 10)); VS = [4.4, 4.5, 4.6, 4.7, 4.8, 4.9]
out = {'v': VS, 'ang': ANG, 'cy': [], 'rin': [], 'rout': []}
for v in VS:
    raw = frame(3.4 + v); rin, rout = [], []; hw = 400
    for a in ANG:
        th = math.radians(a); dx, dy = math.cos(th), math.sin(th); r = 20.; runs = []
        while r < 600:
            x, y = 800 + dx * r, CY + dy * r
            if y >= YMAX or not (0 <= x < W) or y < 0: break
            if bright(raw, x, y) > (THR if y > 385 else 140):
                if runs and r - runs[-1][1] <= 5: runs[-1][1] = r
                else: runs.append([r, r])
            elif not (dy > .3) and runs and r - runs[-1][1] > 5: break
            r += .5
        if dy > .3:   # the last crossing still inside the dome's width (beyond it are NASA's horizon arcs)
            inside = [q for q in runs if abs(dx * q[0]) <= hw + 30]
            run = inside[-1] if inside else (runs[0] if runs else [599, 600])
        else: run = runs[0] if runs else [599, 600]
        if a == 0: hw = run[0]
        rin.append(round(run[0], 1)); rout.append(round(run[1], 1))
    out['cy'].append(CY); out['rin'].append(rin); out['rout'].append(rout)
    print(v, 'top', rin[27], 'right', rin[0], '40°', rin[4], '50°', rin[5], '60°', rin[6], '90°', rin[9], '130°', rin[13], file=sys.stderr)
json.dump(out, open(sys.argv[1], 'w'))
