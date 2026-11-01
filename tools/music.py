import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

import json, sys
PROJ = json.load(open(sys.argv[1]))
SC = PROJ['scenes']
SR = 44100
TOTAL = sum(x['dur'] for x in SC)
SHIFT = PROJ.get('key', 0)
N = int(SR * TOTAL)
BPM = 120
BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(PROJ.get('seed', 7))
L = np.zeros(N); R = np.zeros(N)


def hz(m): return 440 * 2 ** ((m + SHIFT - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def add(sig, t, gl=1.0, gr=None):
    gr = gl if gr is None else gr
    i = int(t * SR)
    if i >= N: return
    n = min(len(sig), N - i)
    sig = sig.copy(); k = min(len(sig) // 2, int(0.006 * SR))
    sig[-k:] *= np.linspace(1, 0, k); sig[:32] *= np.linspace(0, 1, 32)
    L[i:i + n] += sig[:n] * gl; R[i:i + n] += sig[:n] * gr


def saw(f, d, det=0.0):
    t = np.arange(int(d * SR)) / SR
    return 2 * ((t * f * (1 + det)) % 1) - 1


# --- instruments
def kick():
    d = 0.4; t = np.arange(int(d * SR)) / SR
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.3 * np.exp(-t * 300) * rng.standard_normal(len(t)) * 0.3


def clap():
    d = 0.25; t = np.arange(int(d * SR)) / SR
    n = bp(rng.standard_normal(len(t)), 900, 3500) * np.exp(-t * 18)
    return n * 1.6 + 0.3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)


def hat(open_=False):
    d = 0.25 if open_ else 0.06; t = np.arange(int(d * SR)) / SR
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (12 if open_ else 70))


def pluck(m, d=0.35):
    t = np.arange(int(d * SR)) / SR
    f = hz(m)
    s = saw(f, d) + 0.5 * saw(f, d, 0.004)
    return lp(s, 3200) * np.exp(-t * 9)


def pad(notes, d):
    t = np.arange(int(d * SR)) / SR
    s = sum(saw(hz(m), d, dt) for m in notes for dt in (-0.006, 0.0, 0.006))
    s = lp(s, 1600) / (len(notes) * 3)
    env = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.2)
    return s * env


def bass(m, d):
    t = np.arange(int(d * SR)) / SR
    s = lp(saw(hz(m), d) + np.sin(2 * np.pi * hz(m) / 2 * t) * 0.8, 600)
    return s * np.minimum(1, t / 0.01) * np.exp(-t * 4)


# Am - F - C - G
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
roots = [45, 41, 48, 43]
nbars = int(np.ceil(TOTAL / BAR))
DROP = 2 * BAR  # 4.0 s
END = TOTAL

for b in range(nbars):
    t0 = b * BAR
    ch = chords[b % 4]; rt = roots[b % 4]
    add(pad([n + 12 for n in ch], BAR + 0.15), t0, 0.22, 0.2)
    # arpeggio 16ths
    arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[0] + 24, ch[1] + 12, ch[2] + 12]
    for i in range(16):
        tt = t0 + i * BEAT / 4
        if tt >= END: break
        g = 0.13 if t0 >= DROP else 0.12
        p = pluck(arp[i % 8])
        add(p, tt, g * (0.7 if i % 2 else 1.0), g * (1.0 if i % 2 else 0.7))
        add(p * 0.35, tt + BEAT * 0.75, g * 0.2, g * 0.5)  # delay echo
    if t0 < DROP: continue
    for k in range(4):
        tb = t0 + k * BEAT
        add(kick(), tb, 0.9)
        if k in (1, 3): add(clap(), tb, 0.35, 0.4)
        add(hat(), tb + BEAT / 2, 0.12, 0.16)
        add(hat(), tb + BEAT / 4, 0.05, 0.04)
        add(bass(rt, BEAT / 2), tb + BEAT / 2, 0.5)
        add(bass(rt + 12, BEAT / 4), tb + 3 * BEAT / 4, 0.25)
    if b % 4 == 3: add(hat(True), t0 + 3.5 * BEAT, 0.15)

# sidechain ducking on everything that is not kick: approximate via global envelope
duck = np.ones(N)
t = np.arange(int(0.35 * SR)) / SR
shape = 1 - 0.45 * np.exp(-t * 10) * np.minimum(1, t / 0.006)
tb = DROP
while tb < TOTAL:
    i = int(tb * SR); n = min(len(shape), N - i)
    duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n]); tb += BEAT
L *= duck; R *= duck
# re-add kicks un-ducked lightly for punch
tb = DROP
while tb < TOTAL:
    add(kick(), tb, 0.25); tb += BEAT

# --- SFX
scenes = [x['dur'] for x in SC]
starts = np.cumsum([0] + scenes[:-1])


def whoosh(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n); seg = 512
    for i in range(0, n, seg):
        f = 400 + 5000 * (i / n) ** 1.5
        out[i:i + seg] = bp(x[i:i + seg], f * 0.7, min(f * 1.4, 18000), 1)
    return out * np.sin(np.pi * t / d) ** 2


def ding():
    d = 0.9; t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 6)


def pop():
    d = 0.12; t = np.arange(int(d * SR)) / SR
    f = 900 * np.exp(-t * 20) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)


def riser(d=1.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 2000) * (t / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(200 + 800 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.3
    return x * 0.5 + s


for i, st in enumerate(starts):
    if i > 0: add(whoosh(), st - 0.35, 0.5, 0.5)
    if SC[i]['type'] == 'item':
        add(pop(), st + 0.15, 0.5)
        add(ding(), st + 0.2, 0.18, 0.22)
add(riser(), DROP - 1.5, 0.35)
add(riser(), starts[-1] - 1.4, 0.3)
add(ding(), starts[-1] + 0.15, 0.25)
# alert stab on hook badge
add(pop(), 0.2, 0.5); add(ding(), 0.25, 0.15)

mix = np.stack([L, R], 1)
t = np.arange(N) / SR
fade = np.minimum(1, t / 0.3) * np.minimum(1, (TOTAL - t) / 2.5)
mix *= fade[:, None]
mix = np.tanh(mix * 1.1)
mix /= np.abs(mix).max() / 0.89
wavfile.write(sys.argv[2], SR, (mix * 32767).astype(np.int16))
print('ok', TOTAL)
