def solve(bids, asks, buyback, fee=0):
    """
    bids: list of (price, volume)
    asks: list of (price, volume)
    buyback: fixed sell price after auction
    fee: per unit fee
    """

    # sort properly
    bids = sorted(bids, reverse=True)   # high → low
    asks = sorted(asks)                # low → high

    prices = sorted(set([p for p, _ in bids] + [p for p, _ in asks]))

    # compute clearing price
    def get_clearing(bids, asks):
        best_price = None
        best_volume = -1

        for p in prices:
            demand = sum(v for price, v in bids if price >= p)
            supply = sum(v for price, v in asks if price <= p)
            traded = min(demand, supply)

            if traded > best_volume or (traded == best_volume and p > best_price):
                best_volume = traded
                best_price = p

        return best_price, best_volume

    # helper: compute our fill
    def get_fill(p, q, clearing_price, bids, asks):
        if p < clearing_price:
            return 0

        # total supply available
        total_supply = sum(v for price, v in asks if price <= clearing_price)

        # demand ahead of you
        ahead = 0
        for price, vol in bids:
            if price > p:
                ahead += vol
            elif price == p:
                ahead += vol  # you are LAST

        remaining = total_supply - ahead
        if remaining <= 0:
            return 0

        return min(q, remaining)

    best = (0, None, None)  # profit, price, quantity

    # try candidate bid prices
    for p in prices:
        # try a few quantities
        for q in [
            1,
            5000,
            10000,
            20000,
            40000,
            80000
        ]:

            new_bids = bids + [(p, q)]

            clearing_price, _ = get_clearing(new_bids, asks)

            filled = get_fill(p, q, clearing_price, bids, asks)

            profit_per_unit = buyback - clearing_price - fee
            profit = filled * profit_per_unit

            if profit > best[0]:
                best = (profit, p, q)

    return best


print('product |', 'optimal bid\'s (profit, price, quantity)')

bids = [(30,30000), (29,5000), (28,12000), (27,28000)]
asks = [(28,40000), (31,20000), (32,20000), (33,30000)]

print('flax', solve(bids, asks, buyback=30, fee=0))


# this algo is inaccurate for mushrooms
# bids = [(20,43000), (19,17000), (18,6000), (17,5000), (16,10000), (15,5000), (14,10000), (13,7000)]
# asks = [(12,20000), (13,25000), (14,35000), (15,6000), (16,5000), (17,0), (18,10000), (19,12000)]

# print('mushrooms', solve(bids, asks, buyback=20, fee=0.1))


# mushrooms only

def best_thresholds(final_sell_price, cases, fee):
    max_profit, max_profit_vol, max_profit_settle = 0, 0, 0
    for vol, settle_price in cases:
        profit_per_unit = (final_sell_price - settle_price)
        profit = profit_per_unit * vol - fee * vol
        if profit >= max_profit:
            max_profit, max_profit_vol, max_profit_settle = profit, vol, settle_price
        # print(f"profit for {vol} at {settle_price} is {profit}", vol, settle_price, profit)
    
    return (max_profit, max_profit_settle, max_profit_vol)

cases = [(53000, 19), (40000, 19), (50000, 18), (35000, 18), (20000, 17), (10000, 16), (1000, 15)]
print('mushrooms', best_thresholds(20, cases, 0.1)) # profit, volume and price to buy mushrooms at for max profit
# shorting already deemed unprofitable


