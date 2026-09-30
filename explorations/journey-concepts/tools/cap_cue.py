"""Paint the top of the sun or the moon rising out of the middle of NASA's band of light over the last frames before the
handoff, so the extension that continues this footage carries a solid disc up instead of NASA's thin arch.
usage: cap_cue.py <moon|sun> <out.mp4>   → bh-journey frames 0–207 at 960x540, frames 190–207 painted"""
import math, subprocess, sys

JC = '/Users/jordanmoreno/Desktop/Personal-Website/explorations/journey-concepts'
key, out = sys.argv[1], sys.argv[2]
W, H, CX = 960, 540, 480
R = 163                        # the disc's radius (px at 960x540): NASA's arch is ~0.3 W across at its widest
P0, P1 = 190, 207              # painted frames: the disc's top rises from the band, easing in to about NASA's arch speed
H_END = 30.0                   # how far its top stands above the band at the handoff (px)

def frames(path, w, h, vf=''):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-vf', f'scale={w}:{h}{vf}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = w * h * 3; return [bytearray(raw[i:i + n]) for i in range(0, len(raw) - n + 1, n)]

src = frames(f'{JC}/bh-journey.mp4', W, H, f",select='lte(n\\,{P1})'")
D = 2 * R
if key == 'moon':
    tex = frames(f'{JC}/media/moon.jpg', D, D)[0]
    def face(tx, ty):
        i = (min(D - 1, max(0, ty)) * D + min(D - 1, max(0, tx))) * 3
        return [min(255, tex[i + c] * 1.18 + 14) for c in range(3)]
    GLOW, GS, GF = (235, 238, 245), 70, 5
else:
    def face(tx, ty):            # yellow at the top, through orange, to hot pink at the base
        u = ty / D; stops = [(0, (255, 246, 170)), (.35, (255, 206, 80)), (.7, (255, 128, 70)), (1, (240, 70, 120))]
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if u <= b: t = (u - a) / (b - a); return [ca[c] + (cb[c] - ca[c]) * t for c in range(3)]
        return list(stops[-1][1])
    GLOW, GS, GF = (255, 196, 110), 130, 10

def lum(f, x, y): i = (y * W + x) * 3; return .2126 * f[i] + .7152 * f[i + 1] + .0722 * f[i + 2]

for k in range(P0, P1 + 1):
    f = src[k]
    M = int(5 * GF) + 2; x0, x1 = CX - R - M, CX + R + M      # room for the glow to fall off
    edge = {}; last = int(H * .45)
    for x in range(x0, x1 + 1):                      # the band's top edge in each column
        e = next((y for y in range(int(H * .28), int(H * .62)) if lum(f, x, y) > 170), last); edge[x] = last = e
    sm = {}
    for x in edge:                                   # median over 9 columns
        win = sorted(edge[j] for j in range(max(x0, x - 4), min(x1, x + 4) + 1)); sm[x] = win[len(win) // 2]
    base = sorted(sm[x] for x in range(CX - 10, CX + 11))[10]
    h = H_END * ((k - P0 + 1) / (P1 - P0 + 1)) ** 2
    cy = base - h + R
    for y in range(int(base - h) - M, base + 3):
        for x in range(x0, x1 + 1):
            if y < 0: continue
            d = math.hypot(x - CX, y - cy)
            above = min(1., max(0., sm[x] - y + .5))            # only above the band: it comes up from behind the light
            if above <= 0: continue
            i = (y * W + x) * 3
            cov = min(1., max(0., R + .5 - d)) * above
            glow = GS * math.exp(-max(0., d - R) / GF) * above * (1 - cov)
            col = face(x - (CX - R), y - int(cy - R)) if cov > 0 else (0, 0, 0)
            for c in range(3):
                f[i + c] = int(min(255, f[i + c] * (1 - cov) + col[c] * cov + glow * GLOW[c] / 255))

p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for f in src: p.stdin.write(f)
p.stdin.close(); p.wait()
print(f'{out}: {len(src)} frames, frames {P0}–{P1} painted ({key})')
