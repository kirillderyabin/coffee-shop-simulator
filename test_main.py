import unittest

from main import CoffeeShop


class PurchaseTests(unittest.TestCase):
    def test_purchase_updates_budget_and_selected_stock(self):
        shop = CoffeeShop()
        self.assertEqual(shop.buy("coffee", 2), 600)
        self.assertEqual(shop.budget, 2400)
        self.assertEqual(shop.stock, {"coffee": 500, "milk": 0})

    def test_can_spend_entire_budget(self):
        shop = CoffeeShop(budget=100)
        shop.buy("milk", 1)
        self.assertEqual(shop.budget, 0)
        self.assertEqual(shop.stock["milk"], 1000)

    def test_rejected_purchases_preserve_state(self):
        for ingredient, quantity in [
            ("coffee", 11), ("milk", 0), ("milk", -1),
            ("milk", 1.5), ("milk", True), ("water", 1),
        ]:
            with self.subTest(ingredient=ingredient, quantity=quantity):
                shop = CoffeeShop()
                before = (shop.budget, shop.stock.copy())
                with self.assertRaises(ValueError):
                    shop.buy(ingredient, quantity)
                self.assertEqual((shop.budget, shop.stock), before)

    def test_shops_have_independent_stock(self):
        first, second = CoffeeShop(), CoffeeShop()
        first.buy("milk", 1)
        self.assertEqual(second.stock["milk"], 0)


class EspressoTests(unittest.TestCase):
    def test_espresso_consumes_only_coffee(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy("milk", 1)
        shop.prepare_espresso()
        self.assertEqual(shop.stock, {"coffee": 232, "milk": 1000})
        self.assertEqual(shop.budget, 2600)

    def test_exact_coffee_amount_is_enough(self):
        shop = CoffeeShop(stock={"coffee": 18, "milk": 0})
        shop.prepare_espresso()
        self.assertEqual(shop.stock["coffee"], 0)

    def test_insufficient_coffee_preserves_state(self):
        for grams in (0, 17):
            with self.subTest(grams=grams):
                shop = CoffeeShop(stock={"coffee": grams, "milk": 1000})
                before = (shop.budget, shop.stock.copy())
                with self.assertRaisesRegex(ValueError, "Недостаточно кофе"):
                    shop.prepare_espresso()
                self.assertEqual((shop.budget, shop.stock), before)

    def test_package_allows_thirteen_cups_then_requires_purchase(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        for _ in range(13):
            shop.prepare_espresso()
        self.assertEqual(shop.stock["coffee"], 16)
        with self.assertRaises(ValueError):
            shop.prepare_espresso()
        self.assertEqual(shop.stock["coffee"], 16)
        shop.buy("coffee", 1)
        shop.prepare_espresso()
        self.assertEqual(shop.stock["coffee"], 248)


if __name__ == "__main__":
    unittest.main()
