import importlib.util
import json
import os
from pathlib import Path


BASE = (
    Path(__file__).resolve().parents[3]
    / "traders"
    / "Round1"
    / "active"
    / "round1_overhaul_v63.py"
)
spec = importlib.util.spec_from_file_location("base_v63", BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
orig_ash_fair_and_state = base.ash_fair_and_state
orig_pepper_state_and_fair = base.pepper_state_and_fair


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


ASH_ML_SCALE = env_float("ASH_ML_SCALE", 0.0)
ASH_ML_QUOTE_SCALE = env_float("ASH_ML_QUOTE_SCALE", 0.0)
PEPPER_ML_SCALE = env_float("PEPPER_ML_SCALE", 0.0)


ASH_INTERCEPT = 0.070005
ASH_COEFS = {
    "spread": -0.002692,
    "anchor_gap": 0.794834,
    "micro_delta": 0.025834,
    "mm10_gap": -0.345695,
    "wall_gap": 0.213391,
    "ret1": -0.123673,
    "fair_gap": 1.128132,
    "quote_gap": 0.369894,
    "progress": -0.050365,
    "shock": -0.014969,
}

PEPPER_INTERCEPT = -0.521603
PEPPER_COEFS = {
    "spread": 0.005889,
    "residual": 0.075927,
    "carry_left": 0.000846,
    "trade_ema": -0.015519,
    "micro_delta": 0.145940,
    "mm10_gap": -0.087498,
    "wall_gap": 0.121904,
    "ret1": -0.069926,
    "fair_gap": 0.843411,
    "progress": 0.786157,
    "mode_opening": -0.010368,
    "mode_discount": -0.383597,
    "mode_overheated": -0.827176,
}


def ash_fair_and_state(depth, ash_state):
    base_fair, ash_state, diag = orig_ash_fair_and_state(depth, ash_state)
    mid = float(diag["mid"])
    micro = base.microprice(depth) or mid
    mm10 = base.mm10_mid(depth) or mid
    wall = base.wall_mid(depth) or mid
    progress = base.clamp(base_fair and ash_state.get("last_mid", mid) and 0.0, 0.0, 1.0)
    # Use the current tick timestamp-independent fair features only.
    features = {
        "spread": (base.best_ask(depth) - base.best_bid(depth))
        if base.best_bid(depth) is not None and base.best_ask(depth) is not None
        else 0.0,
        "anchor_gap": mid - base.ASH_ANCHOR,
        "micro_delta": micro - mid,
        "mm10_gap": mm10 - mid,
        "wall_gap": wall - mid,
        "ret1": float(diag["ret1"]),
        "fair_gap": base_fair - mid,
        "quote_gap": float(diag["quote_fair"]) - mid,
        "progress": progress,
        "shock": float(diag["shock"]),
    }
    predicted_move = ASH_INTERCEPT + sum(ASH_COEFS[key] * value for key, value in features.items())
    model_fair = mid + predicted_move
    adjusted_fair = base_fair + ASH_ML_SCALE * (model_fair - base_fair)
    base_quote = float(diag["quote_fair"])
    adjusted_quote = base_quote + ASH_ML_QUOTE_SCALE * (model_fair - base_quote)
    diag["quote_fair"] = adjusted_quote
    return adjusted_fair, ash_state, diag


def pepper_state_and_fair(depth, pepper_state, market_trades, timestamp):
    base_fair, mode, pepper_state, diag = orig_pepper_state_and_fair(
        depth,
        pepper_state,
        market_trades,
        timestamp,
    )
    mid = float(diag["mid"])
    micro = base.microprice(depth) or mid
    mm10 = base.mm10_mid(depth) or mid
    wall = base.wall_mid(depth) or mid
    features = {
        "spread": (base.best_ask(depth) - base.best_bid(depth))
        if base.best_bid(depth) is not None and base.best_ask(depth) is not None
        else 0.0,
        "residual": float(diag["residual"]),
        "carry_left": float(diag["carry_left"]),
        "trade_ema": float(diag["trade_ema"]),
        "micro_delta": micro - mid,
        "mm10_gap": mm10 - mid,
        "wall_gap": wall - mid,
        "ret1": mid - float(pepper_state.get("last_mid", mid)),
        "fair_gap": base_fair - mid,
        "progress": float(diag["progress"]),
        "mode_opening": 1.0 if mode == "opening" else 0.0,
        "mode_discount": 1.0 if mode == "discount" else 0.0,
        "mode_overheated": 1.0 if mode == "overheated" else 0.0,
    }
    predicted_move = PEPPER_INTERCEPT + sum(
        PEPPER_COEFS[key] * value for key, value in features.items()
    )
    model_fair = mid + predicted_move
    adjusted_fair = base_fair + PEPPER_ML_SCALE * (model_fair - base_fair)
    return adjusted_fair, mode, pepper_state, diag


base.ash_fair_and_state = ash_fair_and_state
base.pepper_state_and_fair = pepper_state_and_fair

Trader = base.Trader
