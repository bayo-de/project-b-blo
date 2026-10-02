#!/usr/bin/env python3
"""Extend the IG clip (lead-in loop) into its own standalone ambient track.

The 10s clip loops with 2s equal-power crossfades between repetitions, so
the seam never clicks. A slow lowpass sweep (dark -> open -> dark) and
gentle amplitude swells give the repetitions a journey instead of a loop
feeling. Ends with a long fade.

Usage: python3 extend_leadin.py <clip_src> <out_wav> [--minutes 5]
"""
import subprocess
import sys
import wave

import numpy as np

SR = 44100
XF = 2.0        # crossfade seconds between clip repetitions
FADE_OUT = 12.0  # final fade seconds


def load_clip(path, slow=1.0):
    tmp = "/tmp/extend_leadin_src.wav"
    filt = f"atempo={slow}" if slow != 1.0 else "anull"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-i", path, "-ar", str(SR), "-ac", "2",
                    "-filter:a", filt, tmp], check=True)
    with wave.open(tmp, "rb") as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
        return (x.reshape(-1, ch) / 32768.0)


def fft_lowpass(x, cutoff):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    H = 1.0 / (1.0 + (f / cutoff) ** 4)
    return np.fft.irfft(X * H[:, None], len(x), axis=0)


def nature_bed(n, rng):
    """A living place under the music: rain, wind, sparse birds, distant
    thunder. All synthesized, all quiet — environment, not effects."""
    t = np.arange(n) / SR
    bed = np.zeros((n, 2))

    # rain: soft broadband wash with slow breathing
    rain = fft_lowpass(rng.standard_normal((n, 2)), 5200)
    rain_am = (0.72 + 0.28 * np.sin(2 * np.pi * 0.18 * t + 1.0)
               * np.sin(2 * np.pi * 0.043 * t + 0.5))
    bed += rain * rain_am[:, None] * 0.044

    # wind: low, slow, wandering across the stereo field
    wind = fft_lowpass(rng.standard_normal((n, 2)), 320)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * 0.011 * t + 2.0) \
        * np.sin(2 * np.pi * 0.023 * t)
    pan_l = 0.5 + 0.5 * np.sin(2 * np.pi * 0.008 * t + 1.0)
    wind *= swell[:, None]
    wind[:, 0] *= pan_l
    wind[:, 1] *= (1 - pan_l)
    bed += wind * 0.077

    # birds: sparse warbled chirps, never in the first 20s.
    # TUNED: the clip is in G minor — every chirp quantizes to the G minor
    # pentatonic (G Bb C D F) so nothing ever sits out of key.
    penta_midi = [79, 82, 84, 86, 89, 91, 94, 96, 98, 101, 103]
    penta_hz = [440.0 * 2 ** ((m - 69) / 12.0) for m in penta_midi]
    n_birds = 14
    for _ in range(n_birds):
        start = rng.uniform(20, n / SR - 5)
        dur = rng.uniform(0.25, 0.5)
        m = int(dur * SR)
        bt = np.arange(m) / SR
        raw = rng.uniform(1800, 3400)
        f0 = min(penta_hz, key=lambda p: abs(p - raw))
        # gentle warble around the key pitch (stays in tune)
        f = f0 * (1 + 0.10 * np.sin(2 * np.pi * rng.uniform(2, 4) * bt
                                    + rng.uniform(0, 6.28)))
        phase = np.cumsum(2 * np.pi * f / SR)
        env = np.sin(np.pi * bt / dur) ** 2
        chirp = 0.07 * env * np.sin(phase)
        # soft top so it never whines
        chirp = fft_lowpass(chirp[:, None], 4500)[:, 0]
        i = int(start * SR)
        j = min(i + m, n)
        if rng.random() < 0.5:
            bed[i:j, 0] += chirp[: j - i]
        else:
            bed[i:j, 1] += chirp[: j - i]

    # distant thunder: 2 slow low rumbles
    for _ in range(2):
        start = rng.uniform(60, n / SR - 30)
        dur = rng.uniform(9, 14)
        m = int(dur * SR)
        r = fft_lowpass(rng.standard_normal((m, 2)), 120)
        atk = np.minimum(1.0, np.arange(m) / (2.5 * SR)) ** 2
        env = atk * np.exp(-np.arange(m) / (dur * SR * 0.45))
        i = int(start * SR)
        j = min(i + m, n)
        bed[i:j] += (r * env[:, None] * 0.08)[: j - i]

    return bed


def wind_only(n, rng, level=0.077):
    t = np.arange(n) / SR
    wind = fft_lowpass(rng.standard_normal((n, 2)), 320)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * 0.011 * t + 2.0) \
        * np.sin(2 * np.pi * 0.023 * t)
    pan_l = 0.5 + 0.5 * np.sin(2 * np.pi * 0.008 * t + 1.0)
    wind *= swell[:, None]
    wind[:, 0] *= pan_l
    wind[:, 1] *= (1 - pan_l)
    return wind * level


def rain_only(n, rng, level=0.044):
    t = np.arange(n) / SR
    rain = fft_lowpass(rng.standard_normal((n, 2)), 5200)
    rain_am = (0.72 + 0.28 * np.sin(2 * np.pi * 0.18 * t + 1.0)
               * np.sin(2 * np.pi * 0.043 * t + 0.5))
    return rain * rain_am[:, None] * level


def leaves_only(n, rng, count=10, level=0.02):
    bed = np.zeros((n, 2))
    for _ in range(count):
        start = rng.uniform(10, n / SR - 5)
        dur = rng.uniform(0.3, 0.8)
        m = int(dur * SR)
        r = rng.standard_normal(m)
        r = r - np.convolve(r, np.ones(64) / 64, mode="same")
        env = np.sin(np.pi * np.arange(m) / m) ** 2
        i = int(start * SR)
        j = min(i + m, n)
        ch = 0 if rng.random() < 0.5 else 1
        bed[i:j, ch] += level * env[: j - i] * r[: j - i]
    return bed


def crickets_only(n, rng, level=0.010):
    t = np.arange(n) / SR
    bed = np.zeros((n, 2))
    for f_c, ch, ph in ((4300, 0, 0.0), (4720, 1, 2.1)):
        pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 21 * t + ph)) ** 3
        wander = 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + ph)
        bed[:, ch] += level * wander * pulse * np.sin(2 * np.pi * f_c * t)
    return bed


def night_bed(n, rng):
    """Night forest: crickets, a distant owl, wind, leaves. No birds,
    no thunder — this is the night shift."""
    t = np.arange(n) / SR
    bed = np.zeros((n, 2))

    # wind: low, slow, wandering (same recipe as day)
    wind = fft_lowpass(rng.standard_normal((n, 2)), 320)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * 0.011 * t + 2.0) \
        * np.sin(2 * np.pi * 0.023 * t)
    pan_l = 0.5 + 0.5 * np.sin(2 * np.pi * 0.008 * t + 1.0)
    wind *= swell[:, None]
    wind[:, 0] *= pan_l
    wind[:, 1] *= (1 - pan_l)
    bed += wind * 0.077

    # crickets: two trilling voices, left and right, very quiet
    for f_c, ch, ph in ((4300, 0, 0.0), (4720, 1, 2.1)):
        pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 21 * t + ph)) ** 3
        wander = 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + ph)
        bed[:, ch] += 0.010 * wander * pulse * np.sin(2 * np.pi * f_c * t)

    # leaves: sparse rustles
    for _ in range(10):
        start = rng.uniform(10, n / SR - 5)
        dur = rng.uniform(0.3, 0.8)
        m = int(dur * SR)
        r = rng.standard_normal(m)
        # crude highpass: remove the slow stuff
        r = r - np.convolve(r, np.ones(64) / 64, mode="same")
        env = np.sin(np.pi * np.arange(m) / m) ** 2
        i = int(start * SR)
        j = min(i + m, n)
        if rng.random() < 0.5:
            bed[i:j, 0] += 0.02 * env[: j - i] * r[: j - i]
        else:
            bed[i:j, 1] += 0.02 * env[: j - i] * r[: j - i]

    # owl: a distant two-syllable hoot, 3-4 times across the track
    for _ in range(rng.integers(3, 5)):
        start = rng.uniform(30, n / SR - 20)
        syllables = [(rng.uniform(360, 400), 0.45),
                     (rng.uniform(320, 355), 0.60)]
        pos = int(start * SR)
        for f_o, dur in syllables:
            m = int(dur * SR)
            ot = np.arange(m) / SR
            # gentle downward glide + soft vibrato
            f = f_o * (1 - 0.02 * ot / dur) \
                * (1 + 0.008 * np.sin(2 * np.pi * 5 * ot))
            phase = np.cumsum(2 * np.pi * f / SR)
            env = np.minimum(1.0, ot / 0.08) * np.sin(np.pi * ot / dur) ** 0.7
            hoot = 0.035 * env * np.sin(phase)
            j = min(pos + m, n)
            bed[pos:j, 0] += hoot[: j - pos] * 0.7
            bed[pos:j, 1] += hoot[: j - pos] * 0.7
            pos += m + int(0.28 * SR)

    return bed


def v6_drums(n, rng):
    """The infectious pattern: V6's straight boom-bap (kick 1 + and-of-2,
    snare dead on 2 and 4, swung hats), mixed low to complement the tones."""
    from lofi_endless_engine import hat, kick, snare
    BEAT = 60.0 / 76.0
    STEP = BEAT / 4
    SWING = 0.32
    drums = np.zeros((n, 2))

    def step_time(step):
        bar_step = step % 16
        t = (step // 16) * 4 * BEAT + (bar_step // 2) * 2 * STEP
        if bar_step % 2 == 1:
            t += STEP * (1.0 + SWING)
        t += rng.uniform(-0.0035, 0.0015)  # laid-back humanize
        return t

    def place(at_sec, snd):
        i = int(at_sec * SR)
        cut = 0
        if i < 0:          # humanize can push a hit just before zero
            cut = -i
            i = 0
        if i >= n:
            return
        j = min(i + len(snd) - cut, n)
        g = min(1.0, max(0.0, at_sec) / 20.0)  # bloom in over first 20s
        seg = snd[cut: cut + (j - i)] * g
        drums[i:j, 0] += seg
        drums[i:j, 1] += seg

    bar = 0
    while True:
        base = bar * 16
        if step_time(base) * SR >= n:
            break
        for s, v in ((0, 0.95), (7, 0.62), (10, 0.80)):
            place(step_time(base + s),
                  kick(v * 0.32 * rng.uniform(0.9, 1.05)))
        for s in (4, 12):
            place(step_time(base + s),
                  snare(rng, 0.38 * rng.uniform(0.9, 1.05)))
        for i, s in enumerate(range(0, 16, 4)):
            place(step_time(base + s), hat(rng) * (0.5 if i % 2 == 0 else 0.3))
        if bar % 2 == 1:
            place(step_time(base + 14), hat(rng, open_=True) * 0.4)
        bar += 1
    return drums


def main():
    clip_src, out_wav = sys.argv[1], sys.argv[2]
    minutes = 5.0
    nature = "--nature" in sys.argv
    for i, a in enumerate(sys.argv[3:]):
        if a == "--minutes":
            minutes = float(sys.argv[4 + i])

    clip = load_clip(clip_src, slow=0.92 if nature else 1.0)
    target = int(minutes * 60 * SR)
    xf_n = int(XF * SR)

    # tile with equal-power crossfades
    reps = int(np.ceil(target / (len(clip) - xf_n))) + 1
    t = np.linspace(0, np.pi / 2, xf_n)
    g_out, g_in = np.cos(t) ** 2, np.sin(t) ** 2
    out = clip.copy()
    for _ in range(reps - 1):
        tail = out[-xf_n:] * g_out[:, None] + clip[:xf_n] * g_in[:, None]
        out = np.concatenate([out[:-xf_n], tail, clip[xf_n:]])
        if len(out) >= target + SR * 20:
            break
    out = out[:target]

    # slow filter journey: dark -> open -> dark over the whole track.
    # (crossfade between two fixed lowpass versions: fast and click-free)
    dark = fft_lowpass(out, 900)
    # nature version keeps the highs less pronounced
    open_ = fft_lowpass(out, 2800 if nature else 3800)
    tt = np.arange(len(out)) / SR
    k = np.sin(np.pi * tt / (minutes * 60)) ** 1.5
    out = dark * (1 - k)[:, None] + open_ * k[:, None]

    # gentle breathing swells (period ~48s)
    breathe = 1.0 + 0.12 * np.sin(2 * np.pi * tt / 48.0 + 1.0)
    out *= breathe[:, None]

    # nature version: the living place under the music, plus the drums
    if nature:
        rng = np.random.default_rng(20261002)
        out += nature_bed(len(out), rng)
        out += v6_drums(len(out), rng)

    # final fade
    fn = int(FADE_OUT * SR)
    fade = np.minimum(1.0, np.arange(len(out))[::-1] / fn)
    out *= fade[:, None]

    out /= max(1.0, np.abs(out).max() / 0.89)

    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    print(f"wrote {out_wav} ({len(out) / SR / 60:.1f} min extended lead-in)")


if __name__ == "__main__":
    main()
