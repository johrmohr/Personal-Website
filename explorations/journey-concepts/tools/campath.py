"""Camera path through NASA SVS 14576's 360-degree plunge render.

Source time (s) -> pitch (deg, positive looks up) and horizontal field of view.
After 44.5 s the pitch is solved so the straight line of lensed light sits at 58.1% of frame height.
"""
import math

SRC = '/Users/jordanmoreno/Desktop/Personal-Website/explorations/nasa-source/14576_BH_Plunge_Rectilinear_4096x2048_60.mp4'
KEYS = [(2.0, 0.0, 100), (10, 0.5, 100), (20, 1.5, 99), (28, 2.5, 98.5), (31.6, 3, 98), (34, 4, 98), (36, 7, 97),
        (38, 12, 96), (40, 20, 95), (41.5, 27, 94), (43, 34.5, 93), (44.5, 44.2, 92), (46, 52.8, 90), (47.5, 61.2, 89),
        (49, 68.3, 88), (50.5, 74.1, 87), (52, 78.7, 86), (53.5, 82.4, 85), (55, 84.9, 84), (56.5, 87.1, 84), (57.5, 88.0, 84)]


def pchip(xs, ys, x):
    n = len(xs)
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = max(j for j in range(n - 1) if xs[j] <= x)
    t = (x - xs[i]) / h[i]
    h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


def cam(t):
    xs = [k[0] for k in KEYS]
    p = pchip(xs, [k[1] for k in KEYS], t)
    hf = pchip(xs, [k[2] for k in KEYS], t)
    vf = 2 * math.degrees(math.atan(math.tan(math.radians(hf / 2)) * 9 / 16))
    return p, hf, vf


def v360(t, w, h):
    p, hf, vf = cam(t)
    return f'v360@cam=e:flat:yaw=0:pitch={p:.4f}:roll=0:h_fov={hf:.4f}:v_fov={vf:.4f}:w={w}:h={h}:interp=cubic'
