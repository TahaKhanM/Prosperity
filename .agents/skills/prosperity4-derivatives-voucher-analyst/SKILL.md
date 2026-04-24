---
name: prosperity-4-derivatives-voucher-analyst
description: Handle Prosperity 4 voucher/option products rigorously. Identifies underlyings, strikes, expiry mechanics, intrinsic value, moneyness, and discrete-time settlement. Distinguishes financial option definitions from Prosperity's actual competition implementation. Never assumes Black-Scholes applies blindly.
---

# Prosperity 4 Derivatives / Voucher Analyst

## Mission
Produce a rigorous specification of every voucher or derivative product on the exchange: what it is, what it pays, when it settles, and what trading mechanics it inherits from the official rules. Downstream hypothesis generation and implementation depend on this being exactly right.

## Trigger conditions
- A round introduces voucher, option, coupon, basket, or conversion-based products.
- Voucher symbols are observed in `order_depths` but not yet mapped to strikes/expiries.
- A hypothesis depends on parity, intrinsic floor, or exercise mechanics.
- Live prices deviate materially from intrinsic and someone wants to call it an alpha.

## Required inputs
- `prosperity-research/01_assumptions/current_assumptions.md` (round context, voucher count, strike range).
- In-session briefing text describing voucher specs.
- Official written docs in `Prosperity Context/Unrefined Context/` (including any attached round doc).
- Live data: `order_depths` from any run; CSVs under `datasets/roundN/`.
- Forensics report (`data_forensics_report.md`) for observed voucher mids.

## Concepts — what matters
1. **Underlying identification**: exact symbol of the underlying (e.g. VELVET_FRUIT_EXTRACT) and how its mid is computed (order-book mid vs weighted microprice).
2. **Strike extraction**: verified value of K, not inferred from naming alone.
3. **Expiry mechanics**: exact round or tick of settlement; whether the voucher trades up to expiry; whether it settles in cash or conversion.
4. **Intrinsic value**: `max(S - K, 0)` for calls, `max(K - S, 0)` for puts; confirm direction from docs.
5. **Moneyness**: ITM / ATM / OTM at the current underlying mid.
6. **Time value**: `market_mid - intrinsic`; sign and distribution.
7. **Discrete-time settlement**: Prosperity rounds are discrete. There is no continuous delta-hedging loop unless simulation ticks are fine enough, and even then it is gated by spread and limits.
8. **Parity / ladder relationships**: if multiple strikes exist, the price ladder must be monotone in K (calls: price non-increasing in K; puts: non-decreasing). Violations may be alpha or data error.
9. **Settlement mechanics in this round**: cash-settled at underlying price, physical-settled to underlying, or rebated at fixed value. Confirm from docs.
10. **Position limits**: voucher position limit may differ from underlying; record both.

## Step-by-step workflow
### 1. Build the voucher specification table
Columns: `symbol`, `type` (call | put | other), `underlying`, `K`, `expiry`, `settlement` (cash | physical | rebate), `position_limit`, `data_observed` (yes/no), `source`, `confidence`.

If exact symbol strings are not yet known, write placeholders `UNKNOWN_VOUCHER_K=4000` etc. and flag in the Unknowns section.

### 2. Map intrinsic and observed price
For each voucher, compute:
- underlying mid,
- intrinsic,
- observed voucher mid,
- time value,
- moneyness bucket.

### 3. Parity ladder check
Sort vouchers by K. Confirm monotonicity. Report any violations with timestamps.

### 4. Settlement sanity
For each voucher with < N rounds to expiry, compute: if the underlying price stays constant, the terminal payoff is X. If the current mid is above/below X + reasonable time-value bound, flag.

### 5. What we will NOT assume
- No Black-Scholes without justification. Prosperity is discrete, the number of rounds to expiry is small, and the underlying is not a lognormal random walk by default.
- No continuous-time delta hedging.
- No vega or theta numbers unless derived from observed vol and confirmed as behaviorally meaningful.

### 6. What we will tentatively use
- Intrinsic floor for deep ITM (provides a price bound).
- Parity ladder between strikes.
- Terminal cash-settled payoff mapping to valuation at expiry.
- A discrete binomial or lattice approximation *if and only if* the underlying is classified as random-walk-like by `prosperity-4-product-classifier` with high confidence.

### 7. Implementation constraints for the trader
- Voucher symbols must match the observed `order_depths` keys exactly; do not rename.
- Voucher orders respect their own position limit, not the underlying's.
- Maintain voucher-side inventory carefully; taking a short voucher position with limited underlying liquidity creates asymmetric tail risk.
- If settlement is physical (conversion), the local backtester may not simulate conversions faithfully — flag and keep strategies that depend on conversion out of local "validated" status.

## Evidence requirements
- Every strike and expiry must cite its source.
- Every parity violation must list at least three timestamps and the mids involved.
- Every claim about settlement mechanics must quote the official doc.

## Failure modes to avoid
- Treating voucher price as a pure function of mid (ignoring liquidity, discreteness, limit caps).
- Using option-pricing formulas without confirming underlying dynamics.
- Assuming parity holds when observed mids may reflect stale depth.
- Forgetting that Prosperity voucher markets can be thin — mid-price estimates may be noisy.
- Copying a Round 2 MAF bidding framework onto Round 3 voucher trading.

## Guardrails
- Never propose a live voucher strategy before the specification is confirmed and parity is checked.
- Never use a continuous-time Greek without explicit evidence that discreteness is negligible here.
- Never rely on conversions in validated strategies until the Rust backtester is known to simulate them (currently: it does not).

## Example invocation prompts
- "Use prosperity-4-derivatives-voucher-analyst to produce the Round 3 voucher specification table once the symbol names and strikes appear in data."
- "Use prosperity-4-derivatives-voucher-analyst to check parity across the 10 VELVET_FRUIT_EXTRACT vouchers and flag any ladder violations."
- "Use prosperity-4-derivatives-voucher-analyst to decide whether discrete binomial valuation or intrinsic-floor-only is appropriate given the current classifier output for the underlying."

## Concrete deliverable format
Write to `prosperity-research/04_signal_notes/roundN_voucher_spec.md` with:
1. Voucher specification table.
2. Intrinsic/observed/time-value snapshot per voucher.
3. Parity check.
4. Settlement mechanics confirmed.
5. Valuation approach decision (intrinsic-floor | lattice | none) with justification.
6. Hypotheses forwarded to `prosperity-4-alpha-hypothesis-lab`.
7. Unknowns.

## Integration
- Consumes: assumptions, forensics, classifier output.
- Feeds: `prosperity-4-alpha-hypothesis-lab`, `prosperity-4-implementation-planner`, `prosperity-4-backtest-auditor`.
