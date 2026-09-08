import unittest
from round3_manual_research.bids import first_bid_ev, second_bid_payoff


class ManualBidTests(unittest.TestCase):
    def test_endpoint_and_first_accepted_reserve(self):
        self.assertEqual(first_bid_ev(670),0)
        self.assertEqual(first_bid_ev(920),0)
        self.assertAlmostEqual(first_bid_ev(671),249/51)
        self.assertAlmostEqual(first_bid_ev(675),245/51)
        self.assertAlmostEqual(first_bid_ev(676),2*244/51)

    def test_second_bid_boundary_and_penalty(self):
        self.assertEqual(second_bid_payoff(920,920),0)
        self.assertEqual(second_bid_payoff(919,918),1)
        self.assertEqual(second_bid_payoff(918,918),2)
        self.assertAlmostEqual(second_bid_payoff(916,918),.5)


if __name__=='__main__':unittest.main()
