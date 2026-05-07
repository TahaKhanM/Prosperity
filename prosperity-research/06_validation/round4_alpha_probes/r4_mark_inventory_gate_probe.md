# r4_mark_inventory_gate_probe — REJECT

## Probe definition

Track per-(Mark, product) inferred inventory from market trades; when
|inventory| > MARK_INV_THR=50, multiply that Mark's lean contribution by
INV_GATE_REDUCTION=0.5. Inventory resets at day boundary. Tracks Mark
14, Mark 38, Mark 22, Mark 49.

Pre-registered (locked): MARK_INV_THR=50, INV_GATE_REDUCTION=0.5,
INV_RESET_PER_DAY=True.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1298 | 68,616.00 | -369.5 |
| day-2 | 2 | 1287 | 109,466.50 | -559.0 |
| day-3 | 3 | 1196 | 49,336.50 | -163.0 |
| total | | 3,781 | **227,419.00** | **−1,091.5** |

Per-product Δ vs floor:
- HYD: 134,593 vs 134,581 = +12
- VFE: 21,875.50 vs 22,979 = -1,103.50

## Diagnosis

The inventory gate is reducing the lean weight when a Mark's accumulated
position (per the trader's own running tally of their flow) crosses ±50
units. The biggest impact is on VFE: Mark 49's frequent VFE sells
accumulate inventory rapidly, triggering the gate, which reduces our
copy lean. We lose some of the +VFE alpha that came from following Mark
49's sells.

The inventory threshold is too tight: 50 units is reached after just a
few large prints from a frequent Mark. The intended interpretation
("Mark is long-loaded → next move is unwind") doesn't match the actual
flow pattern, where Marks are *consistent in side* rather than building
to an unwind.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +500: **FAIL (-1,091.5)**.

## Verdict — REJECT

The per-Mark inventory hypothesis (Marks build inventory then unwind)
does not hold for the structural-pair Marks in our lean stack. They are
flow-consistent, not inventory-mean-reverting.
