import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from main import CoffeeShop, RECIPES, main


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


class LatteTests(unittest.TestCase):
    def test_latte_consumes_both_ingredients_without_changing_budget(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy("milk", 1)
        shop.prepare_latte()
        self.assertEqual(shop.stock, {"coffee": 232, "milk": 800})
        self.assertEqual(shop.budget, 2600)

    def test_exact_recipe_amounts_are_enough(self):
        shop = CoffeeShop(stock={"coffee": 18, "milk": 200})
        shop.prepare_latte()
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})

    def test_missing_ingredients_preserve_entire_state(self):
        for coffee, milk, message in (
            (0, 200, "Недостаточно кофе"),
            (17, 200, "Недостаточно кофе"),
            (18, 0, "Недостаточно молока"),
            (18, 199, "Недостаточно молока"),
            (0, 0, "Недостаточно кофе"),
        ):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(stock={"coffee": coffee, "milk": milk})
                before = (shop.budget, shop.stock.copy())
                with self.assertRaisesRegex(ValueError, message):
                    shop.prepare_latte()
                self.assertEqual((shop.budget, shop.stock), before)

    def test_milk_limits_repeated_preparation(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy("milk", 1)
        for _ in range(5):
            shop.prepare_latte()
        self.assertEqual(shop.stock, {"coffee": 160, "milk": 0})
        with self.assertRaisesRegex(ValueError, "Недостаточно молока"):
            shop.prepare_latte()
        self.assertEqual(shop.stock, {"coffee": 160, "milk": 0})


class RecipeTests(unittest.TestCase):
    def test_catalog_prepares_each_drink(self):
        for drink, coffee, milk in (
            ("espresso", 18, 0), ("latte", 18, 200), ("cappuccino", 18, 120),
        ):
            with self.subTest(drink=drink):
                shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
                shop.prepare_drink(drink)
                self.assertEqual(shop.stock, {"coffee": 250 - coffee, "milk": 1000 - milk})
                self.assertEqual(shop.budget, 3000)

    def test_cappuccino_exact_amounts(self):
        shop = CoffeeShop(stock={"coffee": 18, "milk": 120})
        shop.prepare_drink("cappuccino")
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})

    def test_cappuccino_shortages_preserve_state(self):
        for coffee, milk, message in (
            (17, 120, "Недостаточно кофе"),
            (18, 119, "Недостаточно молока"),
            (0, 0, "Недостаточно кофе"),
        ):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(stock={"coffee": coffee, "milk": milk})
                before = (shop.budget, shop.stock.copy())
                with self.assertRaisesRegex(ValueError, message):
                    shop.prepare_drink("cappuccino")
                self.assertEqual((shop.budget, shop.stock), before)

    def test_unknown_drink_preserves_state(self):
        shop = CoffeeShop()
        before = (shop.budget, shop.stock.copy())
        with self.assertRaisesRegex(ValueError, "Неизвестный напиток"):
            shop.prepare_drink("unknown")
        self.assertEqual((shop.budget, shop.stock), before)

    def test_existing_menu_numbers_and_cappuccino(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["2", "1", "3", "1", "4", "5", "6", "0"]):
            with redirect_stdout(output):
                main()
        text = output.getvalue()
        for name in ("Эспрессо", "Латте", "Капучино"):
            self.assertIn(f"{name} готов!", text)
        self.assertIn("Кофе: 196 г", text)
        self.assertIn("Молоко: 680 мл", text)


class AvailabilityTests(unittest.TestCase):
    def test_empty_stock_allows_no_cups(self):
        shop = CoffeeShop()
        for drink in RECIPES:
            with self.subTest(drink=drink):
                self.assertEqual(shop.available_cups(drink), 0)

    def test_coffee_limits_all_drinks_and_rounds_down(self):
        shop = CoffeeShop(stock={"coffee": 53, "milk": 1000})
        for drink in RECIPES:
            with self.subTest(drink=drink):
                self.assertEqual(shop.available_cups(drink), 2)

    def test_milk_limits_milk_drinks(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 399})
        self.assertEqual(shop.available_cups("latte"), 1)
        self.assertEqual(shop.available_cups("cappuccino"), 3)

    def test_espresso_needs_no_milk(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 0})
        self.assertEqual(shop.available_cups("espresso"), 13)
        self.assertEqual(shop.available_cups("latte"), 0)
        self.assertEqual(shop.available_cups("cappuccino"), 0)

    def test_view_preserves_state_and_uses_current_stock(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy("milk", 1)
        before = (shop.budget, shop.stock.copy())
        output = StringIO()
        with redirect_stdout(output):
            shop.show_recipes()
            shop.show_recipes()
        self.assertEqual((shop.budget, shop.stock), before)
        self.assertIn("Латте — на чашку: кофе: 18 г, молоко: 200 мл; доступно чашек: 5", output.getvalue())
        shop.prepare_latte()
        self.assertEqual(shop.available_cups("latte"), 4)

    def test_unknown_drink_preserves_state(self):
        shop = CoffeeShop()
        before = (shop.budget, shop.stock.copy())
        with self.assertRaisesRegex(ValueError, "Неизвестный напиток"):
            shop.available_cups("unknown")
        self.assertEqual((shop.budget, shop.stock), before)

    def test_menu_opens_view_and_returns_to_menu(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["7", "2", "1", "7", "0"]):
            with redirect_stdout(output):
                main()
        text = output.getvalue()
        self.assertEqual(text.count("Рецепты и доступные чашки:"), 2)
        self.assertIn("Эспрессо — на чашку: кофе: 18 г; доступно чашек: 0", text)
        self.assertIn("Эспрессо — на чашку: кофе: 18 г; доступно чашек: 13", text)


if __name__ == "__main__":
    unittest.main()
