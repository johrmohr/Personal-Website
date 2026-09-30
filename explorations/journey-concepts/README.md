# Journey concept: black hole to the open sea

A standalone prototype, separate from the Astro site. Published privately at https://claude.ai/artifact/8gRZ3wM5o5jCiXkZis6ySo.

Run it locally with the `journey-concepts` entry in `.claude/launch.json` (a static server on port 4411). The page opens in the website preview (three sections with the site's real text). Close it, or open `/#review`, for the frame-by-frame player.

## What happens

One continuous video per ending, `media/journey_<sun|moon>.mp4` (30 fps, 1920x1080):

1. **Approach** (0–3.4 s): NASA SVS 14576 frames, re-aimed with `tools/campath.py` and built by `tools/build_footage.py` into `bh-journey.mp4`.
2. **Plunge** (3.4–6.9 s): the same footage up to frame 207, just before NASA's band of light bends up into its arch. Over its last 18 frames the top of the sun or the moon is painted rising out of the middle of the band (`tools/cap_cue.py`), so the disc is there from the moment it appears.
3. **Rise over the sea** (6.9–14.5 s): Higgsfield's Seedance 2.5 `video_extension` continues that footage (frames 51–207 uploaded, extended forward 8 s). The model keeps the motion; the disc keeps rising while the band settles into the horizon, the sea and sky come up and the camera pulls back onto the reference framing (the end frames in `output/higgsfield-keyframes/v3/`, passed as an image reference).
4. **Open sea**: at rest `media/loop_<sun|moon>.mp4` holds (a Higgsfield loop with the same frame at both ends, crossfaded over 1 s at the wrap). The journey's last 0.5 s blends into it, and the page picks it up at 0.5 s (`in` in `media/meta.json`).

`tools/build_ext.sh <key> <extension> <loop> <r0> <ramp> <skip> <cue footage> <threshold>` assembles it: the extension is upscaled, its first `skip` frames dropped, its first `ramp` seconds played `r0` times fast easing to 1x (the model starts slower than NASA's pace; `tools/arch_top.py` measures the rise on both sides of the join), motion-interpolated from 24 to 30 fps, and joined to the painted NASA frames. Both endings are eased to the same length (7.614 s after the handoff), which the page uses as `SHOT`. Before the blend into the loop, `tools/align_tail.py` measures the disc and the horizon on both sides and puts them on one frame (the extension eases into a push-in of about 3% over its last 4 s, the loop is reframed by under 1.3%), so the handoff at rest doesn't slide.

Leaving the sea going back up, the loop dissolves into the reversed site cut over half a second.

The site's sections rest at `K = [0, 3.4, 14.55]` s of the journey: intro on the distant black hole, work at the start of the plunge, projects + contact at rest over the sea. Every scroll, down or back up, takes `MOVE` = 3.4 s: intro ↔ work is the footage at 1x, and work ↔ the sea covers its 11.1 s at about 3.5x, easing to 1x over the `EASE` = 0.6 s next to the sea so the loop carries on at its own pace (`moveJ`, `moveRate`). The line-and-dot print dissolves over 1.6 s after the handoff.

The site preview doesn't play the journey at 3.5x (the browser drops frames decoding 1080p that fast). It plays the site cut, `media/journey_<sun|moon>_site.mp4` from `tools/make_site_cut.py`: 6.8 s at 60 fps, the three sections at 0, 3.4 and 6.8 s, with the fast stretch already compressed and motion-blurred (a 360° shutter: each frame averages the source it spans). Going back up plays `journey_<sun|moon>_site_rev.mp4`, the same frames reversed, forward. At rest both copies wait on the matching frame. The review player still scrubs the whole journey, and only the ending being shown is downloaded. The ending is picked from the visitor's local time: sun from 6:00 to 18:59, otherwise the moon. Without the journey videos the page falls back to its own in-browser sea.

## Measured inputs

- NASA's line sits near y = 518 (of 900) mid-frame and bows about 8 px lower toward the edges.
- The `RING_*` table (traced with `tools/trace_ring_early.py`, `tools/trace_ring.py`, `tools/clean_ring.py`) drives only the fallback render now.

## Exports

With the save helper listening on `127.0.0.1:4412` and the viewport at 1600x900, `window.__journey.exportRun(kind, end)` renders frames from stills (`frames/`, extracted with ffmpeg, so a hidden tab never waits on video seeks): `kind` is `walk` (the site walkthrough down to the sea and back up, text drawn from the live layout) or `film` (no text), and `end` is `sun` or `moon`. The encoded videos live in `output/animation-review/`, with web copies in `media/`. Keyframes for video generation are in `output/higgsfield-keyframes/`.

The previous engraved-beach version is kept as `../nasa-source/work/index_v6_engraved.html`.
