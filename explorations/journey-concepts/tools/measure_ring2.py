import subprocess, math
W, H = 1600, 900
def frame(t):
    return subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i','bh-journey.mp4','-frames:v','1','-vf',f'scale={W}:{H}:flags=bicubic','-f','rawvideo','-pix_fmt','rgb24','-'], capture_output=True).stdout
def px(raw, x, y):
    x = max(0, min(W-1, int(round(x)))); y = max(0, min(H-1, int(round(y))))
    i = (y*W + x)*3; return raw[i], raw[i+1], raw[i+2]
# pchip-free: use the page's measured table for the centre
RV=[5.4,5.8,6.1,6.4,6.7,7.0]; RCY=[.3623,.3447,.3327,.3234,.3132,.303]
def lin(xs, ys, x):
    if x <= xs[0]: return ys[0]
    for i in range(len(xs)-1):
        if x <= xs[i+1]: t=(x-xs[i])/(xs[i+1]-xs[i]); return ys[i]+(ys[i+1]-ys[i])*t
    return ys[-1]
for v in [5.4, 5.8, 6.0, 6.4, 7.0]:
    raw = frame(3.4+v); cx = 800; cy = lin(RV, RCY, v)*H
    out = []
    for deg in [-90, -60, -30, 0, 30, 50, 65, 75, 85]:
        th = math.radians(deg)
        # scan outward from r=120 to 330 along direction (−cos, sin) i.e. left half, deg -90 = up
        dx, dy = -math.cos(th), math.sin(th)
        prof = []
        for r10 in range(1200, 3400, 5):
            r = r10/10; c = px(raw, cx + dx*r, cy + dy*r); prof.append((r, max(c), c))
        on = [p for p in prof if p[1] > 110]
        if not on: out.append(f"{deg}:none"); continue
        # outermost run end and first entry
        rin = on[0][0]; rout = on[-1][0]
        # skip galaxy glow: find runs
        runs=[]; 
        for p in on:
            if runs and abs(p[0]-runs[-1][1]) <= .6: runs[-1][1]=p[0]
            else: runs.append([p[0],p[0]])
        out.append(f"{deg}:" + ",".join(f"{a:.0f}-{b:.0f}" for a,b in runs))
    print(f"v={v} cy={cy:.1f} | " + " | ".join(out))
