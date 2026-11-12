import unittest

from main import CoffeeShop


class PurchaseTests(unittest.TestCase):
    def test_purchase_updates_budget_and_selected_stock(self):
        shop = CoffeeShop()
        self.assertEqual(shop.buy("coffee", 2), 600)
        self.assertEqual(shop.budget, 2400)
        self.assertEqual(shop.stock, {"coffee": 2, "milk": 0})

    def test_can_spend_entire_budget(self):
        shop = CoffeeShop(budget=100)
        shop.buy("milk", 1)
        self.assertEqual(shop.budget, 0)
        self.assertEqual(shop.stock["milk"], 1)

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


if __name__ == "__main__":
    unittest.main()
