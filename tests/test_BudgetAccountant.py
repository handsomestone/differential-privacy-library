from unittest import TestCase

from diffprivlib.accountant import BudgetAccountant
from diffprivlib.utils import BudgetError


class TestBudgetAccountant(TestCase):
    def tearDown(self):
        BudgetAccountant.pop_default()

    def test_init(self):
        acc = BudgetAccountant()
        self.assertEqual(acc.epsilon, float("inf"))
        self.assertEqual(acc.delta, 1)

    def test_init_epsilon(self):
        acc = BudgetAccountant(1, 0)
        self.assertEqual(acc.epsilon, 1.0)
        self.assertEqual(acc.delta, 0.0)

    def test_init_delta(self):
        acc = BudgetAccountant(0, 0.5)
        self.assertEqual(acc.epsilon, 0)
        self.assertAlmostEqual(acc.delta, 0.5, places=5)

    def test_init_neg_eps(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(-1)

    def test_init_neg_del(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(1, -0.5)

    def test_init_large_del(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(1, 1.5)

    def test_init_zero_budget(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(0, 0)

    def test_init_scalar_spent(self):
        with self.assertRaises(TypeError):
            BudgetAccountant(spent_budget=2)

    def test_init_non_list_spent(self):
        with self.assertRaises(TypeError):
            BudgetAccountant(spent_budget=(1, 0))

    def test_init_small_tuple_spent(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(spent_budget=[(1,)])

    def test_init_large_tuple_spent(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(spent_budget=[(1, 0, 2)])

    def test_init_large_slack(self):
        with self.assertRaises(ValueError):
            BudgetAccountant(1, 1e-2, 1e-1)

    def test_spent_budget(self):
        acc = BudgetAccountant(1, 0, spent_budget=[(0.5, 0), (0.5, 0)])

        with self.assertRaises(BudgetError):
            acc.check(0.1, 0)

    def test_remaining_budget_epsilon(self):
        acc = BudgetAccountant(1, 0)
        eps, delt = acc.remaining()
        self.assertAlmostEqual(eps, 1.0)
        self.assertEqual(delt, 0)

        acc = BudgetAccountant(1, 0)
        eps, delt = acc.remaining(10)
        self.assertAlmostEqual(eps, 0.1)
        self.assertEqual(delt, 0)

    def test_remaining_budget_epsilon_slack(self):
        acc = BudgetAccountant(1, 1e-15, slack=1e-15)
        eps, delt = acc.remaining(100)
        self.assertGreaterEqual(eps, 0.01)
        self.assertEqual(delt, 0)

    def test_remaining_budget_delta(self):
        acc = BudgetAccountant(1, 1e-2)
        eps, delt = acc.remaining(100)
        self.assertGreaterEqual(delt, 1e-4)
        self.assertLessEqual(delt, 1e-3)

        acc = BudgetAccountant(1, 1e-2, slack=1e-5)
        eps, delt = acc.remaining(100)
        self.assertGreaterEqual(eps, 0.01)
        self.assertGreaterEqual(delt, 1e-4)
        self.assertLessEqual(delt, 1e-3)

    def test_remaining_budget_zero_delta(self):
        acc = BudgetAccountant(1, 1e-2, 1e-2)
        _, delt = acc.remaining(100)
        self.assertEqual(0.0, delt)

    def test_remaining_budget_k(self):
        acc = BudgetAccountant(1, 1e-2, 1e-3)

        with self.assertRaises(ValueError):
            acc.remaining(0)

        with self.assertRaises(TypeError):
            acc.remaining(1.0)

    def test_remaining_budget_inf(self):
        acc = BudgetAccountant()
        self.assertEqual((float("inf"), 1.0), acc.remaining())
        self.assertEqual((float("inf"), 1.0), acc.remaining(100))

        acc.spend(float("inf"), 1)
        self.assertEqual((float("inf"), 1.0), acc.remaining())
        self.assertEqual((float("inf"), 1.0), acc.remaining(100))

    def test_spend(self):
        acc = BudgetAccountant()
        acc.spend(1, 0)
        self.assertEqual(acc.total(), (1, 0))

        acc.spend(1, 0.5)
        self.assertEqual(acc.total(), (2, 0.5))

        acc.spend(5, 0)
        self.assertEqual(acc.total(), (7, 0.5))

    def test_spend_errors(self):
        acc = BudgetAccountant()

        with self.assertRaises(ValueError):
            acc.spend(0, 0)

        with self.assertRaises(ValueError):
            acc.spend(-1, 0)

        with self.assertRaises(ValueError):
            acc.spend(1, -1)

        with self.assertRaises(ValueError):
            acc.spend(1, 2)

    def test_spend_exceed(self):
        acc = BudgetAccountant(5, 0)
        acc.spend(3, 0)

        with self.assertRaises(BudgetError):
            acc.spend(3, 0)

        with self.assertRaises(BudgetError):
            acc.spend(0, 1e-5)

    def test_inf_spend(self):
        acc = BudgetAccountant()
        acc.spend(float("inf"), 1)
        self.assertEqual((float("inf"), 1), acc.total())
        self.assertEqual((float("inf"), 1), acc.remaining())
        self.assertEqual((float("inf"), 1), acc.remaining(100))
        self.assertTrue(acc.check(float("inf"), 1))

    def test_remaining_budget_positive_vals(self):
        acc = BudgetAccountant(1, 1e-2, 1e-5, [(0.01, 0), (0.01, 0), (0.01, 0)])
        eps, delt = acc.remaining(50)
        self.assertGreaterEqual(eps, 0)
        self.assertGreaterEqual(delt, 0)

    def test_remaining_budget_implementation(self):
        acc = BudgetAccountant(1, 1e-2, 1e-5, [(0.01, 0), (0.01, 0), (0.01, 0)])
        k = 50

        eps, delt = acc.remaining(k)

        for i in range(k-1):
            acc.spend(eps, delt)

        remaining_eps, remaining_delt = acc.remaining()

        self.assertAlmostEqual(remaining_eps, eps)
        self.assertAlmostEqual(remaining_delt, delt)

    def test_remaining_budget_implementation2(self):
        acc = BudgetAccountant(1, 1e-2, 1e-5)
        k = 50

        eps, delt = acc.remaining(k)

        for i in range(k//2):
            acc.spend(eps, delt)

        eps, delt = acc.remaining(k)

        for i in range(k-1):
            acc.spend(eps, delt)

        remaining_eps, remaining_delt = acc.remaining()

        self.assertAlmostEqual(remaining_eps, eps)
        self.assertAlmostEqual(remaining_delt, delt)

    def test_load_wrong_type(self):
        with self.assertRaises(TypeError):
            BudgetAccountant.load_default(0)

        with self.assertRaises(TypeError):
            BudgetAccountant.load_default([1, 2, 3])

        with self.assertRaises(TypeError):
            BudgetAccountant.load_default("BudgetAccountant")

    def test_set_default(self):
        acc = BudgetAccountant()
        acc.set_default()

        self.assertIs(BudgetAccountant._default, acc)

    def test_pop_default(self):
        acc = BudgetAccountant().set_default()
        acc2 = BudgetAccountant.pop_default()

        self.assertIs(acc, acc2)

    def test_many_queries(self):
        acc = BudgetAccountant(1, 1e-3, 1e-3)

        for i in range(100):
            epsilon, delta = acc.remaining(2)
            acc.spend(epsilon, delta)

        self.assertGreaterEqual(acc.remaining(), (0, 0))