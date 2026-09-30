"""Line the extension's last frames up with the resting loop, so the half-second blend between them doesn't slide.

Measures the disc (sun or moon: top edge and widest row) and the horizon (strongest row-to-row change away from the
path of light) in the extension's last frame and in loop frame 12 (where the page picks the loop up), then puts both on
the largest frame they share: the extension eases into a plain push-in over its last 4 s (it reads as its pull-back settling),
and the loop takes the small remaining difference as a fixed reframe onto the same frame.
usage: align_tail.py <ext.mp4> <rawloop.mp4> <brightness threshold> → writes ext_filter.txt and loop_filter.txt
(ffmpeg perspective filters)"""
import math, subprocess, sys

ext, loop, thr = sys.argv[1], sys.argv[2], int(sys.argv[3])
W, H = 1920, 1080

def nframes(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)

def geom(path, n):     # measured at half size (area-averaged: stars and the maria's edges soften), returned at full size
    w, h = W // 2, H // 2
    f = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-vf', f"select='eq(n\\,{n})',scale={w}:{h}:flags=area,format=gray",
                        '-fps_mode', 'passthrough', '-frames:v', '1', '-f', 'rawvideo', '-'], capture_output=True).stdout
    L = lambda x, y: f[y * w + x]
    cols = [x for x in range(10, w - 10, 3) if not (w * .3 < x < w * .7)]
    rows = [sum(L(x, y) for x in cols) / len(cols) for y in range(h)]
    hy = max(range(int(h * .4), int(h * .75)), key=lambda y: abs(rows[y + 2] - rows[y - 2]))
    spans = []                                        # first to last bright pixel per row, clear of the glow on the horizon
    for y in range(0, hy - 10):
        xs = [x for x in range(int(w * .2), int(w * .8)) if L(x, y) > thr]
        if len(xs) > 4: spans.append((y, xs[0], xs[-1]))
    top = spans[0][0]; wy, x0, x1 = max(spans, key=lambda s: s[2] - s[1])
    r = (x1 - x0) / 2
    return (x0 + x1), 2 * (top + r), 2 * r, 2 * hy

NE = nframes(ext)
e, l = geom(ext, NE - 1), geom(loop, 12)
S = (l[2] / e[2],)
S = (S[0], (S[0] + (l[3] - l[1]) / (e[3] - e[1])) / 2)                       # loop vs extension scale: disc size; horizon split
# the loop's view in the extension's pixels, cut to the extension's frame: the largest 16:9 frame inside is what both show
ax, bx = max(0, (0 - l[0]) / S[0] + e[0]), min(W, (W - l[0]) / S[0] + e[0])
ay, by = max(0, (0 - l[1]) / S[1] + e[1]), min(H, (H - l[1]) / S[1] + e[1])
fw = min(bx - ax, (by - ay) * W / H); fh = fw * H / W
fx, fy = (ax + bx - fw) / 2, (ay + by - fh) / 2
z = W / fw
Ke, te = (z, z), (-fx * z, -fy * z)                                              # the extension: a plain push-in
Kl = (z / S[0], z / S[1]); tl = tuple(z * (-(l[i]) / S[i] + e[i] - (fx, fy)[i]) for i in range(2))   # the loop: onto the same frame
print(f'extension end: disc ({e[0]:.0f}, {e[1]:.0f}) r {e[2]:.0f}, horizon {e[3]}; loop: disc ({l[0]:.0f}, {l[1]:.0f}) r {l[2]:.0f}, horizon {l[3]}')
print(f'loop scale {S[0]:.4f} x {S[1]:.4f}; the extension pushes in {z:.4f}, the loop by {Kl[0]:.4f} x {Kl[1]:.4f}')

def corners(K, t, w='1'):
    kx, ky = f'(1+({w})*({K[0] - 1:.6f}))', f'(1+({w})*({K[1] - 1:.6f}))'
    tx, ty = f'(({w})*({t[0]:.4f}))', f'(({w})*({t[1]:.4f}))'
    X = lambda q: f'({q}-{tx})/{kx}'; Y = lambda q: f'({q}-{ty})/{ky}'
    return f"x0='{X(0)}':y0='{Y(0)}':x1='{X(W)}':y1='{Y(0)}':x2='{X(0)}':y2='{Y(H)}':x3='{X(W)}':y3='{Y(H)}'"

N1 = NE - 13; N0 = N1 - 96                                                   # ease in over 4 s, full through the blend
w = f'st(0,clip((in-{N0})/{N1 - N0},0,1));ld(0)*ld(0)*(3-2*ld(0))'
open('ext_filter.txt', 'w').write(f'perspective={corners(Ke, te, w)}:interpolation=cubic:eval=frame')
open('loop_filter.txt', 'w').write(f'perspective={corners(Kl, tl)}:interpolation=cubic')
