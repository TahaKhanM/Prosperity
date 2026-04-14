# Prosperity 4 Round 1 Current Assumptions

Date: 2026-04-14

Scope: verify only the current Round 1 facts supported by the local official files first.

Primary official sources:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`

Soft hint only:
- `Prosperity Context/ROUND1_PROMPT_HINTS_CONTEXT.md`

## Anchor Verdicts

| Anchor | Verdict | Basis |
| --- | --- | --- |
| Round 1 live products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`. | Confirmed by official docs | `Official Prosperity Context Round 1.md:9-10` |
| Both Round 1 position limits are 80. | Confirmed by official docs | `Official Prosperity Context Round 1.md:21-24` |
| An Exchange Auction exists in Round 1. | Confirmed by official docs | `Official Prosperity Context Round 1.md:11-17` |
| The auction is separate from the first trader build. | Inferred assumption, not directly stated as a formal rule | Official docs present auction and algorithmic trading as parallel Round 1 tasks, but do not define an auction method or a trader-code interface for it in these files. |
| `bid()` is not required for Round 1 but is allowed. | Confirmed by official docs | `Official Prosperity Context.md:7,25` says `bid()` is required for Algorithmic Trading Round 2 and ignored otherwise. |

## Confirmed By Official Docs

- Round 1 is the first live trading round on Intara and the algorithmic task is to trade `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`. Source: `Official Prosperity Context Round 1.md:1-24`.
- The Round 1 position limits in the local official round file are:
  - `ASH_COATED_OSMIUM`: 80
  - `INTARIAN_PEPPER_ROOT`: 80
  Source: `Official Prosperity Context Round 1.md:21-24`.
- The Exchange Auction is part of Round 1 and is described as an additional profit opportunity alongside the algorithmic task. Source: `Official Prosperity Context Round 1.md:11-17`.
- The only method explicitly required in the generic trader interface is `run()`. Source: `Official Prosperity Context.md:23-25,36-72`.
- `bid()` is a Round 2-specific method. It may exist in every submission, but it is ignored outside Round 2. Source: `Official Prosperity Context.md:7,25`.
- Submission-side state must not rely on globals or persistent class state across invocations; `traderData` is the official persistence channel. Source: `Official Prosperity Context.md:66-78`.
- Position limits are enforced on worst-case aggregated buy or sell quantity per iteration; if breached, all orders for that side are rejected. Source: `Official Prosperity Context.md:19,223-233`.

## Inferred Assumptions

- Working assumption: keep the first trader build focused on the algorithmic `run()` strategy for the two live products, and treat auction work as a separate workstream unless a later official auction-interface document says otherwise.
  Why: the round brief presents the auction as a parallel task, while the generic interface doc only specifies `run()` and the Round 2-only `bid()` hook.
- Working assumption: Round 1 does not require any extra trader method beyond `run()`.
  Why: the only explicit round-specific extra method in the official generic doc is `bid()` for Round 2.
- Working assumption: conversions and observation-driven logic are not a Round 1 priority until product-specific docs say they matter.
  Why: the general interface doc describes conversions generically, but the Round 1 brief does not connect either live product to a conversion mechanic.
- Working assumption: the `EMERALDS` comparison for `INTARIAN_PEPPER_ROOT` is descriptive, not a license to copy tutorial fair values, tutorial limits, or tutorial product behavior.
  Why: the official round brief says Pepper Root is "similar" in steadiness, not identical in mechanics or tradable behavior.

## Borrowed / Public Analogy Only

- Any claim that `ASH_COATED_OSMIUM` is exactly a stationary market-making product or that `INTARIAN_PEPPER_ROOT` is exactly a trend product is still only a strategy hypothesis until local Round 1 data supports it.
- Any use of older Prosperity repos for fair-value design, inventory skew, quoting architecture, or diagnostics is workflow inspiration only, not authority on Round 1 products, syntax, limits, or hidden mechanics.
- The prompt-hints file can support research ideas such as watching spread state, subtle leaning, or calm quote placement, but it is not a rules document. Source boundary: `ROUND1_PROMPT_HINTS_CONTEXT.md:19-25`.

## Still Unknown

- No formal auction execution interface or clearing-rule specification is confirmed in these local official files.
- No official statement in these files says whether auction work should be automated, manual, or both.
- No product-specific official microstructure facts are confirmed beyond:
  - Pepper Root is described as relatively steady.
  - Ash-Coated Osmium is described as more volatile, possibly with pattern.
  Source: `Official Prosperity Context Round 1.md:21-24`.
- No official statement in these files confirms whether observations, conversions, or any hidden external variables matter for the two Round 1 products.
- No official statement in these files confirms a required logging format, backtester assumptions, or fill model for local validation.

## Stale Assumptions To Reject Now

- Reject: "Round 1 requires `bid()`." Official docs say that is a Round 2 requirement only.
- Reject: "Tutorial products or tutorial limits carry over into Round 1." The live products and limits are explicitly different.
- Reject: "The auction prompt implies a trader-code interface change." No such change is stated in the local official docs reviewed here.
- Reject: "`INTARIAN_PEPPER_ROOT` can be treated as literal `EMERALDS` with copied constants." The official doc gives only a loose analogy about steadiness.
- Reject: "Prompt hints are formal rules." The local hints file explicitly says they are not stronger authority than official docs.

## Immediate Research Guardrail

For subsequent Round 1 work, treat the following as the current safe foundation:
- build the first trader around `run()` only,
- target only `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`,
- enforce 80-position limits on both products,
- use `traderData` for persistence,
- keep auction analysis separate until an official auction mechanism source is verified.
