# Master Prosperity Context (Condensed)

This pack condenses the uploaded context files while preserving official rules, Round 1 competition facts, prompt hints, and the repo-local workflow needed for effective strategy work.

## Source priority
1. Official Prosperity context files for current rules, products, limits, syntax, and mechanics.
2. Repo-local backtester/workflow files for validation, artifacts, and iteration.
3. Older public Prosperity repos only for reusable ideas, never as authority for current rules.

## Do not mix contexts
- Tutorial products: `EMERALDS`, `TOMATOES`
- Round 1 products: `ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`
- Never blur tutorial data with live Round 1 assumptions.

## Highest-value official competition facts
- Competition currency: `XIRECS`
- Submission shape: Python `Trader` class with `run(self, state)`
- Return value: `(result, conversions, traderData)`
- `bid()` is only required for Algo Round 2, but is safe to include in every round
- `traderData` is the persistence channel; do not rely on globals/class state surviving across calls
- `traderData` is effectively capped at 50,000 chars
- Sell quantities are negative; buy quantities are positive
- Position limits are enforced under worst-case full execution of all submitted orders for a product; if breached, all orders for that product are rejected
- Unfilled resting quantity can remain visible for bots during the iteration; if not traded on, it is cancelled before the next state
- Matching is effectively instantaneous from the player’s perspective
- Counterparty fields in trades are normally hidden unless your submission is the buyer or seller
- Conversions require an existing position, cannot exceed held/short amount, and incur transport/tariff costs

## Round 1 official facts
- Goal: earn at least **200,000 XIRECS** before the beginning of the third trading day
- Products:
  - `ASH_COATED_OSMIUM`
  - `INTARIAN_PEPPER_ROOT`
- Position limits:
  - `ASH_COATED_OSMIUM`: 80
  - `INTARIAN_PEPPER_ROOT`: 80
- `INTARIAN_PEPPER_ROOT` is described as relatively steady
- `ASH_COATED_OSMIUM` is described as more volatile, possibly with hidden structure
- Round 1 also includes a manual **Exchange Auction**

## Round 1 strategic hints worth preserving
### Pepper Root / subtle alpha
- Stable-looking does not mean alpha-free
- Watch for subtle repeated short-horizon structure:
  - mild imbalance persistence
  - spread-state persistence
  - one-sided leaning before repricing
  - repeatable micro-regimes

### Spread
- Spread may carry signal, not just trading cost
- Analyze spread regime, persistence, asymmetry, and whether “intention” appears before moves/fills

### Order placement
- Fair value is necessary but not sufficient
- Avoid obviously eager quotes and conspicuous size
- Context-aware price, size, and patience may beat blunt aggression

### Auction
- The final order can affect the clearing price
- Treat the auction as a simulation/optimization problem
- Map outcome sensitivity to price and size
- Look for bunching, recurring snap points, and stable clearing zones

### What not to overclaim from hints
- No exact winning model is implied
- No exact auction-clearing algorithm is revealed
- Do not assume Pepper Root must trend rather than mean-revert
- Treat prompt cards as soft strategic hints below official docs and data

## Repo-local operating model
- Active strategy workspace: `prosperity_rust_backtester/`
- Default strategy iteration surface: Rust backtester
- Quick visual validation surface: Python backtester + visualizer
- Follow both `AGENTS.md` files rather than pasting them into prompts

## Codex / AI prompt engineering essentials
- Mention the reusable skill `prosperity-4-strategy-engineer` for strategy reasoning tasks
- `.codex/agents/*.toml` are local project roles, not installable skills
- Role order when explicitly using a role-driven workflow:
  1. `competition_research`
  2. `alpha_miner`
  3. `execution_risk`
  4. `strategy_engineer`
  5. `validator`
- Only `strategy_engineer` should edit trader code by default
- `validator` should compare against a named baseline and end with SHIP/REJECT
- Keep one dominant change per iteration
- Default prompt should name:
  - target trader
  - dataset/round
  - baseline
  - validation command
  - intended improvement metric

## Important repo caveats
- `prosperity-4-strategy-engineer` exists as the main reusable skill
- A conceptual `repo_librarian` may be mentioned in docs, but no local runnable `.codex/agents/repo_librarian.toml` exists
- Some prompt examples mention `traders/latest_trader.py`, but the Rust-backtester context says that file is absent in this checkout; use explicit trader paths instead
- `Trader1/` should not be a default target

## Python backtester / visualizer essentials
- Install locally; do not assume `prosperity4bt` is globally installed
- Use `from datamodel import ...`, not imports from `prosperity4bt`
- Use the Logger pattern if you want visualizer-compatible algorithm output
- Test robustness under:
  - `--match-trades all`
  - `--match-trades worse`
  - `--match-trades none`
- Unknown product limits may fall back to 50 if LIMITS are not updated
- `PROSPERITY4BT_ROUND` and `PROSPERITY4BT_DAY` exist locally during backtests only; never depend on them in submission code

## Rust backtester essentials
- Treat it as the default local evaluation surface, not as the official exchange
- Prefer the local `Makefile` and explicit trader paths
- Use named baselines
- Validate on the full tutorial bundle before day-specific tuning
- Use persistence/artifacts when inventory path or execution behavior matters
- Stress-test strong candidates with stricter fill assumptions:
  - `--trade-match-mode worse --queue-penetration 0.5`
  - `--trade-match-mode none`

## Minimal recommended workflow
1. Verify official facts first.
2. Choose explicit trader + explicit baseline.
3. Form one clear hypothesis.
4. Make one localized change.
5. Backtest locally.
6. Inspect more than headline PnL:
   - per-day PnL
   - product contribution
   - inventory path
   - passive/adverse fills
   - time near limits
7. Reject fragile edges that collapse under stricter fill assumptions.
