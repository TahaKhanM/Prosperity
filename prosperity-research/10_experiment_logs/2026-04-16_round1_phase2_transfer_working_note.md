# Round 1 Phase 2 Transfer Working Note

Date: 2026-04-16

## Official vs inferred

Official:
- Round 1 trader products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Position limit is `80` for both products.
- `Trader.run()` remains the required submission interface; `bid()` is not required for Round 1 trading.
- Orders are stateless across calls except for compact `traderData`.

Inferred from local evidence:
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py` is the current strongest local Round 1 strategy.
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py` remains the older robust anchor.
- `v23` improved Pepper by monetizing inventory better, not by discovering a new fair-value family.
- The remaining frontier is execution control, not another broad fair-value or threshold search.

## Named baselines

- Baseline: `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py`
- Anchor: `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py`
- Dataset: local Rust backtester `round1`

## Transfer-focused diagnosis

`v23` is locally real because it beats `v13` on `default`, `worse`, `queue05`, and `none`, but its mechanism is still mainly an inventory-monetization surface. The persisted artifacts show fewer Pepper trades and less time pinned at `>=78`, but they also show a large remaining cluster of bad Pepper buy-side executions when the strategy is already very long and the spread is still moderately wide. In the persisted default runs, the biggest remaining donor in `v23` is high-inventory aggressive Pepper buying at `spread >= 12`, especially with positive or flat top-book lean; that bucket remains strongly negative on short horizons even after the `v23` carry-target fix. This lines up with the hosted-market notes that Pepper transfer is more about avoiding bad `take_a1` behavior than about earning passive Pepper fills. The main missing piece is therefore not another carry-target tweak; it is a transfer-aware execution gate that suppresses or reshapes bad high-inventory Pepper buy actions while preserving the good low-spread carry capture that still seems to transfer.

## Ranked next mechanisms

1. `v23` Pepper buy-side hazard gate / policy-over-policy gate
   - Target the bad `position >= 78`, `spread >= 12` Pepper buy executions first.
   - Gate both sweep buys and follow-on replenishment when residual / lean / carry-left state is not strong enough.
2. `v23` conservative recycle-overlay fusion
   - Add only a narrow recycle bias in overheated or weakening long states where `v23` still stays sticky.
   - Reject immediately if it helps `default` but weakens `queue05` or `none`.
3. `v23` regime-sensitive one-sided Pepper quoting
   - Explicitly choose bid only / ask only / both / neither from carry state, spread bucket, lean, and inventory distance from target.
4. `v23` exact-control disagreement residual
   - Use the prior exact-control traces only in disagreement states that overlap the bad high-inventory buy cluster.
5. `v23` richer state representation for execution gating
   - Add OFI / wall-state / deeper-shape features only if the simpler gate shows signal but is still too blunt.

## Promote / near miss / reject criteria

Promote:
- Beats `v23` on robust score and also improves or at least preserves `queue05` and `none`.
- Shows a credible Pepper mechanism: fewer bad high-inventory buys, better Pepper fill quality, or fewer Pepper trades with higher Pepper PnL.
- Does not rely on a default-only gain.

Near miss:
- Slightly below `v23` overall but clearly improves the targeted Pepper execution bucket or conservative-mode transfer profile.
- Worth keeping only if it reveals a reusable submodule or a more precise next residual gate.

Reject:
- Improves only `default` or only optimistic matching.
- Raises Pepper trade count without clearly improving Pepper fill quality.
- Looks like another local-only carry tweak rather than a real execution-control advance.
