#!/usr/bin/env python3
"""Feel Study 01 — the Dilla lessons, implemented.

Bayo's critique (2026-10-02, ~3am): the engine's music "sounds like a
computer made it." The masters study (research/masters-study-2026-10-02.md)
diagnosed why. This script is the response: a from-scratch render that
replaces the computer tells with human principles.

THE COMPUTER TELLS WE'RE KILLING:
1. Random per-hit jitter  ->  FIXED per-track feel template (Dilla's feel
   is one committed micro-timing map, repeated identically, not re-rolled).
2. Uniform random velocity  ->  PHRASE-SHAPED velocity (accents follow the
   phrase: starts lift, pickups rise, endings decay).
3. Swing as one global knob  ->  INTER-VOICE CONFLICT (straight hats vs.
   early snare; the lean lives between voices, not in a knob).
4. Kick on the grid  ->  STUTTER-STEP (a quiet kick a 16th before each
   snare, pushing into the backbeat).
5. Root-drone bass  ->  BASS ANSWERS THE KICK (offbeat, bouncy counter-
   line, lazy behind the beat; never just roots on 1).
6. Motif regenerated per section  ->  ONE SEED MOTIF, developed across the
   track (expose plain, then microchop-flip, sequence, invert, return).
7. Block chord jumps  ->  VOICE LEADING (each voicing chosen for minimal
   motion from the last; common tones stay put).
8. Perfect polish  ->  ONE DELIBERATE MISTAKE per section (a rushed fill,
   an early stab — placed, then left alone, Madlib doctrine).
9. Flat stack arrangement  ->  EXPOSE-THEN-FLIP waves (Nujabes: state the
   idea naked, accumulate, strip, return).
10. Static dynamics  ->  SIDECHAIN BREATHE (pads duck gently under each
    kick; the whole track breathes with the drums).

HARMONY (the progression study, applied):
D minor: Dm9 - Bbmaj9 - Gm9 - A7. i-VI-iv-V7. The A7 is a secondary
dominant (V7 of i) — the C# leading tone pulls home to D. That single
chromatic pull is the "interesting and pleasing" move: tension with
intention, not decoration.

Playability test (Tomppabeats): every part performable by two hands.
If it couldn't be played live, it got thinned.

This is a study, not the engine. If Bayo's ears approve, the feel system
ports into lofi_endless_engine.py as the v8 foundation.
"""
import sys
import wave

import numpy as np

sys.path.insert(0, "/home/hatch/workspace/biblo-brand/lofi-engine")
from lofi_endless_engine import (
    SR, midi, lowpass_fft, fftconvolve, underwater,
    pad_chord, embrace, sub_drone, shimmer,
    rhodes_note, piano_note, harp_note, pluck_note, handpan_note,
    kick, snare, hat, bass_note,
)

VOICES = {"piano": piano_note, "harp": harp_note, "pluck": pluck_note,
          "handpan": handpan_note}

# ------------------------------------------------------------------ feel ---
MS = SR / 1000.0


class Feel:
    """One committed micro-timing map for the whole track.

    Dilla's lesson: the feel is a FIXED template, repeated identically.
    We roll it once per track from the seed — then it never changes.
    """

    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        # The lean: straight hats (0ms) against an early snare.
        # Picked once, committed for the whole track.
        self.snare_ms = -16.0 if rng.random() < 0.7 else 14.0
        self.hat_ms = 0.0
        self.kick_ms = 6.0
        self.stutter_ms = 4.0
        self.bass_ms = 14.0      # lazy, behind the beat
        self.keys_ms = -6.0      # laid back
        self.motif_ms = -8.0

    def vel(self, bar_in_phrase, step_in_bar, base=1.0):
        """Phrase-shaped velocity. Accents follow structure, not dice."""
        v = base
        if bar_in_phrase == 0:
            v *= 1.12            # phrase starts lift
        if bar_in_phrase == 7:
            v *= 0.90            # phrase ends decay
        if step_in_bar in (14, 15):
            v *= 1.08            # pickup rises into the downbeat
        if step_in_bar == 0:
            v *= 1.05            # downbeat speaks
        v *= 0.98 + 0.04 * np.random.default_rng(
            bar_in_phrase * 131 + step_in_bar).random()
        return v


def voice_lead(prev, nxt):
    """Choose octave displacements minimizing motion from prev voicing.
    Common tones stay; everything else walks, never jumps."""
    import itertools
    best, bestcost = None, 1e18
    n = min(len(prev), len(nxt))
    for shifts in itertools.product((-12, 0, 12), repeat=len(nxt)):
        cand = [m + s for m, s in zip(nxt, shifts)]
        if min(cand) < 45 or max(cand) > 86:
            continue
        if any(cand[i] >= cand[i + 1] for i in range(len(cand) - 1)):
            continue
        cost = sum(abs(c - p) for c, p in zip(cand, prev[:n]))
        cost += sum(abs(s) for s in shifts) * 0.15
        if cost < bestcost:
            bestcost, best = cost, cand
    return best if best is not None else nxt


# ------------------------------------------------------------- the study ---
# D minor: Dm9 - Bbmaj9 - Gm9 - A7 (i - VI - iv - V7). The V7's C# is the
# secondary-dominant pull home. Voicings in 3-5-7-9 stacks; voice_lead()
# will walk them into each other.
PROG = [
    ([53, 57, 60, 64], 38),   # Dm9   (i)
    ([62, 65, 69, 72], 34),   # Bbmaj9 (VI)
    ([58, 62, 65, 69], 31),   # Gm9   (iv)
    ([61, 64, 67, 71], 33),   # A7    (V7 -> home)
]

# The seed motif: one idea for the whole track. E4 D4 C4 A3 — a falling
# sigh out of the Dm9, at CHORD register on felt piano (V7: Bayo asked
# for piano over the whiny octave-up Rhodes). Everything later is a
# transformation of this.
SEED_MOTIF = [64, 62, 60, 57]


def develop_motif(section):
    """Expose-then-flip. The motif's life across the track."""
    m = SEED_MOTIF
    if section == 0:
        return m, "plain (exposed naked)"
    if section == 1:
        return m, "plain (drums enter under it)"
    if section == 2:
        # microchop: same cells, new order — timbre coherent, rhythm new
        return [m[2], m[0], m[3], m[1]], "microchop flip"
    if section == 3:
        return m, "plain (stripped back)"
    if section == 4:
        # sequence: the sigh climbs a whole step
        return [x + 2 for x in m], "sequenced up"
    if section == 5:
        # inversion: the falling sigh becomes a rising question
        return [m[0], m[0] + (m[0] - m[1]),
                m[0] + (m[0] - m[2]), m[0] + (m[0] - m[3])], "inverted"
    return m, "plain (home)"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="piano", choices=list(VOICES),
                    help="melody instrument (V7 exploration)")
    a = ap.parse_args()
    melody = VOICES[a.voice]
    BPM = 72.0
    SECTIONS = 7            # 8 bars each -> ~3.1 min
    BARS = SECTIONS * 8
    BEAT = 60.0 / BPM
    STEP = BEAT / 4.0
    SWING = 0.0             # no global swing knob — the lean is inter-voice
    feel = Feel(seed=20261002)
    rng = np.random.default_rng(777)

    total = BARS * 4 * BEAT + 9.0
    N = int(total * SR)
    mix = np.zeros(N)
    verb = np.zeros(N)
    kick_times = []

    def at(step):
        bar_step = step % 16
        t = (step // 16) * 4 * BEAT + (bar_step // 2) * 2 * STEP
        if bar_step % 2 == 1:
            t += STEP * (1.0 + SWING)
        return t

    def place(buf, sound, t_sec):
        i = int(t_sec * SR)
        if i < 0:
            sound = sound[-i:]
            i = 0
        j = min(i + len(sound), N)
        if i < N:
            buf[i:j] += sound[: j - i]

    def ms(x):
        return x * MS / SR  # ms -> seconds

    # voice-lead the whole progression cycle once; the harmony walks
    voiced = []
    prev = PROG[0][0]
    for chord, root in PROG:
        v = voice_lead(prev, chord)
        voiced.append((v, root))
        prev = v

    for sec in range(SECTIONS):
        motif, how = develop_motif(sec)
        print(f"  section {sec + 1}/{SECTIONS}: motif {how}", flush=True)
        drums_on = sec not in (0, 3)          # expose naked, then strip
        for bar in range(8):
            gbar = sec * 8 + bar
            chord, root = voiced[(gbar // 2) % 4]
            # final two bars: resolve home under the fade
            if sec == SECTIONS - 1 and bar >= 6:
                chord, root = voiced[0]
            base = gbar * 16
            phrase_bar = bar  # 0..7 within the 8-bar phrase

            if bar % 2 == 0:
                t = at(base) + ms(feel.keys_ms)
                place(verb, pad_chord([midi(m) for m in chord],
                                      dur=2 * 4 * BEAT, vel=0.20),
                      t)
                place(verb, embrace([midi(m) for m in chord[:3]],
                                    dur=2 * 4 * BEAT, vel=0.55), t)
                place(mix, sub_drone(midi(root - 12), dur=2 * 4 * BEAT,
                                     vel=0.8), t)
                place(verb, shimmer(midi(chord[-1]), vel=0.36),
                      at(base + 4) + ms(feel.keys_ms))

            # Rhodes stabs: downbeat + swung answer, phrase-shaped
            for s, vb in ((0, 0.95), (7, 0.60)):
                t = at(base + s) + ms(feel.keys_ms)
                v = feel.vel(phrase_bar, s, vb)
                for m in chord:
                    place(mix, rhodes_note(midi(m), dur=4.5, vel=v), t)
                    place(verb, rhodes_note(midi(m), dur=4.5, vel=v * 0.8),
                          t)

            # bass ANSWERS the kick: offbeat counter-line, lazy, bouncy.
            # root with the kick on 1, then the 5th and 3rd talking back.
            if drums_on:
                for s, deg, vb in ((0, 0, 0.85), (6, 7, 0.55),
                                   (11, 7, 0.50), (14, 3, 0.45)):
                    t = at(base + s) + ms(feel.bass_ms)
                    v = feel.vel(phrase_bar, s, vb)
                    place(mix, bass_note(midi(root + deg), dur=0.7, vel=v),
                          t)

            # drums: the committed feel. fixed offsets, every bar identical.
            if drums_on and not (sec == 3):
                for s in (0, 7, 10):
                    t = at(base + s) + ms(feel.kick_ms)
                    v = feel.vel(phrase_bar, s, 0.95)
                    place(mix, kick(vel=v), t)
                    kick_times.append(t)
                # stutter-step: a quiet kick a 16th before each snare
                for s in (3, 11):
                    t = at(base + s) + ms(feel.stutter_ms)
                    place(mix, kick(vel=0.45), t)
                    kick_times.append(t)
                for s in (4, 12):
                    t = at(base + s) + ms(feel.snare_ms)
                    v = feel.vel(phrase_bar, s, 0.92)
                    place(mix, snare(rng, vel=v), t)
                # hats DEAD ON the grid — the conflict with the early
                # snare is the lean (Dilla inversion)
                for i, s in enumerate((0, 4, 8, 12)):
                    t = at(base + s) + ms(feel.hat_ms)
                    place(mix, hat(rng) * (1.0 if i % 2 == 0 else 0.55), t)
                for s in (2, 6, 10, 14):
                    t = at(base + s) + ms(feel.hat_ms)
                    place(mix, hat(rng) * 0.35, t)

            # the motif, developed — V7 melody voice at chord register,
            # laid back, phrase-shaped
            if bar % 2 == 1:
                for k, m_ in enumerate(motif):
                    s = (2, 5, 9, 12)[k]
                    t = at(base + s) + ms(feel.motif_ms)
                    v = feel.vel(phrase_bar, s, 0.62 * (1 - 0.12 * k))
                    place(mix, melody(midi(m_), dur=2.2, vel=v, rng=rng),
                          t)
                    place(verb, melody(midi(m_), dur=2.2, vel=v * 0.8,
                                       rng=rng), t)

        # ONE deliberate mistake per section (Madlib doctrine) — placed,
        # then left alone. Not random: composed imperfection.
        if sec == 2:
            # rushed fill into bar 20: four 16ths, each a little early,
            # accelerating — the drummer leaning forward
            fb = sec * 8 + 4
            for k in range(4):
                t = at(fb * 16 + 12 + k) - ms(6 + 3 * k)
                place(mix, snare(rng, vel=0.5),
                      t)
            print("    + mistake: rushed fill into bar 21", flush=True)
        if sec == 4:
            # early chord stab: the Rhodes jumps the downbeat by 25ms
            # and nobody fixes it
            sb = sec * 8 + 0
            t = at(sb * 16) - ms(25)
            for m in voiced[0][0]:
                place(mix, rhodes_note(midi(m), dur=2.0, vel=0.7), t)
            print("    + mistake: early stab on the section downbeat",
                  flush=True)

    # ---- sidechain breathe: pads duck under every kick, the track
    # inhales with the drums (modern lofi pump, gentle)
    duck = np.ones(N)
    kt = np.array(kick_times)
    # vectorized-ish: for each kick, dip 90ms
    for t in kt:
        i = int(t * SR)
        L = int(0.09 * SR)
        if i + L < N:
            env = np.linspace(1.0, 0.82, L // 3)
            env = np.concatenate([env, np.linspace(0.82, 1.0, L - L // 3)])
            duck[i:i + L] = np.minimum(duck[i:i + L], env)
    verb *= duck

    # ---- room: short, warm, a little dusty
    ir_n = int(1.4 * SR)
    ir_t = np.arange(ir_n) / SR
    ir = np.zeros(ir_n)
    for _k in range(7):
        _f = rng.uniform(200, 2000)
        _d = rng.uniform(1.8, 3.2)
        _p = rng.uniform(0, 2 * np.pi)
        ir += rng.uniform(0.4, 1.0) * np.sin(2 * np.pi * _f * ir_t + _p) \
            * np.exp(-ir_t * _d)
    ir = lowpass_fft(ir, 2400)
    ir *= np.minimum(1.0, ir_t / 0.01)
    ir /= max(1e-9, np.sqrt((ir ** 2).sum()))
    conv = fftconvolve(verb, ir)[:N]
    conv = underwater(conv, mix_=0.10)
    hd = int(0.012 * SR)
    room_r = np.concatenate([np.zeros(hd), conv])[:N]
    st = np.stack([mix + conv * 0.15, mix + room_r * 0.15])

    # tape whisper + fade
    t_all = np.arange(N) / SR
    st = st * (1.0 + 0.018 * np.sin(2 * np.pi * 0.55 * t_all))
    hiss = rng.standard_normal((2, N)) * 0.0016
    hiss = np.stack([np.convolve(hiss[c], np.ones(48) / 48, mode="same")
                     for c in range(2)])
    st = st + hiss
    st = np.stack([lowpass_fft(st[c], 8000) for c in range(2)])
    n_f = int(8.0 * SR)
    st[:, N - n_f:] *= np.linspace(1, 0, n_f)

    peak = np.abs(st).max()
    st = st / max(1e-9, peak) * 0.89
    out = ("/home/hatch/workspace/biblo-brand/lofi-engine/endless/v7-nite/"
           f"feel-study-02-{a.voice}.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st.T * 32767).astype(np.int16).tobytes())
    print(f"wrote {out} ({N / SR / 60:.1f} min, peak 0.890)")


if __name__ == "__main__":
    main()
