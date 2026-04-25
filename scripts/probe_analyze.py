#!/usr/bin/env python3
"""probe_analyze.py — unify PROBE log lines + fills across three backtesters.

Inputs (any subset; all flags optional):
    --python-stdout    raw stdout captured from `python -m prosperity4bt --print`
    --python-json      output log file from prosperity4bt (3-section text format)
    --rust-stdout      stdout captured from rust_backtester (terminal summary)
    --rust-json        rust_backtester submission.log (IMC-format JSON)
    --official-log     IMC submission .log file (IMC-format JSON, e.g. 379811.log)

PROBE-line format (emitted by probe_v1_matching.py):

    PROBE eid=E05 ts=2000 product=HYDROGEL_PACK action=BUY price=10023 qty=26 \\
        book=b=10011x8,10003x13|a=10019x12,10022x13,10023x1 \\
        pos_before=0 limit=200 note=waterfall_sum3

    (the trader actually emits `orders=10023x26` instead of `price=...,qty=...` —
    handled).

Outputs (always written to runs/probes/):
    diff_table.csv      one row per (eid, ts, symbol) with columns for python,
                        rust, and official fill counts/quantities
    diff_summary.md     human-readable section per eid

Pure-stdlib + (optional) pandas. Works without pandas.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# PROBE line parsing
# ---------------------------------------------------------------------------

_PROBE_LINE_RE = re.compile(r"^PROBE\s+(.*)$")


def _split_probe_kv(payload: str) -> dict[str, str]:
    """Split a PROBE payload like 'eid=E05 ts=2000 product=H action=BUY orders=10023x26 book=... pos_before=0 limit=200 note=foo' into a dict.

    Tokens are separated by whitespace, but `book=...` and `note=...` may carry
    spaces; the trader currently doesn't, but be defensive: we split on the
    fixed key list.
    """
    keys = [
        "eid",
        "ts",
        "product",
        "action",
        "orders",
        "book",
        "pos_before",
        "limit",
        "note",
    ]
    # Find each `key=` position and slice between them.
    positions: list[tuple[str, int]] = []
    for k in keys:
        m = re.search(rf"(?:^|\s){re.escape(k)}=", payload)
        if m:
            positions.append((k, m.start() + (1 if m.group(0).startswith(" ") else 0)))
    positions.sort(key=lambda x: x[1])
    out: dict[str, str] = {}
    for i, (k, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(payload)
        seg = payload[start:end].strip()
        if seg.startswith(k + "="):
            out[k] = seg[len(k) + 1 :].strip()
    return out


def parse_probe_lines(text: str, source: str) -> list[dict[str, Any]]:
    """Extract PROBE events from a chunk of text (raw stdout or lambdaLog
    concatenation). One row per PROBE line."""
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("PROBE"):
            continue
        m = _PROBE_LINE_RE.match(line)
        if not m:
            continue
        kv = _split_probe_kv(m.group(1))
        if not kv.get("eid"):
            continue
        try:
            ts = int(kv.get("ts", "0"))
        except ValueError:
            ts = 0
        try:
            pos_before = int(kv.get("pos_before", "0"))
        except ValueError:
            pos_before = 0
        try:
            limit = int(kv.get("limit", "0"))
        except ValueError:
            limit = 0
        events.append(
            {
                "source": source,
                "eid": kv.get("eid", ""),
                "ts": ts,
                "product": kv.get("product", ""),
                "action": kv.get("action", ""),
                "orders_requested": kv.get("orders", ""),
                "book_snapshot": kv.get("book", ""),
                "pos_before": pos_before,
                "limit": limit,
                "note": kv.get("note", ""),
            }
        )
    return events


# ---------------------------------------------------------------------------
# Fill parsing — three input shapes:
#   1) IMC-format JSON  (rust BT submission.log; official IMC log)
#   2) prosperity4bt 3-section text log (Sandbox logs / Activities log / Trade History)
# ---------------------------------------------------------------------------


def _classify_side(buyer: str, seller: str) -> str:
    """Map (buyer, seller) -> SUBMISSION_BUY / SUBMISSION_SELL / EXTERNAL."""
    if buyer == "SUBMISSION":
        return "SUBMISSION_BUY"
    if seller == "SUBMISSION":
        return "SUBMISSION_SELL"
    return "EXTERNAL"


def _trade_to_row(t: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "source": source,
        "ts": int(t.get("timestamp", 0)),
        "symbol": str(t.get("symbol", "")),
        "side": _classify_side(str(t.get("buyer", "")), str(t.get("seller", ""))),
        "price": float(t.get("price", 0)),
        "qty": int(t.get("quantity", 0)),
    }


def parse_fills_imc_json(path: Path, source: str) -> tuple[list[dict[str, Any]], str]:
    """Parse an IMC-format JSON log. Returns (fills, lambda_log_text)."""
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: not valid JSON ({exc})") from exc
    fills = [_trade_to_row(t, source) for t in data.get("tradeHistory", [])]
    # Concatenate all lambdaLogs so we can feed them to parse_probe_lines.
    lambda_chunks: list[str] = []
    for log_entry in data.get("logs", []):
        text = log_entry.get("lambdaLog") or ""
        if text:
            lambda_chunks.append(text)
    return fills, "\n".join(lambda_chunks)


_PYBT_SECTION_RE = re.compile(r"^([A-Za-z][A-Za-z ]+):\s*$", re.MULTILINE)


def parse_pybt_log(path: Path, source: str) -> tuple[list[dict[str, Any]], str]:
    """Parse the prosperity4bt 3-section text log.

    Sections:
      Sandbox logs:
        <one or more JSON objects with keys sandboxLog, lambdaLog, timestamp>
      Activities log:
        <header;values...>
      Trade History:
        <JSON array of trade objects>
    """
    raw = path.read_text(encoding="utf-8")

    # Split sections by header lines.
    headers = list(_PYBT_SECTION_RE.finditer(raw))
    sections: dict[str, str] = {}
    for i, m in enumerate(headers):
        name = m.group(1).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
        sections[name] = raw[start:end].strip()

    # Trade history section is a JSON array. prosperity4bt emits trailing
    # commas inside each trade object (Python dict syntax, not strict JSON):
    #     "quantity": 8,\n  },
    # Strip them before parsing.
    trade_text = sections.get("Trade History", "").strip()
    fills: list[dict[str, Any]] = []
    if trade_text:
        sanitized = re.sub(r",(\s*[}\]])", r"\1", trade_text)
        try:
            trades = json.loads(sanitized)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: Trade History JSON parse failed ({exc})") from exc
        for t in trades:
            fills.append(_trade_to_row(t, source))

    # Sandbox logs are a sequence of JSON objects (not an array). Each object
    # is multi-line and indented. Parse via a streaming JSONDecoder.
    sandbox_text = sections.get("Sandbox logs", "").strip()
    lambda_chunks: list[str] = []
    if sandbox_text:
        decoder = json.JSONDecoder()
        idx = 0
        n = len(sandbox_text)
        while idx < n:
            # Skip whitespace.
            while idx < n and sandbox_text[idx].isspace():
                idx += 1
            if idx >= n:
                break
            try:
                obj, end = decoder.raw_decode(sandbox_text, idx)
            except json.JSONDecodeError:
                break
            idx = end
            text = obj.get("lambdaLog") or ""
            if text:
                lambda_chunks.append(text)

    return fills, "\n".join(lambda_chunks)


# ---------------------------------------------------------------------------
# Probe schedule — derived from the trader file. We hardcode the per-eid
# (single_ts vs range, ts/start/end, product) so we know how to slice fills.
# Keep in lock-step with traders/Round3/probes/probe_v1_matching.py.
# ---------------------------------------------------------------------------


PROBE_SCHEDULE: list[dict[str, Any]] = [
    {"eid": "E00_IDLE_A", "mode": "range", "start": 0, "end": 999, "product": None},
    {"eid": "E01_CROSS_ASK_TOP", "mode": "single_ts", "ts": 1000, "product": "HYDROGEL_PACK"},
    {"eid": "E02_CROSS_BID_TOP", "mode": "single_ts", "ts": 1100, "product": "HYDROGEL_PACK"},
    {"eid": "E03_FLATTEN_H", "mode": "single_ts", "ts": 1200, "product": "HYDROGEL_PACK"},
    {"eid": "E04_CROSS_ASK_TOP_VE", "mode": "single_ts", "ts": 1400, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E05_FLATTEN_VE", "mode": "single_ts", "ts": 1500, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E06_WATERFALL_SUM3", "mode": "single_ts", "ts": 2000, "product": "HYDROGEL_PACK"},
    {"eid": "E07_WATERFALL_EXCESS", "mode": "single_ts", "ts": 2100, "product": "HYDROGEL_PACK"},
    {"eid": "E08_FLATTEN_H", "mode": "single_ts", "ts": 2200, "product": "HYDROGEL_PACK"},
    {"eid": "E09_RESTING_BELOW_BB", "mode": "range", "start": 3000, "end": 3499, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E10_RESTING_JOIN_BB", "mode": "range", "start": 3500, "end": 3999, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E11_FLATTEN_VE", "mode": "single_ts", "ts": 4000, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E12_POSLIMIT_OVER1", "mode": "single_ts", "ts": 4200, "product": "VEV_6500"},
    {"eid": "E13_POSLIMIT_EXACT", "mode": "single_ts", "ts": 4300, "product": "VEV_6500"},
    {"eid": "E14_POSLIMIT_AGG", "mode": "single_ts", "ts": 4400, "product": "VEV_6500"},
    {"eid": "E15_FLATTEN_V65", "mode": "single_ts", "ts": 4500, "product": "VEV_6500"},
    {"eid": "E16_SELFCROSS", "mode": "single_ts", "ts": 5000, "product": "VEV_6500"},
    {"eid": "E17_FLATTEN_V65", "mode": "single_ts", "ts": 5100, "product": "VEV_6500"},
    {"eid": "E18_QTY_ZERO", "mode": "single_ts", "ts": 5300, "product": "VEV_6500"},
    {"eid": "E19_DUPLICATE_BUY", "mode": "single_ts", "ts": 5400, "product": "VEV_6500"},
    {"eid": "E20_FLATTEN_V65", "mode": "single_ts", "ts": 5500, "product": "VEV_6500"},
    {"eid": "E21_PRICE_ZERO_BUY", "mode": "single_ts", "ts": 6000, "product": "VEV_6500"},
    {"eid": "E22_SELL_AT_ZERO", "mode": "single_ts", "ts": 6100, "product": "VEV_6500"},
    {"eid": "E23_FLATTEN_V65", "mode": "single_ts", "ts": 6200, "product": "VEV_6500"},
    {"eid": "E24_RESTING_ABOVE_BA", "mode": "range", "start": 7000, "end": 7499, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E25_FLATTEN_VE", "mode": "single_ts", "ts": 7500, "product": "VELVETFRUIT_EXTRACT"},
    {"eid": "E26_WIDE_RESTING_H", "mode": "range", "start": 8000, "end": 8499, "product": "HYDROGEL_PACK"},
    {"eid": "E27_FLATTEN_H", "mode": "single_ts", "ts": 8500, "product": "HYDROGEL_PACK"},
    {"eid": "E28_IDLE_END", "mode": "range", "start": 9000, "end": 9999, "product": None},
]


def _eid_range(eid_def: dict[str, Any]) -> tuple[int, int]:
    if eid_def["mode"] == "single_ts":
        ts = int(eid_def["ts"])
        return (ts, ts)
    return (int(eid_def["start"]), int(eid_def["end"]))


# ---------------------------------------------------------------------------
# Fill aggregation per eid, per source
# ---------------------------------------------------------------------------


def aggregate_fills_by_eid(
    fills: list[dict[str, Any]], schedule: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """For each eid in the schedule, collect SUBMISSION-side fills whose ts
    falls inside the eid's range AND whose symbol matches the eid's product
    (or any symbol when product is None).

    Returns: eid -> {"buy_qty": int, "sell_qty": int, "fills": [row...]}
    """
    out: dict[str, dict[str, Any]] = {}
    for eid_def in schedule:
        lo, hi = _eid_range(eid_def)
        prod = eid_def.get("product")
        bucket: list[dict[str, Any]] = []
        for f in fills:
            if f["side"] == "EXTERNAL":
                continue
            if f["ts"] < lo or f["ts"] > hi:
                continue
            if prod is not None and f["symbol"] != prod:
                continue
            bucket.append(f)
        buy_qty = sum(f["qty"] for f in bucket if f["side"] == "SUBMISSION_BUY")
        sell_qty = sum(f["qty"] for f in bucket if f["side"] == "SUBMISSION_SELL")
        out[eid_def["eid"]] = {
            "buy_qty": buy_qty,
            "sell_qty": sell_qty,
            "n_fills": len(bucket),
            "fills": bucket,
        }
    return out


# ---------------------------------------------------------------------------
# Diff table + summary writers
# ---------------------------------------------------------------------------


def write_diff_table(
    out_path: Path,
    schedule: list[dict[str, Any]],
    py_agg: dict[str, dict[str, Any]] | None,
    rust_agg: dict[str, dict[str, Any]] | None,
    off_agg: dict[str, dict[str, Any]] | None,
    py_events: list[dict[str, Any]] | None,
) -> int:
    """Write per-eid diff CSV. Returns number of rows where Python vs Rust
    fill aggregates disagree (used for divergence count)."""
    fieldnames = [
        "eid",
        "mode",
        "ts_or_start",
        "ts_or_end",
        "product",
        "intent_action",
        "intent_orders",
        "py_buy_qty",
        "py_sell_qty",
        "py_n_fills",
        "rust_buy_qty",
        "rust_sell_qty",
        "rust_n_fills",
        "off_buy_qty",
        "off_sell_qty",
        "off_n_fills",
        "divergence_py_vs_rust",
        "divergence_local_vs_official",
        # Fill-shape divergence: differs from the qty-based flags above when
        # the *totals* match but the per-fill tuple list differs (e.g. IMC
        # emits 13@1; 4@1 while locals emit a single 17@1). Real signal for
        # matching-engine differences that the totals-only flags miss.
        "fill_shape_py_vs_rust",
        "fill_shape_local_vs_official",
    ]
    intent_lookup: dict[str, dict[str, Any]] = {}
    if py_events:
        for ev in py_events:
            intent_lookup.setdefault(ev["eid"], ev)

    divergent = 0
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for eid_def in schedule:
            eid = eid_def["eid"]
            lo, hi = _eid_range(eid_def)
            intent = intent_lookup.get(eid, {})
            py = (py_agg or {}).get(eid, {})
            rs = (rust_agg or {}).get(eid, {})
            off = (off_agg or {}).get(eid, {})

            div_pr = "n/a"
            if py and rs:
                if (
                    py.get("buy_qty") != rs.get("buy_qty")
                    or py.get("sell_qty") != rs.get("sell_qty")
                ):
                    div_pr = "yes"
                    divergent += 1
                else:
                    div_pr = "no"

            div_lo = "pending_official"
            if off:
                if (
                    py
                    and (
                        py.get("buy_qty") != off.get("buy_qty")
                        or py.get("sell_qty") != off.get("sell_qty")
                    )
                ) or (
                    rs
                    and (
                        rs.get("buy_qty") != off.get("buy_qty")
                        or rs.get("sell_qty") != off.get("sell_qty")
                    )
                ):
                    div_lo = "yes"
                else:
                    div_lo = "no"

            w.writerow(
                {
                    "eid": eid,
                    "mode": eid_def["mode"],
                    "ts_or_start": lo,
                    "ts_or_end": hi,
                    "product": eid_def.get("product") or "",
                    "intent_action": intent.get("action", ""),
                    "intent_orders": intent.get("orders_requested", ""),
                    "py_buy_qty": py.get("buy_qty", ""),
                    "py_sell_qty": py.get("sell_qty", ""),
                    "py_n_fills": py.get("n_fills", ""),
                    "rust_buy_qty": rs.get("buy_qty", ""),
                    "rust_sell_qty": rs.get("sell_qty", ""),
                    "rust_n_fills": rs.get("n_fills", ""),
                    "off_buy_qty": off.get("buy_qty", ""),
                    "off_sell_qty": off.get("sell_qty", ""),
                    "off_n_fills": off.get("n_fills", ""),
                    "divergence_py_vs_rust": div_pr,
                    "divergence_local_vs_official": div_lo,
                    "fill_shape_py_vs_rust": _fill_shape_diff(py, rs),
                    # Compare against whichever local source we have. Prefer
                    # python (it's the reference impl), fall back to rust.
                    "fill_shape_local_vs_official": _fill_shape_diff(
                        py if py else rs, off
                    ),
                }
            )
    return divergent


def _fill_signature(agg: dict[str, Any] | None) -> tuple | None:
    """Canonical fill-shape signature for cross-source comparison.

    Returns a sorted tuple of (side, symbol, qty, price, ts) for every fill,
    or None if the source had no observed events. We sort so that intra-tick
    ordering doesn't cause spurious divergence — what matters is the *set*
    of (side, symbol, qty, price, ts) emitted.
    """
    if not agg:
        return None
    fills = agg.get("fills") or []
    return tuple(
        sorted(
            (
                str(f.get("side", "")),
                str(f.get("symbol", "")),
                int(f.get("qty", 0)),
                int(round(float(f.get("price", 0)))),
                int(f.get("ts", 0)),
            )
            for f in fills
        )
    )


def _fill_shape_diff(a: dict[str, Any] | None, b: dict[str, Any] | None) -> str:
    """'yes' / 'no' / 'n/a' depending on whether two sources' fill shapes match.

    'n/a' is returned when either side is missing input. We do NOT collapse
    'both empty' into 'no' — that's a real "no shape divergence" answer.
    """
    if not a or not b:
        return "n/a"
    return "no" if _fill_signature(a) == _fill_signature(b) else "yes"


def _fmt_fills(fills: list[dict[str, Any]]) -> str:
    if not fills:
        return "(none)"
    parts = []
    for f in fills[:8]:
        parts.append(f"{f['side']} {f['symbol']} {f['qty']}@{f['price']:.0f} ts={f['ts']}")
    if len(fills) > 8:
        parts.append(f"... +{len(fills) - 8} more")
    return "; ".join(parts)


def write_diff_summary(
    out_path: Path,
    schedule: list[dict[str, Any]],
    py_agg: dict[str, dict[str, Any]] | None,
    rust_agg: dict[str, dict[str, Any]] | None,
    off_agg: dict[str, dict[str, Any]] | None,
    py_events: list[dict[str, Any]] | None,
    rust_events: list[dict[str, Any]] | None,
    off_events: list[dict[str, Any]] | None,
) -> None:
    intent_lookup: dict[str, dict[str, Any]] = {}
    for src in (py_events or []), (rust_events or []), (off_events or []):
        for ev in src:
            intent_lookup.setdefault(ev["eid"], ev)

    lines: list[str] = []
    lines.append("# Probe diff summary\n")
    lines.append(
        "Per-eid 3-way comparison of intent vs SUBMISSION-side fills across\n"
        "Python BT, Rust BT, and (optionally) the official IMC log.\n"
    )
    for eid_def in schedule:
        eid = eid_def["eid"]
        lo, hi = _eid_range(eid_def)
        intent = intent_lookup.get(eid, {})
        py = (py_agg or {}).get(eid, {})
        rs = (rust_agg or {}).get(eid, {})
        off = (off_agg or {}).get(eid, {})

        if py and rs:
            if (
                py.get("buy_qty") == rs.get("buy_qty")
                and py.get("sell_qty") == rs.get("sell_qty")
            ):
                tag_pr = "no"
            else:
                tag_pr = "yes"
        else:
            tag_pr = "missing_input"
        if off:
            if (
                (py and (py.get("buy_qty") != off.get("buy_qty") or py.get("sell_qty") != off.get("sell_qty")))
                or (rs and (rs.get("buy_qty") != off.get("buy_qty") or rs.get("sell_qty") != off.get("sell_qty")))
            ):
                tag_lo = "yes"
            else:
                tag_lo = "no"
        else:
            tag_lo = "pending_official"

        lines.append(f"\n## {eid} ({eid_def['mode']}, {lo}..{hi}, product={eid_def.get('product') or 'NONE'})")
        lines.append(f"- intent: action={intent.get('action', '?')}, orders={intent.get('orders_requested', '?')}, note={intent.get('note', '')}")
        lines.append(f"- python:   buy={py.get('buy_qty', 'n/a')} sell={py.get('sell_qty', 'n/a')} n_fills={py.get('n_fills', 'n/a')} | {_fmt_fills(py.get('fills', []) if py else [])}")
        lines.append(f"- rust:     buy={rs.get('buy_qty', 'n/a')} sell={rs.get('sell_qty', 'n/a')} n_fills={rs.get('n_fills', 'n/a')} | {_fmt_fills(rs.get('fills', []) if rs else [])}")
        lines.append(f"- official: buy={off.get('buy_qty', 'pending')} sell={off.get('sell_qty', 'pending')} n_fills={off.get('n_fills', 'pending')} | {_fmt_fills(off.get('fills', []) if off else [])}")
        lines.append(f"- divergence_py_vs_rust: {tag_pr}")
        lines.append(f"- divergence_local_vs_official: {tag_lo}")
        # Fill-shape flags catch matching-engine differences where totals
        # agree but per-fill granularity differs (e.g. official splits
        # 17@1 into 13@1 + 4@1). Without these, such cases silently
        # report "no divergence" above.
        lines.append(
            f"- fill_shape_py_vs_rust: {_fill_shape_diff(py, rs)}"
        )
        lines.append(
            f"- fill_shape_local_vs_official: "
            f"{_fill_shape_diff(py if py else rs, off)}"
        )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read(path_str: str | None) -> str | None:
    if not path_str:
        return None
    p = Path(path_str)
    if not p.exists():
        print(f"[probe_analyze] WARN: {p} does not exist; skipping", file=sys.stderr)
        return None
    return p.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diff PROBE events + fills across backtesters.")
    ap.add_argument("--python-stdout", default=None)
    ap.add_argument("--python-json", default=None)
    ap.add_argument("--rust-stdout", default=None)
    ap.add_argument("--rust-json", default=None)
    ap.add_argument("--official-log", default=None)
    # Default to <repo_root>/runs/probes so the script is portable across
    # checkouts. Override with --out-dir for ad-hoc runs (e.g. v2 probes).
    _default_out_dir = Path(__file__).resolve().parent.parent / "runs" / "probes"
    ap.add_argument(
        "--out-dir",
        default=str(_default_out_dir),
    )
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Probe events ------------------------------------------------------
    py_events: list[dict[str, Any]] = []
    rust_events: list[dict[str, Any]] = []
    off_events: list[dict[str, Any]] = []

    py_stdout_text = _read(args.python_stdout)
    if py_stdout_text:
        py_events.extend(parse_probe_lines(py_stdout_text, "python_stdout"))

    py_fills: list[dict[str, Any]] = []
    if args.python_json:
        path = Path(args.python_json)
        if path.exists():
            try:
                py_fills, py_lambda = parse_pybt_log(path, "python_bt")
                py_events.extend(parse_probe_lines(py_lambda, "python_lambda"))
            except ValueError as exc:
                print(f"[probe_analyze] failed to parse {path}: {exc}", file=sys.stderr)

    rust_stdout_text = _read(args.rust_stdout)
    if rust_stdout_text:
        rust_events.extend(parse_probe_lines(rust_stdout_text, "rust_stdout"))

    rust_fills: list[dict[str, Any]] = []
    if args.rust_json:
        path = Path(args.rust_json)
        if path.exists():
            try:
                rust_fills, rust_lambda = parse_fills_imc_json(path, "rust_bt")
                rust_events.extend(parse_probe_lines(rust_lambda, "rust_lambda"))
            except ValueError as exc:
                print(f"[probe_analyze] failed to parse {path}: {exc}", file=sys.stderr)

    off_fills: list[dict[str, Any]] = []
    if args.official_log:
        path = Path(args.official_log)
        if path.exists():
            try:
                off_fills, off_lambda = parse_fills_imc_json(path, "official")
                off_events.extend(parse_probe_lines(off_lambda, "official_lambda"))
            except ValueError as exc:
                print(f"[probe_analyze] failed to parse {path}: {exc}", file=sys.stderr)

    # ---- Aggregate fills per eid ------------------------------------------
    py_agg = aggregate_fills_by_eid(py_fills, PROBE_SCHEDULE) if py_fills else None
    rust_agg = aggregate_fills_by_eid(rust_fills, PROBE_SCHEDULE) if rust_fills else None
    off_agg = aggregate_fills_by_eid(off_fills, PROBE_SCHEDULE) if off_fills else None

    # ---- Diff table & summary --------------------------------------------
    diff_csv = out_dir / "diff_table.csv"
    diff_md = out_dir / "diff_summary.md"
    n_div = write_diff_table(
        diff_csv, PROBE_SCHEDULE, py_agg, rust_agg, off_agg, py_events
    )
    write_diff_summary(
        diff_md, PROBE_SCHEDULE, py_agg, rust_agg, off_agg, py_events, rust_events, off_events
    )

    # ---- Console summary ---------------------------------------------------
    n_py_probe = len(py_events)
    n_rust_probe = len(rust_events)
    n_off_probe = len(off_events)
    n_py_subs = sum(1 for f in py_fills if f["side"] != "EXTERNAL")
    n_rust_subs = sum(1 for f in rust_fills if f["side"] != "EXTERNAL")
    n_off_subs = sum(1 for f in off_fills if f["side"] != "EXTERNAL")

    print("=" * 60)
    print(f"PROBE events: python={n_py_probe} rust={n_rust_probe} official={n_off_probe}")
    print(f"SUBMISSION fills: python={n_py_subs} rust={n_rust_subs} official={n_off_subs}")
    print(f"Diverging eids (python vs rust): {n_div}")
    print(f"Diff table: {diff_csv}")
    print(f"Diff summary: {diff_md}")
    print("=" * 60)

    # Print first 5 diverging rows for the operator.
    if py_agg and rust_agg:
        diverging: list[str] = []
        for eid_def in PROBE_SCHEDULE:
            eid = eid_def["eid"]
            py = py_agg.get(eid, {})
            rs = rust_agg.get(eid, {})
            if (
                py.get("buy_qty") != rs.get("buy_qty")
                or py.get("sell_qty") != rs.get("sell_qty")
            ):
                diverging.append(
                    f"  {eid}: py(b={py.get('buy_qty')}, s={py.get('sell_qty')}) "
                    f"vs rust(b={rs.get('buy_qty')}, s={rs.get('sell_qty')})"
                )
        if diverging:
            print("First diverging eids:")
            for line in diverging[:5]:
                print(line)
        else:
            print("No fill divergence between python and rust.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
