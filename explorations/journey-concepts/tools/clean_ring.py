"""Symmetrize (the ring is mirror-symmetric about the frame's centre line), then smooth in angle and time."""
import json, sys
d = json.load(open(sys.argv[1])); A = d['ang']; n = len(A)
idx = {a: i for i, a in enumerate(A)}
rin = [row[:] for row in d['rin']]; rout = [row[:] for row in d['rout']]
for k in range(len(d['v'])):
    R = d['rin'][k]
    for i, a in enumerate(A):
        j = idx[(180 - a) % 360]
        # keep the side that agrees with its neighbours: a stray hit is either a galaxy spot inside the ring or an arc outside it
        nb = (R[(i - 1) % n] + R[(i + 1) % n] + R[(j - 1) % n] + R[(j + 1) % n]) / 4
        src = i if abs(R[i] - nb) <= abs(R[j] - nb) else j
        rin[k][i], rout[k][i] = d['rin'][k][src], d['rout'][k][src]
def sm_ang(row):
    return [round((row[(i-1) % n] + 2*row[i] + row[(i+1) % n]) / 4, 1) for i in range(n)]
def sm_time(tab):
    T = len(tab); out = []
    for k in range(T):
        a, b = max(0, k-1), min(T-1, k+1)
        out.append([round((tab[a][i] + 2*tab[k][i] + tab[b][i]) / 4, 1) for i in range(n)])
    return out
rin = sm_time([sm_ang(r) for r in rin]); rout = sm_time([sm_ang(r) for r in rout])
# the base sits on the line: never let the band dip below it (the early dome's base is traced directly)
CAP_FROM = float(sys.argv[3]) if len(sys.argv) > 3 else -1
for k in range(len(d['v'])):
    if d['v'][k] < CAP_FROM: continue
    cy = d['cy'][k]
    for i, a in enumerate(A):
        import math
        s = math.sin(math.radians(a))
        if s > 0:
            cap = (509 - cy) / s
            rout[k][i] = min(rout[k][i], round(cap, 1)); rin[k][i] = min(rin[k][i], rout[k][i] - 2.5)
d['rin'], d['rout'] = rin, rout
json.dump(d, open(sys.argv[2], 'w'))
for k in (0, 10, 20):
    print('v', d['v'][k], 'rin ', ' '.join(f'{x:4.0f}' for x in rin[k]))
    print('     ', 'rout', ' '.join(f'{x:4.0f}' for x in rout[k]))
