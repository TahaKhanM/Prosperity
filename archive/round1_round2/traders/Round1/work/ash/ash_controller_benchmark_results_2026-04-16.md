# Ash Controller Benchmark Results

Date: 2026-04-16
Dataset: `round1`
Baseline: `traders/Round1/Ash.py`

## Commands

```bash
python3 scripts/round1_benchmark.py --trader traders/Round1/work/ash/ash_controller_v1.py --compare traders/Round1/Ash.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/ash/ash_controller_v2.py --compare traders/Round1/Ash.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/ash/ash_controller_v3.py --compare traders/Round1/Ash.py --dataset round1 --json
```

## Baseline

| Mode | Total PnL | Ash PnL |
| --- | ---: | ---: |
| `default` | 205542.0 | 37695.0 |
| `worse` | 205544.0 | 37697.0 |
| `queue05` | 190637.5 | 23451.5 |
| `none` | 173468.5 | 8828.0 |

Baseline robust score: `435254.375`

## Ranking

| Rank | Variant | Robust score | Score delta vs `Ash.py` | Non-regression |
| --- | --- | ---: | ---: | --- |
| 1 | `ash_controller_v1.py` | 417503.125 | -17751.250 | `false` |
| 2 | `ash_controller_v3.py` | 402182.625 | -33071.750 | `false` |
| 3 | `ash_controller_v2.py` | 396493.500 | -38760.875 | `false` |

## Per-Variant Results

### `ash_controller_v1.py`

Candidate run ids:
- `default`: `bench-ash_controller_v1-default-1776374283074`
- `worse`: `bench-ash_controller_v1-worse-1776374290854`
- `queue05`: `bench-ash_controller_v1-queue05-1776374292945`
- `none`: `bench-ash_controller_v1-none-1776374295044`

| Mode | Candidate total | Candidate Ash | Ash delta vs `Ash.py` | Default day delta |
| --- | ---: | ---: | ---: | ---: |
| `default` | 197186.5 | 29339.5 | -8355.5 | -8355.5 |
| `worse` | 197186.5 | 29339.5 | -8357.5 | n/a |
| `queue05` | 182992.5 | 15806.5 | -7645.0 | n/a |
| `none` | 166144.5 | 1504.0 | -7324.0 | n/a |

Notes:
- Least bad of the three new controllers, but still materially below baseline in every mode.
- Losses are broad rather than localized: all four modes degrade by roughly `7.3k` to `8.4k` Ash.
- `worse` and `default` are identical because the controller rarely leans on queue-sensitive Ash behavior in this form.

### `ash_controller_v2.py`

Candidate run ids:
- `default`: `bench-ash_controller_v2-default-1776374314124`
- `worse`: `bench-ash_controller_v2-worse-1776374317155`
- `queue05`: `bench-ash_controller_v2-queue05-1776374319909`
- `none`: `bench-ash_controller_v2-none-1776374324474`

| Mode | Candidate total | Candidate Ash | Ash delta vs `Ash.py` | Default day delta |
| --- | ---: | ---: | ---: | ---: |
| `default` | 182131.0 | 14284.0 | -23411.0 | -23411.0 |
| `worse` | 182131.0 | 14284.0 | -23413.0 | n/a |
| `queue05` | 175319.0 | 8133.0 | -15318.5 | n/a |
| `none` | 165746.5 | 1106.0 | -7722.0 | n/a |

Notes:
- Worst overall result.
- The discrete controller rewrite stands down too often and gives up too much neutral/passive capture.
- `default` and `worse` both lose more than `23k` Ash versus baseline.

### `ash_controller_v3.py`

Candidate run ids:
- `default`: `bench-ash_controller_v3-default-1776374363583`
- `worse`: `bench-ash_controller_v3-worse-1776374366491`
- `queue05`: `bench-ash_controller_v3-queue05-1776374368747`
- `none`: `bench-ash_controller_v3-none-1776374372606`

| Mode | Candidate total | Candidate Ash | Ash delta vs `Ash.py` | Default day delta |
| --- | ---: | ---: | ---: | ---: |
| `default` | 187031.0 | 19184.0 | -18511.0 | -18511.0 |
| `worse` | 187031.0 | 19184.0 | -18513.0 | n/a |
| `queue05` | 177108.5 | 9922.5 | -13529.0 | n/a |
| `none` | 164640.5 | 0.0 | -8828.0 | n/a |

Notes:
- Better than `v2`, worse than `v1`.
- The EV-selector version still sacrifices too much passive neutral capture.
- In `none`, Ash collapses from `8828.0` to `0.0`.

## Conclusion

All three new Ash controllers underperform `traders/Round1/Ash.py` materially on the local `round1` benchmark. None should be promoted.

Current ranking:
1. `ash_controller_v1.py`
2. `ash_controller_v3.py`
3. `ash_controller_v2.py`

If continuing from this family, `v1` is the best restart point only because it loses the least. It is still decisively below the benchmark and does not justify further validation as-is.
