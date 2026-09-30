"""Trace the lensed ring's band on bh-journey.mp4: inner/outer radius per angle, per frame.

Rays start at the ring's centre (the page's RCY table) and search a window around the
ellipse measured earlier (RXO/RYO), so NASA's horizon arcs below the ring are ignored.
The ring's base merges into the horizon line; there the band is capped just above it."""
import subprocess, math, json, sys
W, H = 1600, 900
YLINE = 509
RV = [5.4, 5.8, 6.1, 6.4, 6.7, 7.0]
RCY = [.3623, .3447, .3327, .3234, .3132, .303]
RXO = [.14115, .1453, .1495, .15315, .1568, .1602]
RYO = [.2197, .2373, .24935, .2586, .2688, .279]
def pchip(xs, ys, x):
    n = len(xs)
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    h = [xs[i+1]-xs[i] for i in range(n-1)]; d = [(ys[i+1]-ys[i])/h[i] for i in range(n-1)]
    m = [0]*n; m[0] = d[0]; m[-1] = d[-1]
    for i in range(1, n-1):
        if d[i-1]*d[i] <= 0: m[i] = 0
        else:
            w1 = 2*h[i]+h[i-1]; w2 = h[i]+2*h[i-1]; m[i] = (w1+w2)/(w1/d[i-1]+w2/d[i])
    i = 0
    while i < n-2 and x > xs[i+1]: i += 1
    t = (x-xs[i])/h[i]
    return (2*t**3-3*t**2+1)*ys[i]+(t**3-2*t**2+t)*h[i]*m[i]+(-2*t**3+3*t**2)*ys[i+1]+(t**3-t**2)*h[i]*m[i+1]
def frame(t):
    return subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.4f}', '-i', 'bh-journey.mp4', '-frames:v', '1',
                           '-vf', f'scale={W}:{H}:flags=bicubic', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
def bright(raw, x, y):
    xi, yi = int(x), int(y)
    if xi < 0 or yi < 0 or xi >= W-1 or yi >= H-1: return 0
    fx, fy = x-xi, y-yi
    def m(a, b):
        i = (b*W+a)*3; return max(raw[i], raw[i+1], raw[i+2])
    return (m(xi, yi)*(1-fx)+m(xi+1, yi)*fx)*(1-fy)+(m(xi, yi+1)*(1-fx)+m(xi+1, yi+1)*fx)*fy
ANG = list(range(0, 360, 10))
VS = [round(5.0+0.1*i, 1) for i in range(21)]
out = {'v': VS, 'ang': ANG, 'cy': [], 'rin': [], 'rout': []}
for v in VS:
    raw = frame(3.4+v); cx = 800.0; cy = pchip(RV, RCY, v)*H
    rxo = pchip(RV, RXO, v)*W; ryo = pchip(RV, RYO, v)*H
    rin, rout = [], []
    for a in ANG:
        th = math.radians(a); dx, dy = math.cos(th), math.sin(th)
        re = 1/math.sqrt(dx*dx/rxo**2 + dy*dy/ryo**2)
        lo, hi = re-70, re+28
        prof = []; r = lo; guard = None
        while r < hi:
            x, y = cx+dx*r, cy+dy*r
            if y >= YLINE: guard = r; break
            prof.append((r, bright(raw, x, y))); r += .5
        peak = max((b for _, b in prof), default=0)
        thr = max(60, .3*peak)
        runs = []
        for rr, b in prof:
            if b > thr:
                if runs and rr-runs[-1][1] <= 1.01: runs[-1][1] = rr
                else: runs.append([rr, rr])
        merged = []
        for a0, a1 in runs:                       # strands of one band are separated by thin gaps
            if merged and a0-merged[-1][1] < 5: merged[-1][1] = a1
            else: merged.append([a0, a1])
        if guard is not None:
            if not merged or guard-merged[-1][1] > 6: merged.append([guard-3, guard])
        band = max(merged, key=lambda q: q[1]) if merged else [re-4, re]
        rin.append(round(band[0], 1)); rout.append(round(band[1], 1))
    out['cy'].append(round(cy, 2)); out['rin'].append(rin); out['rout'].append(rout)
json.dump(out, open(sys.argv[1], 'w'))
