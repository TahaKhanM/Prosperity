# Round 4 — "The More The Merrier" (Salvinar)

> Source-grounded transcription of the official Round 4 Notion-wiki briefing
> shipped in `Data/ROUND 4 Context.txt`. Treat this file as the primary
> written-doc source for Round 4. Anything in the ARIA uplink or hint cards
> that contradicts this file loses.

## Algorithm status

- Status: N/A
- Recent upload: N/A
- Open Challenge: yes

## Round summary

For this second round of the Great Orbital Ascension Trials (GOAT), the
Frontier Trade Watch (FTW) has disclosed information about the counterparties
active in the market. Their IDs have been added to the historical trade data
available in the Data Capsule.

You will continue trading **Hydrogel Packs** (`HYDROGEL_PACK`),
**Velvetfruit Extract** (`VELVETFRUIT_EXTRACT`), and **10 Velvetfruit Extract
Vouchers** (`VEV_<K>`). This time, however, having insight into your
counterparties — and understanding what defines their trading behavior and the
unique opportunities they bring — could shift the balance for teams that know
how to separate profit from pretense.

In addition to your algorithmic trading activities, you will also have the
opportunity to **manually trade the Aether Crystal**, along with a collection
of option contracts based on it. Some of these contracts are more exotic than
others. You must determine a strategy that turns this one-time opportunity
into profit.

> **Be aware that these exotic options operate independently from your
> algorithmic trading activities.**

## Round objective

1. Optimise your Python program to trade `HYDROGEL_PACK`,
   `VELVETFRUIT_EXTRACT`, and `VELVETFRUIT_EXTRACT_VOUCHER`, incorporating the
   newly disclosed counterparty information into your strategy.
2. Select from the available Aether Crystal and corresponding option contracts,
   and submit your orders to generate additional profit.

## Algorithmic trading challenge: "Hello, I'm Mark"

The products are the same as in Round 3 (`HYDROGEL_PACK`,
`VELVETFRUIT_EXTRACT`, and 10 `VEV_<K>` options), but now you have
counterparty information available. That is, you can identify every other
participant in the market and study their behavior.

In the data model described in *Appendix B: datamodel.py file* in 💻 *Writing
an Algorithm in Python*, you will find the `Trade` class:

```python
class Trade:
    def __init__(self, symbol: Symbol, price: int, quantity: int,
                 buyer: UserId = None, seller: UserId = None,
                 timestamp: int = 0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp
        # Some methods
```

For previous Rounds 1, 2, 3, the `self.buyer` and `self.seller` fields were
always `None` because no counterparty information was available. With increased
transparency in the market, however, these fields **now represent the names of
the participants**. Use this information however you see fit and refine your
strategy with the extra visibility.

### Position limits (unchanged from Round 3)

- `HYDROGEL_PACK`: **200**
- `VELVETFRUIT_EXTRACT`: **200**
- `VELVETFRUIT_EXTRACT_VOUCHER`: **300** for each of the 10 vouchers

### Voucher / TTE rules

All Velvetfruit Extract Vouchers have a Time-To-Expiry (TTE) of **7
Solvenarian days, starting from day 1**. The available VEVs are:

| Symbol | Strike (K) |
|---|---|
| `VEV_4000` | 4000 |
| `VEV_4500` | 4500 |
| `VEV_5000` | 5000 |
| `VEV_5100` | 5100 |
| `VEV_5200` | 5200 |
| `VEV_5300` | 5300 |
| `VEV_5400` | 5400 |
| `VEV_5500` | 5500 |
| `VEV_6000` | 6000 |
| `VEV_6500` | 6500 |

> Example (building on Round 3): `VEV_5000` is an option with strike 5000,
> has **TTE = 4 days in Round 4**, and a position limit of 300.

So in Round 4 the TTE schedule is:

| Source | TTE (days) |
|---|---|
| Round 4 historical day 1 (`prices_round_4_day_1.csv`) | 7 |
| Round 4 historical day 2 (`prices_round_4_day_2.csv`) | 6 |
| Round 4 historical day 3 (`prices_round_4_day_3.csv`) | 5 |
| Round 4 live | **4** |

Settlement: cash at `max(S_T - K, 0)` at expiry. Vouchers cannot be exercised
early.

## Counterparty data (disclosed)

The FTW has identified your trading counterparties as products of several
local neuro-robotics research programs. They are all named **"Mark"** followed
by a number. These IDs have been added to the historical trade data in the
Data Capsule.

Use this information to re-evaluate your strategy for trading Hydrogel Packs,
Velvetfruit Extract, and the VEVs.

The 7 distinct counterparties observed in the Round 4 historical
`trades_round_4_day_*.csv` files are:

```
Mark 01    Mark 14    Mark 22    Mark 38    Mark 49    Mark 55    Mark 67
```

Mark 67 only ever appears as a buyer in the historical data. Mark 22 and
Mark 49 are very low volume. Mark 01 is the most active (469–649 trades/day).
Initial classifications live in
`prosperity-research/03_eda/round4/counterparty_by_product.md`.

## Manual trading: Aether Crystal options

Round 4 introduces a one-shot **manual** Aether Crystal options book.
**This is independent of the algorithmic trader.**

You may trade the Aether Crystal directly, but a set of option contracts is
also available, including **standard vanilla options** as well as several
**exotic options**. Key details for the exotic contracts (per the official
brief):

### Chooser option

- **Strike**: 50 ZYREX
- **Expiry**: 21 Solvenarian days
- **Mechanic**: After **14 Solvenarian days**, the buyer decides whether the
  contract becomes a call or a put. During this competition, the chooser
  contract will automatically convert to whichever side is **in the money** at
  the simulated decision point.
- After the type is fixed, behaves like a vanilla option for the remaining
  time to expiry.

### Binary put

- **Strike**: 40 XIRECS
- **Expiry**: 21 Solvenarian days
- **Payoff**: All-or-nothing.
  - If `S_T < 40`: pays a fixed **10 XIRECS**.
  - If `S_T ≥ 40`: pays nothing.

### Knockout put (down-and-out put)

- **Strike**: 45 ZYREX
- **Barrier**: 35 ZYREX
- **Expiry**: 21 Solvenarian days
- **Mechanic**: Settles as a regular put with strike 45 **as long as the price
  of the Aether Crystal never falls below the barrier (35) during the
  contract's lifetime, not even momentarily**. If the barrier is breached at
  any tick, the contract is **immediately knocked out and becomes worthless**.

### Vanillas

In addition, standard vanilla call and put options on the Aether Crystal are
available across multiple strikes (full set surfaced in the Manual Challenge
Overview window in the Prosperity UI; manual is independent of algo so the
exact list is not exposed in CSVs).

### Manual trading interface

- The Manual Challenge Overview window is where you submit your manual
  trading input.
- You may adjust your submission as long as time remains in this round.
- The **final manual submission before the timer expires counts** as your
  official entry.
- The only practical limitation is **available volume** per contract. Other
  than that it is entirely up to you which contracts to incorporate.

## Reminders

- Round duration: 48 hours (GOAT-phase rule).
- PnL was reset at the start of Round 3; Round 4 PnL accumulates on the same
  ledger as Round 3.
- Last submission of the round wins.
- Hosted execution is stateless across ticks. Use `traderData` (≤ 50,000 chars).
- `OrderDepth.sell_orders` volumes are negative.
- Worst-case position-limit breach in a single tick rejects **all** orders for
  that product in that tick. Size defensively.

## Currency naming

The wiki uses **XIRECS** but the ARIA uplink and hint cards drift between
"Zyrex / ZYREX / XYX". They all refer to the same in-game currency
(`XIRECS` is canonical from the written doc; trades CSV uses `XIRECS` too).

## Naming reference: settings vs uplink drift

| Wiki / written doc | Uplink / transcript variants |
|---|---|
| Salvinar | Salvinar / Solvenar |
| XIRECS | Zyrex / ZYREX / XYX / Zyre |
| Mark NN | Mark NN (consistent) |
| Aether Crystal | Aether Crystal / Ether Crystal |

Prefer the wiki naming when writing code or context.
