# Round 5 exploration: a rejected guardrail

The PEBBLES candidates test a rolling residual between XL and the mean of the
four smaller sizes. SNACKPACK variants and the exploratory notebook are retained
alongside them. These are experiments, not a verified final Round 5 submission.

A post-competition review replayed two unchanged candidates on **day 2**:

| Candidate | Own trade records | Local marked PnL |
|---|---:|---:|
| `round5_individual_products/pebbles_xl_meanRev_basket_v1.py` | 546 | 6,603.00 |
| `round5_individual_products/pebbles_xl_meanRev_basket_v2_guardrails.py` | 0 | 0.00 |

The guarded candidate's zero result is not evidence of a successful risk system.
It requires positive rolling correlation above 0.3, but the mean observed
100-tick XL/basket return correlation is **−0.991414794**. All **9,951** windows
after warmup are below the gate. The implementation therefore rejects every
entry as decoupled even though the series are strongly related in the opposite
direction. A sign assumption, not lack of a statistical relationship, disables it.

Reproduce the diagnosis from the repository root:

```bash
python3 scripts/round5_family_diagnostics.py --day 2
cd prosperity_rust_backtester
make round5 TRADER=traders/Round5/round5_individual_products/pebbles_xl_meanRev_basket_v1.py DAY=2
make round5 TRADER=traders/Round5/round5_individual_products/pebbles_xl_meanRev_basket_v2_guardrails.py DAY=2
```

The guarded candidate is **rejected as a general improvement**. Its code remains
as an archived experiment so the failure can be explained. Simply relaxing the
correlation threshold to recover trades would not validate the basket fair-value
model: a negative loading calls for a signed hedge relationship, estimated on a
training window and assessed on later data. The existing residual subtracts an
equal-weight basket without fitting that relationship.

There is a second limitation: its drawdown proxy sums position times mid changes
and omits execution-price cash flows, so it is not realized-plus-unrealized equity
despite the old comment. It should not be used as a production loss limit. The
reviewed Rust harness computes actual cash plus marked inventory for comparison.
The baseline's positive day-2 replay alone does not establish a robust strategy;
all of these observations are development-data diagnostics. Unknown Round 5
product limits outside the implemented PEBBLES/SNACKPACK subset are now rejected
explicitly by the harness instead of receiving an invented default cap.
