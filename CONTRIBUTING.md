# Contributing

How to add work to Project B-Blo. Short version: follow the cycle,
meet the bar, show your work.

## The cycle

Read `ENGINEERING.md` first. Every contribution moves through study,
build, ear, refine. If you are an engineer working with Biblo, your job
is to keep that cycle turning honestly: record the studies, keep builds
reproducible, and never route around the ear.

## Adding a track

1. **Study.** Write down what you studied and what you took from it.
   Name the references. "Inspired by" is a sentence, not a vibe.
2. **Build.** Compose in code under the project's `source/` directory.
   Keep modules small and named for what they do. Record seeds and
   parameters in the build notes.
3. **Render.** Render with the project's documented toolchain. Verify
   the render: clean decode, correct duration, no artifacts.
4. **Document.** Update the project's README: the track's key, tempo,
   form, and what it is. Add build notes describing what changed
   across versions.
5. **Ear.** The track goes to Bayo. His judgment is final. Apply it,
   version the result, repeat until approved.

## Standards

- **Source beside the artifact.** A track without its published source
  is not a contribution yet.
- **Reproducible.** If another engineer cannot re-render your track
  from the repo, it isn't done.
- **No placeholders.** No typos, no lorem ipsum, no "coming soon" in
  anything that ships. Drafts stay in branches.
- **License headers.** Source files note the MIT code license; the
  music remains CC BY-SA 4.0. When in doubt, check `CODE-LICENSE.md`
  and `LICENSE.md` at the root.
- **Small diffs.** One track, one change, one clear commit message.
  History is the lab notebook; keep it legible.

## For engineers joining the team

Start here:

1. `README.md` for what this is.
2. `ARCHITECTURE.md` for how it's organized.
3. `ENGINEERING.md` for how we build.
4. The project READMEs (`lofi-biblo/README.md`,
   `nite-forest/README.md`) for the current state of the work.
5. The source directories, oldest files first. Read the engines
   before the tracks.

Then pick up the cycle where it left off: the build notes and version
history always say what the next step is.
