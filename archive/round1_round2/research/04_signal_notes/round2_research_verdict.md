# Round 2 Research Verdict

Date: 2026-04-19

Decision on the main uncertainty:

- The main problem is `D`: some combination of missing monetization and
  validation-surface mismatch.
- More precise ranking:
  - primary blocker: `B` the builder has real Pepper alpha but is failing to
    monetize it in a shell that can beat the local baseline
  - secondary blocker: `C` the default local surface is too incomplete to rank
    Round 2-specific quote-intensity ideas correctly
  - lower-priority blocker: `A` there are still some missed alphas, but they
    are mostly monetization / state-shell alphas rather than brand-new
    predictor families

Why this is decisive:

- first-wave research already found the right Pepper predictor stack
- `v01 -> v02` showed the big recovery came from restoring carry shape, not
  from discovering a new signal
- the current local objective is saturated by Pepper carry and does not model
  MAF or extra-flow

Practical consequence:

- the next builder cycle should stop trying to replace Pepper carry with a
  cleaner fair model
- the next builder cycle should preserve the carry shell and improve recycle /
  refill discipline
- validation should stop using the current default local surface as the sole
  ranking objective

One-sentence verdict:
- The blocker is mainly `real Pepper alpha trapped inside the wrong monetization shell on an incomplete local Round 2 ranking surface`.

Highest-EV next strategy direction:
- Build on the baseline Pepper carry shell and add `harvest-aware refill guard` plus `late cap-streak recycle` before changing the Pepper fair model again.

Highest-EV next research direction:
- Redesign validation around a split Round 2 surface: current explicit local base-stream attribution plus a stricter or hosted-aware lens for quote-intensity and MAF-sensitive ideas.

Biggest unresolved risk:
- The local checkout still cannot measure how much extra `25%` quote access changes strategy ranking, so quote-quality candidates may remain misranked until stricter or hosted evidence is added.
