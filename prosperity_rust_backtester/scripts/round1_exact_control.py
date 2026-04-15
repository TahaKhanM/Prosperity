#!/usr/bin/env python3
"""Exact-control search for Round 1 using the Rust backtester's tick matcher."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "datasets" / "round1"

ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"
PRODUCTS = (ASH, PEPPER)
LIMIT = 80
TRADE_MATCH_MODE = "all"
QUEUE_PENETRATION = 1.0


@dataclass(frozen=True)
class MarketTrade:
    price: int
    quantity: int


@dataclass(frozen=True)
class Tick:
    timestamp: int
    bids: Tuple[Tuple[int, int], ...]
    asks: Tuple[Tuple[int, int], ...]
    market_trades: Tuple[MarketTrade, ...]
    mark: float


@dataclass(frozen=True)
class LegTemplate:
    side: str
    mode: str
    size: int


@dataclass(frozen=True)
class ActionTemplate:
    name: str
    legs: Tuple[LegTemplate, ...]


@dataclass(frozen=True)
class MaterializedLeg:
    side: str
    price: int
    quantity: int


def python_round_to_i64(value: float) -> int:
    return int(round(value))


def queue_penetration_available(quantity: int, queue_penetration: float) -> int:
    raw = quantity * max(0.0, queue_penetration)
    available = python_round_to_i64(raw)
    if quantity > 0 and queue_penetration > 0.0 and available == 0:
        available = 1
    return max(0, available)


def eligible_trade_price(order_price: int, trade_price: int, quantity: int, mode: str) -> bool:
    if mode == "none":
        return False
    if quantity > 0:
        if mode == "all":
            return trade_price <= order_price
        return trade_price < order_price
    if quantity < 0:
        if mode == "all":
            return trade_price >= order_price
        return trade_price > order_price
    return False


def load_ticks(product: str, day: int) -> List[Tick]:
    price_path = DATASET_ROOT / f"prices_round_1_day_{day}.csv"
    trade_path = DATASET_ROOT / f"trades_round_1_day_{day}.csv"

    trades_by_ts: Dict[int, List[MarketTrade]] = {}
    with trade_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["symbol"] != product:
                continue
            ts = int(float(row["timestamp"]))
            price = int(float(row["price"]))
            qty = int(float(row["quantity"]))
            trades_by_ts.setdefault(ts, []).append(MarketTrade(price=price, quantity=qty))

    ticks: List[Tick] = []
    with price_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["product"] != product:
                continue
            ts = int(float(row["timestamp"]))
            bids: List[Tuple[int, int]] = []
            asks: List[Tuple[int, int]] = []
            for idx in range(1, 4):
                bid_price = row.get(f"bid_price_{idx}") or ""
                bid_volume = row.get(f"bid_volume_{idx}") or ""
                ask_price = row.get(f"ask_price_{idx}") or ""
                ask_volume = row.get(f"ask_volume_{idx}") or ""
                if bid_price and bid_volume:
                    bids.append((int(float(bid_price)), int(float(bid_volume))))
                if ask_price and ask_volume:
                    asks.append((int(float(ask_price)), int(float(ask_volume))))
            bids.sort(key=lambda item: item[0], reverse=True)
            asks.sort(key=lambda item: item[0])
            if not bids and not asks:
                continue
            if bids and asks:
                mark = (bids[0][0] + asks[0][0]) / 2.0
            elif bids:
                mark = float(bids[0][0])
            else:
                mark = float(asks[0][0])
            ticks.append(
                Tick(
                    timestamp=ts,
                    bids=tuple(bids),
                    asks=tuple(asks),
                    market_trades=tuple(trades_by_ts.get(ts, [])),
                    mark=mark,
                )
            )
    return ticks


def best_bid(tick: Tick) -> Optional[int]:
    return tick.bids[0][0] if tick.bids else None


def best_ask(tick: Tick) -> Optional[int]:
    return tick.asks[0][0] if tick.asks else None


def nth_bid(tick: Tick, idx: int) -> Optional[int]:
    return tick.bids[idx][0] if idx < len(tick.bids) else None


def nth_ask(tick: Tick, idx: int) -> Optional[int]:
    return tick.asks[idx][0] if idx < len(tick.asks) else None


def leg_price(tick: Tick, side: str, mode: str) -> Optional[int]:
    bid = best_bid(tick)
    ask = best_ask(tick)
    if side == "buy":
        if mode == "deep":
            return None if bid is None else bid - 1
        if mode == "join":
            return bid
        if mode == "inside":
            if bid is None or ask is None:
                return None
            inside = bid + 1
            return inside if inside < ask else None
        if mode == "take1":
            return ask
        if mode == "take2":
            return nth_ask(tick, 1) or ask
        if mode == "take3":
            return nth_ask(tick, 2) or nth_ask(tick, 1) or ask
        raise ValueError(f"unknown buy mode: {mode}")
    if mode == "deep":
        return None if ask is None else ask + 1
    if mode == "join":
        return ask
    if mode == "inside":
        if bid is None or ask is None:
            return None
        inside = ask - 1
        return inside if inside > bid else None
    if mode == "take1":
        return bid
    if mode == "take2":
        return nth_bid(tick, 1) or bid
    if mode == "take3":
        return nth_bid(tick, 2) or nth_bid(tick, 1) or bid
    raise ValueError(f"unknown sell mode: {mode}")


def materialize_action(tick: Tick, action: ActionTemplate) -> Optional[List[MaterializedLeg]]:
    legs: List[MaterializedLeg] = []
    buy_price: Optional[int] = None
    sell_price: Optional[int] = None
    for leg in action.legs:
        price = leg_price(tick, leg.side, leg.mode)
        if price is None:
            return None
        if leg.side == "buy":
            buy_price = price
            qty = leg.size
        else:
            sell_price = price
            qty = leg.size
        legs.append(MaterializedLeg(side=leg.side, price=price, quantity=qty))
    if buy_price is not None and sell_price is not None and buy_price >= sell_price:
        return None
    return legs


def simulate_action(
    tick: Tick,
    position: int,
    legs: Sequence[MaterializedLeg],
    trade_match_mode: str = TRADE_MATCH_MODE,
    queue_penetration: float = QUEUE_PENETRATION,
) -> Tuple[int, float]:
    bids = [[price, volume] for price, volume in tick.bids]
    asks = [[price, volume] for price, volume in tick.asks]
    market_available = [
        [trade.price, queue_penetration_available(trade.quantity, queue_penetration)]
        for trade in tick.market_trades
    ]
    buy_queue_remaining = {price: volume for price, volume in tick.bids if volume > 0}
    sell_queue_remaining = {price: volume for price, volume in tick.asks if volume > 0}
    cash_delta = 0.0
    pos = position

    for leg in legs:
        remaining = leg.quantity if leg.side == "buy" else -leg.quantity
        if remaining > 0:
            for level in asks:
                if remaining <= 0:
                    break
                level_price, level_volume = level
                if level_price > leg.price or level_volume <= 0:
                    continue
                fill = min(remaining, level_volume)
                pos += fill
                cash_delta -= level_price * fill
                level[1] -= fill
                remaining -= fill
        elif remaining < 0:
            for level in bids:
                if remaining >= 0:
                    break
                level_price, level_volume = level
                if level_price < leg.price or level_volume <= 0:
                    continue
                fill = min(-remaining, level_volume)
                pos -= fill
                cash_delta += level_price * fill
                level[1] -= fill
                remaining += fill

        if remaining == 0 or trade_match_mode == "none":
            continue

        for trade in market_available:
            trade_price, trade_quantity = trade
            if remaining == 0:
                break
            if trade_quantity <= 0:
                continue
            if not eligible_trade_price(leg.price, trade_price, remaining, trade_match_mode):
                continue
            if remaining > 0 and trade_price == leg.price:
                ahead = buy_queue_remaining.get(leg.price)
                if ahead is not None:
                    consumed = min(trade_quantity, ahead)
                    trade[1] -= consumed
                    ahead -= consumed
                    if ahead <= 0:
                        buy_queue_remaining.pop(leg.price, None)
                    else:
                        buy_queue_remaining[leg.price] = ahead
            elif remaining < 0 and trade_price == leg.price:
                ahead = sell_queue_remaining.get(leg.price)
                if ahead is not None:
                    consumed = min(trade_quantity, ahead)
                    trade[1] -= consumed
                    ahead -= consumed
                    if ahead <= 0:
                        sell_queue_remaining.pop(leg.price, None)
                    else:
                        sell_queue_remaining[leg.price] = ahead
            if trade[1] <= 0:
                continue

            fill = min(abs(remaining), trade[1])
            if remaining > 0:
                pos += fill
                cash_delta -= leg.price * fill
                remaining -= fill
            else:
                pos -= fill
                cash_delta += leg.price * fill
                remaining += fill
            trade[1] -= fill

    if pos < -LIMIT or pos > LIMIT:
        raise ValueError(f"position limit violated: {pos}")
    return pos, cash_delta


ASH_ACTIONS: Tuple[ActionTemplate, ...] = (
    ActionTemplate("hold", ()),
    ActionTemplate("mm_join_12", (LegTemplate("buy", "join", 12), LegTemplate("sell", "join", 12))),
    ActionTemplate("mm_inside_12", (LegTemplate("buy", "inside", 12), LegTemplate("sell", "inside", 12))),
    ActionTemplate("mm_inside_20", (LegTemplate("buy", "inside", 20), LegTemplate("sell", "inside", 20))),
    ActionTemplate("buy_join_16", (LegTemplate("buy", "join", 16),)),
    ActionTemplate("sell_join_16", (LegTemplate("sell", "join", 16),)),
    ActionTemplate("buy_inside_20", (LegTemplate("buy", "inside", 20),)),
    ActionTemplate("sell_inside_20", (LegTemplate("sell", "inside", 20),)),
    ActionTemplate("buy_take1_16", (LegTemplate("buy", "take1", 16),)),
    ActionTemplate("sell_take1_16", (LegTemplate("sell", "take1", 16),)),
    ActionTemplate("buy_take2_32", (LegTemplate("buy", "take2", 32),)),
    ActionTemplate("sell_take2_32", (LegTemplate("sell", "take2", 32),)),
    ActionTemplate("buy_take1_sell_inside", (LegTemplate("buy", "take1", 16), LegTemplate("sell", "inside", 12))),
    ActionTemplate("sell_take1_buy_inside", (LegTemplate("sell", "take1", 16), LegTemplate("buy", "inside", 12))),
    ActionTemplate("buy_deep_16", (LegTemplate("buy", "deep", 16),)),
    ActionTemplate("sell_deep_16", (LegTemplate("sell", "deep", 16),)),
)


PEPPER_ACTIONS: Tuple[ActionTemplate, ...] = (
    ActionTemplate("hold", ()),
    ActionTemplate("carry_join", (LegTemplate("buy", "join", 12), LegTemplate("sell", "inside", 4))),
    ActionTemplate("carry_inside", (LegTemplate("buy", "inside", 12), LegTemplate("sell", "inside", 4))),
    ActionTemplate("carry_inside_big", (LegTemplate("buy", "inside", 20), LegTemplate("sell", "inside", 8))),
    ActionTemplate("buy_join_12", (LegTemplate("buy", "join", 12),)),
    ActionTemplate("buy_inside_12", (LegTemplate("buy", "inside", 12),)),
    ActionTemplate("buy_inside_20", (LegTemplate("buy", "inside", 20),)),
    ActionTemplate("buy_take1_16", (LegTemplate("buy", "take1", 16),)),
    ActionTemplate("buy_take1_32", (LegTemplate("buy", "take1", 32),)),
    ActionTemplate("buy_take2_48", (LegTemplate("buy", "take2", 48),)),
    ActionTemplate("buy_take3_80", (LegTemplate("buy", "take3", 80),)),
    ActionTemplate("sell_inside_8", (LegTemplate("sell", "inside", 8),)),
    ActionTemplate("sell_take1_12", (LegTemplate("sell", "take1", 12),)),
    ActionTemplate("sell_take1_24", (LegTemplate("sell", "take1", 24),)),
    ActionTemplate("sell_take2_40", (LegTemplate("sell", "take2", 40),)),
    ActionTemplate("recycle_inside", (LegTemplate("buy", "join", 8), LegTemplate("sell", "inside", 12))),
    ActionTemplate("recycle_take", (LegTemplate("buy", "inside", 8), LegTemplate("sell", "take1", 16))),
    ActionTemplate("sell_deep_8", (LegTemplate("sell", "deep", 8),)),
)


def candidate_actions(product: str, position: int) -> Sequence[ActionTemplate]:
    if product == ASH:
        if position >= 50:
            return tuple(
                action
                for action in ASH_ACTIONS
                if not action.name.startswith(("buy_take2", "buy_inside_20", "buy_join_16"))
            )
        if position <= -50:
            return tuple(
                action
                for action in ASH_ACTIONS
                if not action.name.startswith(("sell_take2", "sell_inside_20", "sell_join_16"))
            )
        return ASH_ACTIONS

    if position >= 72:
        return (
            PEPPER_ACTIONS[0],
            PEPPER_ACTIONS[11],
            PEPPER_ACTIONS[12],
            PEPPER_ACTIONS[13],
            PEPPER_ACTIONS[14],
            PEPPER_ACTIONS[15],
            PEPPER_ACTIONS[16],
            PEPPER_ACTIONS[17],
        )
    if position <= 20:
        return (
            PEPPER_ACTIONS[0],
            PEPPER_ACTIONS[1],
            PEPPER_ACTIONS[2],
            PEPPER_ACTIONS[3],
            PEPPER_ACTIONS[4],
            PEPPER_ACTIONS[5],
            PEPPER_ACTIONS[6],
            PEPPER_ACTIONS[7],
            PEPPER_ACTIONS[8],
            PEPPER_ACTIONS[9],
            PEPPER_ACTIONS[10],
        )
    return PEPPER_ACTIONS


def solve_day(product: str, day: int) -> Dict[str, object]:
    ticks = load_ticks(product, day)
    if not ticks:
        raise ValueError(f"no ticks for {product} day {day}")

    terminal_mark = ticks[-1].mark
    value_next = {pos: pos * terminal_mark for pos in range(-LIMIT, LIMIT + 1)}
    choice_by_tick: List[Dict[int, Tuple[str, int]]] = []

    for tick in reversed(ticks):
        current_values: Dict[int, float] = {}
        current_choices: Dict[int, Tuple[str, int]] = {}
        for position in range(-LIMIT, LIMIT + 1):
            best_value = float("-inf")
            best_choice = ("hold", position)
            for action in candidate_actions(product, position):
                legs = materialize_action(tick, action)
                if legs is None:
                    continue
                try:
                    new_pos, cash_delta = simulate_action(tick, position, legs)
                except ValueError:
                    continue
                value = cash_delta + value_next[new_pos]
                if value > best_value:
                    best_value = value
                    best_choice = (action.name, new_pos)
            current_values[position] = best_value
            current_choices[position] = best_choice
        choice_by_tick.append(current_choices)
        value_next = current_values

    choice_by_tick.reverse()
    action_counts: Dict[str, int] = {}
    cash = 0.0
    position = 0
    trace: List[Dict[str, object]] = []
    for tick_idx, tick in enumerate(ticks):
        action_name, _ = choice_by_tick[tick_idx][position]
        action = next(action for action in candidate_actions(product, position) if action.name == action_name)
        legs = materialize_action(tick, action) or []
        new_pos, cash_delta = simulate_action(tick, position, legs)
        cash += cash_delta
        action_counts[action_name] = action_counts.get(action_name, 0) + 1
        trace.append(
            {
                "timestamp": tick.timestamp,
                "position_before": position,
                "action": action_name,
                "position_after": new_pos,
                "cash_delta": cash_delta,
                "mark": tick.mark,
                "legs": [
                    {"side": leg.side, "price": leg.price, "quantity": leg.quantity}
                    for leg in legs
                ],
            }
        )
        position = new_pos

    final_value = cash + position * terminal_mark
    return {
        "product": product,
        "day": day,
        "ticks": len(ticks),
        "final_pnl": final_value,
        "final_cash": cash,
        "final_position": position,
        "terminal_mark": terminal_mark,
        "action_counts": dict(sorted(action_counts.items(), key=lambda item: (-item[1], item[0]))),
        "trace_head": trace[:40],
        "trace_tail": trace[-40:],
    }


def solve_bundle(product: str, days: Iterable[int]) -> Dict[str, object]:
    per_day = [solve_day(product, day) for day in days]
    total = sum(float(day["final_pnl"]) for day in per_day)
    action_counts: Dict[str, int] = {}
    for day in per_day:
        for action_name, count in day["action_counts"].items():
            action_counts[action_name] = action_counts.get(action_name, 0) + int(count)
    return {
        "product": product,
        "total_pnl": total,
        "per_day": per_day,
        "action_counts": dict(sorted(action_counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=PRODUCTS)
    parser.add_argument("--days", default="-2,-1,0")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    days = [int(part) for part in args.days.split(",") if part]
    products = [args.product] if args.product else list(PRODUCTS)
    report = {product: solve_bundle(product, days) for product in products}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    for product, payload in report.items():
        print(f"\n{product}")
        print(f"  total_pnl={payload['total_pnl']:.1f}")
        print(f"  action_counts={payload['action_counts']}")
        for day in payload["per_day"]:
            print(
                f"  day={day['day']:>2} pnl={day['final_pnl']:>9.1f} "
                f"final_pos={day['final_position']:>4} top_actions={list(day['action_counts'].items())[:8]}"
            )


if __name__ == "__main__":
    main()
