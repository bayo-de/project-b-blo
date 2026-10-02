#!/usr/bin/env python3
"""Biblo lofi engine v1 — original generative lofi hip-hop loop.

Fully synthesized in code (numpy): Rhodes-style electric piano, swung
boom-bap drums, sub bass, vinyl texture. Every note is composed here, so
the output is original by construction — no samples, no rights issues.

Progression: Dm9 - G13 - Cmaj9 - Am9 (ii - V - I - vi in C), 8 bars @ 76 BPM.
Usage: python3 lofi_loop_v3.py  ->  biblo-lofi-loop-v4.wav (seamless loop)
"""
import numpy as np

SR = 44100
BPM = 76
BEAT = 60.0 / BPM
STEP = BEAT / 4          # 16th note
N_BARS = 8
N_STEPS = N_BARS * 16
SWING = 0.32             # MPC-style: odd 16ths pushed late (fraction of STEP)
TOTAL = N_BARS * 4 * BEAT
N = int(TOTAL * SR)

rng = np.random.default_rng(20261001)

def lowpass_fft(x, cutoff, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    H = 1.0 / (1.0 + (f / cutoff) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def fftconvolve(a, b):
    n = 1
    while n < len(a) + len(b) - 1:
        n *= 2
    return np.fft.irfft(np.fft.rfft(a, n) * np.fft.rfft(b, n),
                        n)[: len(a) + len(b) - 1]


def pad_chord(freqs, dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = min(1.4, dur * 0.35)
    env = np.minimum(1.0, t / a) * np.minimum(1.0, (dur - t) / a)
    sig = np.zeros(n)
    for f in freqs:
        sig += (np.sin(2 * np.pi * f * t)
                + 0.6 * np.sin(2 * np.pi * f * 1.0035 * t)
                + 0.25 * np.sin(2 * np.pi * f * 2.002 * t))
    sig = lowpass_fft(sig, 1400)
    return vel * 0.035 * env * sig / max(1, len(freqs))


def embrace(freqs, dur, vel=1.0):
    """Warm enveloping swell: slow bloom, sub warmth, soft top. The hug."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = min(2.0, dur * 0.4)
    env = np.minimum(1.0, t / a) ** 0.7 * np.minimum(1.0, (dur - t) / a) ** 0.7
    sig = np.zeros(n)
    for f in freqs:
        sig += (np.sin(2 * np.pi * f * t)
                + 0.5 * np.sin(2 * np.pi * f * 1.002 * t)
                + 0.30 * np.sin(2 * np.pi * 0.5 * f * t))
    sig = lowpass_fft(sig, 900)
    return vel * 0.05 * env * sig / max(1, len(freqs))


def shimmer(freq, dur=6.5, vel=1.0):
    """Distant light: soft high sine with slow breathing tremolo."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 0.55) * np.minimum(1.0, t / 2.2)
    trem = 1.0 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * t + 0.5))
    return vel * 0.10 * env * trem * np.sin(2 * np.pi * freq * t)


def sub_drone(freq, dur, vel=1.0):
    """Grounding: felt more than heard."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = min(2.0, dur * 0.3)
    env = np.minimum(1.0, t / a) * np.minimum(1.0, (dur - t) / a)
    return vel * 0.15 * env * np.sin(2 * np.pi * freq * t)




def midi(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def place(sig, sound, at_sec):
    i = int(at_sec * SR)
    j = min(i + len(sound), N)
    if i < N:
        sig[i:j] += sound[: j - i]


def step_time(step):
    """Seconds for a 16th-step index, with swing on odd 16ths."""
    bar_step = step % 16
    t = (step // 16) * 4 * BEAT + (bar_step // 2) * 2 * STEP
    if bar_step % 2 == 1:
        t += STEP * (1.0 + SWING)
    return t


# ---- voices ----
def rhodes_note(freq, dur=2.2, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 0.85) * np.minimum(1.0, t * 40.0)
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.32 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 2.5)
           + 0.10 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t * 4.0))
    trem = 1.0 - 0.20 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.6 * t + 1.0))
    # gentle chorus detune
    sig += 0.15 * np.sin(2 * np.pi * freq * 1.003 * t) * env
    return vel * 0.5 * env * trem * sig


def kick():
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    f = 45 + 120 * np.exp(-t * 30)
    ph = np.cumsum(2 * np.pi * f / SR)
    atk = np.minimum(1.0, t / 0.003)
    return 0.8 * np.sin(ph) * np.exp(-t * 9) * atk


def snare():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # crude bandpass around 1.8kHz via difference of smoothed versions
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    atk = np.minimum(1.0, t / 0.003)
    return 0.42 * (noise * np.exp(-t * 40) * 0.5 + tone * 0.6) * atk


def hat(open_=False):
    dur = 0.30 if open_ else 0.045
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    hp = noise - np.convolve(noise, np.ones(24) / 24, mode="same")  # crude highpass
    atk = np.minimum(1.0, t / 0.002)
    s = 0.17 * hp * np.exp(-t * (8 if open_ else 90)) * atk
    return lowpass_fft(s, 6000)


def bass_note(freq, dur=0.9, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.0) * np.minimum(1.0, t * 60.0)
    sig = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
    return vel * 0.42 * env * sig


# ---- composition ----
# chord per 2-bar block: (name, voicing midi, bass root midi)
PROG = [
    ("Dm9",   [53, 57, 60, 64], 38),
    ("G13",   [53, 59, 64],      43),
    ("Cmaj9", [52, 59, 62],      36),
    ("Am9",   [55, 60, 64],      33),
]

mix = np.zeros(N)
verb = np.zeros(N)

for bar in range(N_BARS):
    name, chord, root = PROG[bar // 2]
    base = bar * 16
    if bar % 2 == 0:
        place(verb, pad_chord([midi(m) for m in chord[:4]],
                              dur=2 * 4 * BEAT, vel=0.20),
              step_time(base))
        place(verb, embrace([midi(m) for m in chord[:3]],
                            dur=2 * 4 * BEAT, vel=0.55),
              step_time(base))
        place(mix, sub_drone(midi(root - 12), dur=2 * 4 * BEAT, vel=0.8),
              step_time(base))
        place(verb, shimmer(midi(chord[-1] + 12), vel=0.55),
              step_time(base + 4))
        place(verb, shimmer(midi(chord[-2] + 12), vel=0.45),
              step_time(base + 12))
    # Rhodes stabs: downbeat + swung 'and of 2', extra anticipation every 4th bar
    for s, vel in ((0, 0.95), (7, 0.62)):
        t = step_time(base + s)
        for m in chord:
            v = vel * rng.uniform(0.85, 1.0)
            place(mix, rhodes_note(midi(m), dur=4.5, vel=v), t)
            place(verb, rhodes_note(midi(m), dur=4.5, vel=v * 0.8), t)
    if bar % 4 == 3:
        t = step_time(base + 10)
        for m in chord[:3]:
            place(mix, rhodes_note(midi(m), dur=3.5, vel=0.5), t)
            place(verb, rhodes_note(midi(m), dur=3.5, vel=0.4), t)
    # bass: root on 1, syncopated fifth/octave on the 'and of 3'
    place(mix, bass_note(midi(root), vel=0.9), step_time(base + 0))
    place(mix, bass_note(midi(root + 7), dur=0.5, vel=0.55), step_time(base + 11))
    # drums: boom-bap
    for s in (0, 7, 10):
        place(mix, kick(), step_time(base + s))
    for s in (4, 12):
        place(mix, snare(), step_time(base + s))
    for i, s in enumerate(range(0, 16, 4)):
        place(mix, hat() * (1.0 if i % 2 == 0 else 0.6), step_time(base + s))
    if bar % 2 == 1:
        place(mix, hat(open_=True) * 0.8, step_time(base + 14))
    # sparse top-line: chord tones an octave up, bars 1,3,5,7
    if bar % 2 == 1:
        top = [m + 12 for m in chord]
        motif = [top[2], top[1]] if len(top) > 2 else top[:2]
        for k, (s, m_) in enumerate(zip((2, 9), motif)):
            place(mix, rhodes_note(midi(m_), dur=1.8,
                                   vel=0.42 * (1 - 0.15 * k)),
                  step_time(base + s))
            place(verb, rhodes_note(midi(m_), dur=1.8,
                                    vel=0.34 * (1 - 0.15 * k)),
                  step_time(base + s))

# ---- gentle room: short convolution reverb, tail wrapped (seamless) ----
_ir_n = int(1.6 * SR)
_ir_t = np.arange(_ir_n) / SR
_ir = np.zeros(_ir_n)
for _k in range(10):
    _f = rng.uniform(180, 2400)
    _d = rng.uniform(1.6, 3.0)
    _p = rng.uniform(0, 2 * np.pi)
    _ir += rng.uniform(0.4, 1.0) * np.sin(2 * np.pi * _f * _ir_t + _p) * np.exp(-_ir_t * _d)
_ir = lowpass_fft(_ir, 2800)
_ir *= np.minimum(1.0, _ir_t / 0.01)
_ir /= max(1e-9, np.sqrt((_ir ** 2).sum()))  # unit energy: no level jump
_conv = fftconvolve(verb, _ir)
_tail = _conv[N:]
_room = _conv[:N].copy()
_room[: len(_tail)] += _tail
_hd = int(0.012 * SR)  # Haas delay: width without phase risk
_room_r = np.concatenate([np.zeros(_hd), _room])[:N]
mix = np.stack([mix + _room * 0.15, mix + _room_r * 0.15])

# ---- tape: whisper of hiss only. NO pops, NO crackle ----
t_all = np.arange(N) / SR
wow = 1.0 + 0.018 * np.sin(2 * np.pi * 0.55 * t_all)
mix = np.stack([mix[0] * wow, mix[1] * wow])
_hiss = rng.standard_normal((2, N)) * 0.0016
_hiss = np.stack([np.convolve(_hiss[c], np.ones(48) / 48, mode="same") for c in range(2)])
mix += _hiss

# ---- master: lofi muffle + straight normalize. NO saturation ----
mix = np.stack([lowpass_fft(mix[c], 8000) for c in range(2)])
mix /= max(1e-9, np.abs(mix).max() / 0.89)

import wave
_st = np.stack([(mix[c] * 32767).astype(np.int16) for c in range(2)], axis=1)
with wave.open("biblo-lofi-loop-v6.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(_st.tobytes())
print(f"wrote biblo-lofi-loop-v6.wav ({TOTAL:.1f}s, {BPM} BPM, seamless {N_BARS}-bar loop)")
