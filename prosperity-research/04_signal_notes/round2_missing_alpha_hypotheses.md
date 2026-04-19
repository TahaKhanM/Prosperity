# Round 2 Missing Alpha Hypotheses

Date: 2026-04-19

Scope: focused list of still-unexploited or underweighted Round 2 ideas after
the first builder loop.

Supporting files:

- [round2_postbuilder_alpha_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_alpha_report.md)
- [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)
- [round2_postbuilder_feedback_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_feedback_audit.md)

| short name | why it might work | supporting evidence | how it differs from already-tried ideas | target type | priority |
| --- | --- | --- | --- | --- | --- |
| `Pepper regime-conditioned carry shell` | local winner looks like a Pepper state machine, not a single fair-value rule | baseline Pepper changes caps, targets, edges, and sizes by state; builder only rewrote fair logic | preserves high-carry occupancy instead of replacing it with lower-carry residual logic | regime / monetization | high |
| `Pepper harvest-aware refill guard` | realized recycle gains may be getting given back by low-quality re-entry | baseline behavior and post-builder read both point to selective refills after harvest | distinct from broad soft caps and distinct from a generic quote gate | execution | high |
| `Pepper late cap-streak recycle` | selling only after prolonged rich saturation may unlock recycle PnL without abandoning carry | baseline appears to recycle late, not early; `v01` shows early flattening was the wrong shape locally | not another soft-cap branch; this is delayed recycle only in rich states | execution / risk overlay | high |
| `Pepper flow-conditioned target inventory` | remaining EV may be in moving target inventory, not moving fair alone | baseline-like shell seems to use trade-flow more structurally than `v02`, which used it mainly as skew | changes carry target and edge levels, not just quote centre | regime | medium-high |
| `Pepper quote-side / no-quote gate` | local default surface may be hiding quote-quality EV rather than raw signal EV | builder evidence shows more trading and sometimes better fill edges still lost on occupancy; quote-quality remains unresolved | unlike `v01` / `v02`, this keeps the carry shell and changes participation state only | execution | medium-high |
| `Ash medium/wide-spread taker suppression` | Ash still has a narrow transfer-shaped donor bucket in medium spreads | prior Ash validation and current baseline cooldown logic align on this | not a new Ash fair, not a broad Ash rewrite | execution | medium |
| `Ash passive-inside state placement` | small remaining Ash EV may come from better inside/join/step-out choice | passive inside fills remain good; current Ash frontier is execution-state mapping | differs from broad passive suppression and from trend overlays | execution | medium |
| `MAF extra-flow convexity` | a modestly better quote-intensive strategy may rank much higher once extra quotes matter | official Round 2 gives `25%` more quotes to accepted bids; local backtests ignore `bid()` | targets Round 2 access economics, not just base-stream PnL | validation mismatch / Round 2 specific | medium |

## What This File Explicitly Excludes

These are not missing alpha frontiers now:

- another generic Pepper dynamic-fair retune
- exact Pepper path hardcoding
- standalone OFI in either product
- a broad Ash signal rewrite
