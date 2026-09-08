import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prosperity_rust_backtester/scripts/round4_options'))
from counterparty_scan import scan_day, mid_at


class CounterpartyTests(unittest.TestCase):
    def test_censored_volume_is_not_zero_return(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'prices.csv'; t=Path(d)/'trades.csv'
            p.write_text('timestamp;product;mid_price\n100;P;110\n200;P;115\n')
            t.write_text('timestamp;symbol;buyer;seller;price;quantity\n0;P;A;B;100;2\n300;P;A;B;100;2\n')
            rows,_=scan_day(p,t,1,100,200)
            buyer=next(row for row in rows if row['side']=='buyer')
            self.assertEqual(buyer['total_qty'],4)
            self.assertEqual(buyer['observed_qty_100'],2)
            self.assertEqual(buyer['mean_horizon_pnl_100'],10)
            self.assertEqual(buyer['horizon_pnl_200'],30)
            self.assertNotIn('horizon_pnl_500',buyer)

    def test_exact_horizon_does_not_search_into_later_prices(self):
        self.assertIsNone(mid_at({(200,'P'):99},0,'P',100))
        with self.assertRaises(ValueError):mid_at({},0,'P',0)


if __name__=='__main__':unittest.main()
