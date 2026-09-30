"""The site cut: media/journey_<key>_site.mp4 (and _site_rev.mp4), 60 fps, what the site preview plays at 1x.

Every scroll takes MOVE seconds. Intro → work is the footage as it is; work → the sea covers 11 s of the journey, so it is
compressed here (about 3.5x, easing to 1x over the last EASE seconds, into the loop), instead of asking the browser to play
1080p at 3.5x, which drops frames. Where the journey moves at about 1x each output frame is the nearest source frame; faster,
it averages the source over the output frame's time (a 360-degree shutter), so fast motion blurs instead of skipping.
The site's default pace (SPEED, 1.3x) is baked in too, so the browser always plays it at exactly 1x: every scroll is
MOVE / SPEED seconds long. Must match MOVE, EASE, K, SITE_SPEED in index.html.   usage: make_site_cut.py <sun|moon> [speed=1.3]"""
import json, math, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

JC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = sys.argv[1]; SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.3
K = [0, 3.4, 208 / 30 + 7.614]; MOVE = K[1] - K[0]; EASE = .6; FPS_IN, FPS = 30, 60

def rate_J(tau):   # work → the sea, tau seconds in: journey speed and position (as moveRate / moveJ in the page)
    dJ = K[2] - K[1]; E = EASE; R = (dJ - E / 2) / (MOVE - E / 2); tau = min(max(tau, 0), MOVE)
    if tau <= MOVE - E: return R, K[1] + R * tau
    x = tau - MOVE + E
    return R - (R - 1) * x / E, K[1] + R * (MOVE - E) + R * x - (R - 1) * x * x / (2 * E)

def at(T):         # the site cut at time T: (journey speed, journey time)
    return (1.0, T) if T <= MOVE else rate_J(T - MOVE)

tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), f'site_cut_{key}'); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
src = os.path.join(JC, 'media', f'journey_{key}.mp4')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', src, '-start_number', '0', os.path.join(tmp, 's_%04d.png')], check=True)
NS = len([f for f in os.listdir(tmp) if f.startswith('s_')]); last = NS - 1
N = round(2 * MOVE / SPEED * FPS) + 1
S = lambda n: os.path.join(tmp, f's_{min(max(n, 0), last):04d}.png')
O = lambda k: os.path.join(tmp, f'o_{k:04d}.png')

def weights(a, b):  # box average of the linearly interpolated source over [a, b] (in source frames)
    w = {}
    for n in range(math.floor(a), math.ceil(b)):
        u0, u1 = max(a, n) - n, min(b, n + 1) - n
        if u1 <= u0: continue
        w[n] = w.get(n, 0) + (u1 - u0) - (u1 * u1 - u0 * u0) / 2
        w[n + 1] = w.get(n + 1, 0) + (u1 * u1 - u0 * u0) / 2
    w = {n: v for n, v in w.items() if v > .02 * (b - a)}; s = sum(w.values())
    return {min(max(n, 0), last): v / s for n, v in w.items()}

plan = []
for k in range(N):
    r, J = at(k / FPS * SPEED); p = min(max(J * FPS_IN, 0), last); step = r * SPEED * FPS_IN / FPS   # source frames per output frame
    plan.append((k, {math.floor(p + .5 - 1e-6): 1.0} if step <= .55 else weights(max(0, p - step / 2), min(last, p + step / 2))))

def make(item):
    k, w = item
    if len(w) == 1: os.link(S(next(iter(w))), O(k)); return
    ins = sum((['-i', S(n)] for n in w), [])
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *ins, '-filter_complex', f"mix=inputs={len(w)}:weights='{' '.join(f'{v:.4f}' for v in w.values())}'",
                    '-frames:v', '1', O(k)], check=True)
with ThreadPoolExecutor(6) as ex: list(ex.map(make, plan))
blended = sum(1 for _, w in plan if len(w) > 1)

enc = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-g', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an']
out = os.path.join(JC, 'media', f'journey_{key}_site.mp4')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tmp, 'o_%04d.png'), *enc, out], check=True)
for k in range(N): os.link(O(N - 1 - k), os.path.join(tmp, f'r_{k:04d}.png'))     # going back up: the same frames, reversed
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tmp, 'r_%04d.png'), *enc,
                os.path.join(JC, 'media', f'journey_{key}_site_rev.mp4')], check=True)
fr = os.path.join(JC, 'frames', f'journey_{key}_site'); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)   # stills for exports
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', out, '-q:v', '3', os.path.join(fr, 'f_%04d.jpg')], check=True)
mp = os.path.join(JC, 'media', 'meta.json'); m = json.load(open(mp)); m[f'journey_{key}_site'] = {'fps': FPS, 'n': N, 'speed': SPEED}
json.dump(m, open(mp, 'w'), indent=1, sort_keys=True)
shutil.rmtree(tmp)
print(f'journey_{key}_site: {N} frames at {FPS} fps ({blended} blended), {os.path.getsize(out) / 1e6:.1f} MB; source {NS} frames')
