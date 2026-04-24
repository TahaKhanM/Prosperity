# Probe diff summary

Per-eid 3-way comparison of intent vs SUBMISSION-side fills across
Python BT, Rust BT, and (optionally) the official IMC log.


## E00_IDLE_A (range, 0..999, product=NONE)
- intent: action=IDLE_MARK, orders=, note=
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E01_CROSS_ASK_TOP (single_ts, 1000..1000, product=HYDROGEL_PACK)
- intent: action=BUY, orders=10028x1, note=cross_top_ask
- python:   buy=1 sell=0 n_fills=1 | SUBMISSION_BUY HYDROGEL_PACK 1@10028 ts=1000
- rust:     buy=1 sell=0 n_fills=1 | SUBMISSION_BUY HYDROGEL_PACK 1@10028 ts=1000
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E02_CROSS_BID_TOP (single_ts, 1100..1100, product=HYDROGEL_PACK)
- intent: action=SELL, orders=10011x-1, note=cross_top_bid
- python:   buy=0 sell=1 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 1@10011 ts=1100
- rust:     buy=0 sell=1 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 1@10011 ts=1100
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E03_FLATTEN_H (single_ts, 1200..1200, product=HYDROGEL_PACK)
- intent: action=FLAT_NOOP, orders=0x0, note=already_flat_or_no_book
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E04_CROSS_ASK_TOP_VE (single_ts, 1400..1400, product=VELVETFRUIT_EXTRACT)
- intent: action=BUY, orders=5267x1, note=cross_top_ask
- python:   buy=1 sell=0 n_fills=1 | SUBMISSION_BUY VELVETFRUIT_EXTRACT 1@5267 ts=1400
- rust:     buy=1 sell=0 n_fills=1 | SUBMISSION_BUY VELVETFRUIT_EXTRACT 1@5267 ts=1400
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E05_FLATTEN_VE (single_ts, 1500..1500, product=VELVETFRUIT_EXTRACT)
- intent: action=FLAT_SELL, orders=5261x-1, note=target_flat_1
- python:   buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VELVETFRUIT_EXTRACT 1@5262 ts=1500
- rust:     buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VELVETFRUIT_EXTRACT 1@5262 ts=1500
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E06_WATERFALL_SUM3 (single_ts, 2000..2000, product=HYDROGEL_PACK)
- intent: action=BUY, orders=10030x35, note=waterfall_sum3_vol=35_cap=100
- python:   buy=35 sell=0 n_fills=2 | SUBMISSION_BUY HYDROGEL_PACK 13@10027 ts=2000; SUBMISSION_BUY HYDROGEL_PACK 22@10030 ts=2000
- rust:     buy=35 sell=0 n_fills=2 | SUBMISSION_BUY HYDROGEL_PACK 13@10027 ts=2000; SUBMISSION_BUY HYDROGEL_PACK 22@10030 ts=2000
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E07_WATERFALL_EXCESS (single_ts, 2100..2100, product=HYDROGEL_PACK)
- intent: action=BUY, orders=10078x57, note=waterfall_excess_sum_vol=37_excess=20_cap=100
- python:   buy=37 sell=0 n_fills=2 | SUBMISSION_BUY HYDROGEL_PACK 12@10025 ts=2100; SUBMISSION_BUY HYDROGEL_PACK 25@10028 ts=2100
- rust:     buy=37 sell=0 n_fills=2 | SUBMISSION_BUY HYDROGEL_PACK 12@10025 ts=2100; SUBMISSION_BUY HYDROGEL_PACK 25@10028 ts=2100
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E08_FLATTEN_H (single_ts, 2200..2200, product=HYDROGEL_PACK)
- intent: action=FLAT_SELL, orders=10008x-72, note=target_flat_72
- python:   buy=0 sell=10 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 10@10009 ts=2200
- rust:     buy=0 sell=10 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 10@10009 ts=2200
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E09_RESTING_BELOW_BB (range, 3000..3499, product=VELVETFRUIT_EXTRACT)
- intent: action=BUY_RESTING, orders=5267x5, note=offset_1_below_bb
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E10_RESTING_JOIN_BB (range, 3500..3999, product=VELVETFRUIT_EXTRACT)
- intent: action=BUY_RESTING, orders=5271x5, note=join_best_bid
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E11_FLATTEN_VE (single_ts, 4000..4000, product=VELVETFRUIT_EXTRACT)
- intent: action=FLAT_NOOP, orders=0x0, note=already_flat_or_no_book
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E12_POSLIMIT_OVER1 (single_ts, 4200..4200, product=VEV_6500)
- intent: action=BUY, orders=1x301, note=over_by_1_room_300
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E13_POSLIMIT_EXACT (single_ts, 4300..4300, product=VEV_6500)
- intent: action=BUY, orders=1x300, note=exact_room_300
- python:   buy=17 sell=0 n_fills=1 | SUBMISSION_BUY VEV_6500 17@1 ts=4300
- rust:     buy=17 sell=0 n_fills=1 | SUBMISSION_BUY VEV_6500 17@1 ts=4300
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E14_POSLIMIT_AGG (single_ts, 4400..4400, product=VEV_6500)
- intent: action=BUY_DUAL, orders=1x144,1x144, note=sum=288_room=283
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E15_FLATTEN_V65 (single_ts, 4500..4500, product=VEV_6500)
- intent: action=FLAT_SELL, orders=-1x-17, note=target_flat_17
- python:   buy=0 sell=16 n_fills=1 | SUBMISSION_SELL VEV_6500 16@0 ts=4500
- rust:     buy=0 sell=16 n_fills=1 | SUBMISSION_SELL VEV_6500 16@0 ts=4500
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E16_SELFCROSS (single_ts, 5000..5000, product=VEV_6500)
- intent: action=SELF_CROSS, orders=6x3,-5x-3, note=high_buy_low_sell
- python:   buy=3 sell=3 n_fills=2 | SUBMISSION_BUY VEV_6500 3@1 ts=5000; SUBMISSION_SELL VEV_6500 3@0 ts=5000
- rust:     buy=3 sell=3 n_fills=2 | SUBMISSION_BUY VEV_6500 3@1 ts=5000; SUBMISSION_SELL VEV_6500 3@0 ts=5000
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E17_FLATTEN_V65 (single_ts, 5100..5100, product=VEV_6500)
- intent: action=FLAT_SELL, orders=-1x-1, note=target_flat_1
- python:   buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VEV_6500 1@0 ts=5100
- rust:     buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VEV_6500 1@0 ts=5100
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E18_QTY_ZERO (single_ts, 5300..5300, product=VEV_6500)
- intent: action=BUY_ZERO_QTY, orders=1x0, note=schema_edge
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E19_DUPLICATE_BUY (single_ts, 5400..5400, product=VEV_6500)
- intent: action=BUY_DUPLICATE, orders=1x2,1x2, note=same_price_same_side
- python:   buy=4 sell=0 n_fills=2 | SUBMISSION_BUY VEV_6500 2@1 ts=5400; SUBMISSION_BUY VEV_6500 2@1 ts=5400
- rust:     buy=4 sell=0 n_fills=2 | SUBMISSION_BUY VEV_6500 2@1 ts=5400; SUBMISSION_BUY VEV_6500 2@1 ts=5400
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E20_FLATTEN_V65 (single_ts, 5500..5500, product=VEV_6500)
- intent: action=FLAT_SELL, orders=-1x-4, note=target_flat_4
- python:   buy=0 sell=4 n_fills=1 | SUBMISSION_SELL VEV_6500 4@0 ts=5500
- rust:     buy=0 sell=4 n_fills=1 | SUBMISSION_SELL VEV_6500 4@0 ts=5500
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E21_PRICE_ZERO_BUY (single_ts, 6000..6000, product=VEV_6500)
- intent: action=BUY, orders=0x1, note=explicit_price_0
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E22_SELL_AT_ZERO (single_ts, 6100..6100, product=VEV_6500)
- intent: action=SELL, orders=0x-1, note=explicit_price_0
- python:   buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VEV_6500 1@0 ts=6100
- rust:     buy=0 sell=1 n_fills=1 | SUBMISSION_SELL VEV_6500 1@0 ts=6100
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E23_FLATTEN_V65 (single_ts, 6200..6200, product=VEV_6500)
- intent: action=FLAT_BUY, orders=2x1, note=target_flat_-1
- python:   buy=1 sell=0 n_fills=1 | SUBMISSION_BUY VEV_6500 1@1 ts=6200
- rust:     buy=1 sell=0 n_fills=1 | SUBMISSION_BUY VEV_6500 1@1 ts=6200
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E24_RESTING_ABOVE_BA (range, 7000..7499, product=VELVETFRUIT_EXTRACT)
- intent: action=SELL_RESTING, orders=5272x-5, note=offset_1_above_ba
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E25_FLATTEN_VE (single_ts, 7500..7500, product=VELVETFRUIT_EXTRACT)
- intent: action=FLAT_NOOP, orders=0x0, note=already_flat_or_no_book
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E26_WIDE_RESTING_H (range, 8000..8499, product=HYDROGEL_PACK)
- intent: action=WIDE_QUOTE, orders=9989x3,10035x-3, note=offset_15
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E27_FLATTEN_H (single_ts, 8500..8500, product=HYDROGEL_PACK)
- intent: action=FLAT_SELL, orders=10009x-62, note=target_flat_62
- python:   buy=0 sell=14 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 14@10010 ts=8500
- rust:     buy=0 sell=14 n_fills=1 | SUBMISSION_SELL HYDROGEL_PACK 14@10010 ts=8500
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official

## E28_IDLE_END (range, 9000..9999, product=NONE)
- intent: action=IDLE_MARK, orders=, note=
- python:   buy=0 sell=0 n_fills=0 | (none)
- rust:     buy=0 sell=0 n_fills=0 | (none)
- official: buy=pending sell=pending n_fills=pending | (none)
- divergence_py_vs_rust: no
- divergence_local_vs_official: pending_official
