#!/usr/bin/env python3
"""Inspect the sign of PEBBLES_XL/basket co-movement before choosing a hedge.

Offline diagnostic only: it fits no strategy and does not claim an executable
return. A positive-correlation gate is meaningful only for a positive-loading
basket hypothesis. Reads the committed price CSV and requires complete mids.
"""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
from statistics import correlation, fmean, StatisticsError

ROOT=Path(__file__).resolve().parents[1]
SYMBOLS=('PEBBLES_XS','PEBBLES_S','PEBBLES_M','PEBBLES_L','PEBBLES_XL')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--day',type=int,choices=(2,3,4),default=2)
    args=parser.parse_args()
    source=ROOT/'prosperity_rust_backtester/datasets/round5'/f'prices_round_5_day_{args.day}.csv'
    ticks=defaultdict(dict)
    with source.open() as stream:
        for row in csv.DictReader(stream,delimiter=';'):
            if row['product'] in SYMBOLS:
                ticks[int(row['timestamp'])][row['product']]=(float(row['bid_price_1'])+float(row['ask_price_1']))/2
    x=[];basket=[]
    for timestamp,books in sorted(ticks.items()):
        if set(books)!=set(SYMBOLS):
            raise ValueError(f'incomplete family at timestamp {timestamp}')
        x.append(books['PEBBLES_XL'])
        basket.append(fmean(books[symbol] for symbol in SYMBOLS[:-1]))
    dx=[0]+[b-a for a,b in zip(x,x[1:])]
    db=[0]+[b-a for a,b in zip(basket,basket[1:])]
    rolling=[]
    for i in range(49,len(dx)):
        try:rolling.append(correlation(dx[max(0,i-99):i+1],db[max(0,i-99):i+1]))
        except StatisticsError:continue
    if not rolling:
        raise ValueError('no nonconstant windows')
    print(f'day={args.day}, ticks={len(ticks)}, valid rolling windows={len(rolling)}')
    print(f'mean rolling correlation={fmean(rolling):.9f}')
    print(f'windows below original positive-loading threshold 0.3: {sum(value<.3 for value in rolling)}/{len(rolling)}')


if __name__=='__main__':main()
