"""Top edge of the band of light in the middle columns (first row brighter than 150 from above), per frame.
usage: arch_top.py <video> <first frame> <count> <fps>"""
import subprocess, sys
W, H = 480, 270
path, n0, cnt, fps = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-vf', f"select='between(n\\,{n0}\\,{n0 + cnt - 1})',scale={W}:{H}:flags=area,format=gray",
                      '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'], capture_output=True).stdout
F = W * H
for k in range(len(raw) // F):
    f = raw[k * F:(k + 1) * F]; tops = []
    for x in range(W // 2 - 12, W // 2 + 13, 2):
        for y in range(int(H * .25), int(H * .7)):
            if f[y * W + x] > 150: tops.append(y); break
    tops.sort(); t = tops[len(tops) // 2] / H if tops else float('nan')
    print(f'{(n0 + k) / fps:6.3f} s  top {t:.4f}')
