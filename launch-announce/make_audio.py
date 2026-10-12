import numpy as np
import subprocess

SR = 44100
FPS = 24
DUR = 780 / FPS  # 32.5s
t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)

def env(sig, attack, decay, start_t):
    e = np.zeros_like(t)
    i0 = int(start_t * SR)
    ia = int(attack * SR)
    idc = int(decay * SR)
    n = min(len(sig), len(t) - i0)
    if n <= 0: return e
    seg = sig[:n].copy()
    if ia > 0: seg[:min(ia, n)] *= np.linspace(0, 1, min(ia, n))
    if idc > 0: seg[max(0, n - idc):] *= np.linspace(1, 0, n - max(0, n - idc))
    e[i0:i0 + n] = seg
    return e

# quiet ambient pad: warm triad, slow tremolo
pad = (np.sin(2*np.pi*220*t) * 0.5 + np.sin(2*np.pi*277.18*t) * 0.28 + np.sin(2*np.pi*329.63*t) * 0.22)
pad *= (1 + 0.35*np.sin(2*np.pi*0.6*t)) * 0.05
pad *= np.minimum(1, t/2.0) * np.minimum(1, (DUR-t)/2.5)

# soft tick on each pick frame (subtle UI "select")
def tick(f):
    tt = np.linspace(0, 0.09, int(SR*0.09), endpoint=False)
    s = np.sin(2*np.pi*1320*tt) * np.exp(-tt*45) + np.sin(2*np.pi*1980*tt)*0.3*np.exp(-tt*60)
    return env(s, 0.004, 0.08, f/FPS) * 0.35

# soft swell at save (f539) — rising chime
def swell(f):
    tt = np.linspace(0, 1.6, int(SR*1.6), endpoint=False)
    s = (np.sin(2*np.pi*523.25*tt)*0.5 + np.sin(2*np.pi*659.25*tt)*0.35 + np.sin(2*np.pi*783.99*tt)*0.3)
    s *= np.exp(-tt*1.8) * np.minimum(1, tt/0.15)
    return env(s, 0.1, 1.2, f/FPS) * 0.5

# gentle whoosh on walk-in (f1-70) and turn (f695)
def whoosh(f0, f1):
    i0, i1 = int(f0/FPS*SR), int(f1/FPS*SR)
    n = i1 - i0
    noise = np.random.RandomState(7).randn(n)
    k = np.ones(80)/80
    s = np.convolve(noise, k)[:n] * 0.12
    e = np.zeros_like(t); e[i0:i1] = s * np.sin(np.pi*np.linspace(0,1,n))**2
    return e

mix = pad + whoosh(1,70) + whoosh(695,760)
for f in (205, 339, 436):
    mix += tick(f)
mix += swell(539)

mix = np.clip(mix, -0.95, 0.95)
pcm = (mix * 32767).astype(np.int16)
pcm.tofile('/home/ubuntu/work/launch/audio_raw.pcm')
subprocess.run(['ffmpeg','-y','-f','s16le','-ar','44100','-ac','1','-i','/home/ubuntu/work/launch/audio_raw.pcm','/home/ubuntu/work/launch/audio.wav'], check=True, capture_output=True)
print('audio.wav', DUR)
