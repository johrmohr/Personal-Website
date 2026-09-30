"""Render NASA's 360-degree plunge along the camera path, then retime it to the site's section timing.

Outputs explorations/journey-concepts/bh-journey.mp4:
  0 .. D12 s              approach: distant hole (NASA 4 s) to the saddle (NASA 31.6 s)
  D12 .. D12 + D_FOOT s   plunge: saddle to the ring rising off the line (NASA 47.7 s)
The page draws the sun from the ring after that, so the footage stops being visible there.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from campath import SRC, cam, pchip  # noqa: E402

WORK = '/Users/jordanmoreno/Desktop/Personal-Website/explorations/nasa-source/work'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bh-journey.mp4')
T0, T1, FPS = 2.0, 48.5, 30
D12 = 3.4
# plunge retime (journey seconds after the saddle -> NASA seconds); must match FOOT_V / FOOT_T in index.html
FOOT_V = [0, 1.2, 3.4, 4.4, 5.6, 6.4, 7.0]
FOOT_T = [31.6, 33.0, 41.0, 44.6, 46.6, 47.3, 47.7]
D_FOOT = FOOT_V[-1]


def render_source():
    os.makedirs(WORK, exist_ok=True)
    cmds = os.path.join(WORK, 'cmds.txt')
    n = int(round((T1 - T0) * FPS))
    prev = cam(T0)[0]
    with open(cmds, 'w') as f:
        for i in range(1, n + 1):
            t = T0 + i / FPS
            p, hf, vf = cam(t)
            dp, prev = p - prev, p  # v360 applies pitch commands incrementally
            f.write(f"{(i - 0.5) / FPS:.5f}-{(i + 0.5) / FPS:.5f} [enter] v360@cam pitch {dp:.6f}, "
                    f"[enter] v360@cam h_fov {hf:.4f}, [enter] v360@cam v_fov {vf:.4f};\n")
    p0, h0, v0 = cam(T0)
    out = os.path.join(WORK, 'plunge_960.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(T0), '-t', str(T1 - T0), '-i', SRC, '-vf',
                    f'fps={FPS},sendcmd=f={cmds},v360@cam=e:flat:yaw=0:pitch={p0}:roll=0:h_fov={h0}:v_fov={v0:.4f}:w=960:h=540:interp=cubic',
                    '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-g', '10', '-pix_fmt', 'yuv420p', out], check=True)
    frames = os.path.join(WORK, 'fr')
    os.makedirs(frames, exist_ok=True)
    for name in os.listdir(frames):
        os.remove(os.path.join(frames, name))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-q:v', '2', os.path.join(frames, '%05d.jpg')], check=True)
    return len(os.listdir(frames))


def build_journey(count):
    def approach(j):
        u = min(1, max(0, j / D12))
        s = u * u * (3 - 2 * u)
        return 4.0 + 27.6 * (0.35 * u + 0.65 * s)

    times = [approach(k / FPS) for k in range(int(round(D12 * FPS)) + 1)]
    times += [pchip(FOOT_V, FOOT_T, k / FPS) for k in range(1, int(round(D_FOOT * FPS)) + 1)]
    lst = os.path.join(WORK, 'journey.txt')
    with open(lst, 'w') as f:
        for t in times:
            n = min(count - 1, max(0, int(round((t - T0) * FPS))))
            f.write(f"file '{os.path.join(WORK, 'fr', f'{n + 1:05d}.jpg')}'\nduration {1 / FPS:.6f}\n")
        f.write(f"file '{os.path.join(WORK, 'fr', f'{n + 1:05d}.jpg')}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-vf', f'fps={FPS},format=yuv420p',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-g', '5', '-movflags', '+faststart', '-an', OUT], check=True)
    return len(times)


if __name__ == '__main__':
    count = render_source() if '--skip-render' not in sys.argv else len(os.listdir(os.path.join(WORK, 'fr')))
    print('source frames', count, 'journey frames', build_journey(count), '->', OUT)
