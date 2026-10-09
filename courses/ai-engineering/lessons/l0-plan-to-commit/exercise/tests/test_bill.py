import unittest

from bill import split_bill


class SplitBill(unittest.TestCase):
    def test_an_even_split(self):
        self.assertEqual(split_bill(10000, 10, 4), [2750, 2750, 2750, 2750])

    def test_one_person_pays_everything(self):
        self.assertEqual(split_bill(4200, 15, 1), [4830])

    def test_left_over_cents_go_to_the_first_people(self):
        self.assertEqual(split_bill(1000, 0, 3), [334, 333, 333])
        self.assertEqual(split_bill(1001, 0, 3), [334, 334, 333])

    def test_the_tip_rounds_to_the_nearest_cent(self):
        self.assertEqual(split_bill(999, 15, 1), [1149])   # tip 149.85 cents -> 150
        self.assertEqual(split_bill(1003, 10, 1), [1103])  # tip 100.3 cents -> 100

    def test_a_half_cent_of_tip_rounds_up(self):
        self.assertEqual(split_bill(10, 15, 1), [12])  # tip 1.5 cents -> 2
        self.assertEqual(split_bill(30, 5, 1), [32])   # tip 1.5 cents -> 2

    def test_shares_always_add_up_to_the_bill_and_tip(self):
        for total in (0, 1, 99, 1000, 12345, 99999):
            for tip in (0, 5, 12, 15, 20):
                for people in range(1, 9):
                    shares = split_bill(total, tip, people)
                    expected = total + (total * tip + 50) // 100
                    self.assertEqual(sum(shares), expected, (total, tip, people))
                    self.assertEqual(len(shares), people)
                    self.assertLessEqual(max(shares) - min(shares), 1)
                    self.assertEqual(shares, sorted(shares, reverse=True))
                    self.assertTrue(all(isinstance(s, int) for s in shares))

    def test_more_people_than_cents(self):
        self.assertEqual(split_bill(2, 0, 4), [1, 1, 0, 0])

    def test_a_free_bill(self):
        self.assertEqual(split_bill(0, 20, 2), [0, 0])

    def test_bad_inputs_are_refused(self):
        for args in ((1000, 10, 0), (1000, 10, -1), (-1, 10, 2), (1000, -5, 2)):
            with self.assertRaises(ValueError, msg=str(args)):
                split_bill(*args)


if __name__ == "__main__":
    unittest.main()
