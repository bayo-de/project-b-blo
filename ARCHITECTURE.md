# Architecture

How Project B-Blo is organized, and the standard every piece of it is held to.

## Layout

```
project-b-blo/
  README.md            The project in plain language
  ARCHITECTURE.md      This file
  ENGINEERING.md       How we build: the development cycle
  CONTRIBUTING.md      How to add work to this repo
  CODE-LICENSE.md      MIT terms for the source code
  LICENSE.md           CC BY-SA 4.0 terms for the music, plain language
  lofi-biblo/          The main line: warm, dreamy lofi hip hop
    README.md          The sound, the blueprint, the tracks
    source/            The composition engines (MIT)
    tracks/            The rendered artifacts (CC BY-SA 4.0)
  nite-forest/         The Halloween project: darker tones, built in public
    README.md          The sound, the track list, the build notes
    source/            The composition engines (MIT)
    tracks/            The rendered artifacts (CC BY-SA 4.0)
```

Two kinds of things live here, under two licenses, on purpose:

- **Source code** (MIT): the engines that compose. Anyone can read, run,
  and learn from them.
- **Music** (CC BY-SA 4.0): the rendered tracks. Anyone can share, remix,
  and sell them, with credit, under the same terms.

The rule: **source beside the artifact.** Every track in `tracks/` has the
code that made it in `source/`. A track without its source is unfinished.

## The scientist standard

Everything here is built like a scientist runs an experiment:

1. **Testable.** Every claim about a track can be checked. Render
   commands, seeds, and parameters are recorded with the build.
2. **Repeatable.** Anyone with the source and the documented toolchain
   can reproduce the artifact. If it can't be reproduced, it isn't done.
3. **Honest.** Claims align with reality. Build notes say what worked,
   what didn't, and what changed between versions. Version history is
   the lab notebook.

## Rendering

Tracks are synthesized in code, not recorded. The toolchain is Python
with NumPy/SciPy for synthesis. Each project's README names its exact
render path. Renders are deterministic given the recorded seed and
parameters; verification is re-running the render and diffing.

## Versioning

Tracks version like software: v1, v2, v3. The current version is the one
Bayo's ear approved. Superseded versions stay in history with notes on
what changed and why. Nothing is overwritten silently.
