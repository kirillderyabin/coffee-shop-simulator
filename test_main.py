import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from unittest.mock import patch

from main import CoffeeShop, Order, PurchaseNeed, Recipe, RECIPES, main


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


class BatchTests(unittest.TestCase):
    def test_batch_uses_scaled_recipe_and_preserves_budget(self):
        for drink, expected in (
            ("espresso", {"coffee": 196, "milk": 1000}),
            ("latte", {"coffee": 196, "milk": 400}),
            ("cappuccino", {"coffee": 196, "milk": 640}),
        ):
            with self.subTest(drink=drink):
                shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
                shop.prepare_drink(drink, 3)
                self.assertEqual(shop.stock, expected)
                self.assertEqual(shop.budget, 3000)

    def test_exact_batch_stock_is_enough(self):
        shop = CoffeeShop(stock={"coffee": 54, "milk": 600})
        shop.prepare_drink("latte", 3)
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})

    def test_batch_espresso_needs_no_milk(self):
        shop = CoffeeShop(stock={"coffee": 54, "milk": 0})
        shop.prepare_drink("espresso", 3)
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})

    def test_shortage_for_whole_batch_preserves_state(self):
        for coffee, milk, message in (
            (53, 600, "Недостаточно кофе: нужно 54 г"),
            (54, 599, "Недостаточно молока: нужно 600 мл"),
        ):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(stock={"coffee": coffee, "milk": milk})
                before = (shop.budget, shop.stock.copy())
                with self.assertRaisesRegex(ValueError, message):
                    shop.prepare_drink("latte", 3)
                self.assertEqual((shop.budget, shop.stock), before)

    def test_invalid_quantities_preserve_state(self):
        for quantity in (True, False, 1.0, 1.5, 0, -1, "2", None):
            with self.subTest(quantity=quantity):
                shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
                before = (shop.budget, shop.stock.copy())
                with self.assertRaisesRegex(ValueError, "положительное целое количество чашек"):
                    shop.prepare_drink("latte", quantity)
                self.assertEqual((shop.budget, shop.stock), before)

    def test_batch_menu_then_single_cup(self):
        output = StringIO()
        with patch("builtins.input", side_effect=[
            "2", "1", "3", "1", "8", "5", "3", "4", "0",
        ]):
            with redirect_stdout(output):
                main()
        text = output.getvalue()
        self.assertIn("Партия готова: Латте, чашек: 3", text)
        self.assertIn("Эспрессо готов!", text)
        self.assertIn("Кофе: 178 г", text)
        self.assertIn("Молоко: 400 мл", text)

    def test_invalid_batch_menu_input_returns_without_preparation(self):
        for inputs, message in (
            (["8", "9", "0"], "Неизвестный напиток"),
            (["8", "5", "abc", "0"], "положительное целое количество чашек"),
            (["8", "5", "0", "0"], "положительное целое количество чашек"),
        ):
            with self.subTest(inputs=inputs):
                output = StringIO()
                with patch("builtins.input", side_effect=inputs):
                    with redirect_stdout(output):
                        main()
                self.assertIn(message, output.getvalue())
                self.assertNotIn("Партия готова", output.getvalue())


class PurchasePlanTests(unittest.TestCase):
    def test_sufficient_and_exact_stock_require_no_purchase(self):
        for coffee, milk in ((54, 600), (250, 1000)):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(stock={"coffee": coffee, "milk": milk})
                self.assertEqual(shop.plan_purchase("latte", 3), {
                    "coffee": PurchaseNeed(0, 0, 0),
                    "milk": PurchaseNeed(0, 0, 0),
                })

    def test_shortage_of_each_ingredient(self):
        for coffee, milk, expected in (
            (53, 600, {"coffee": PurchaseNeed(1, 1, 300), "milk": PurchaseNeed(0, 0, 0)}),
            (54, 599, {"coffee": PurchaseNeed(0, 0, 0), "milk": PurchaseNeed(1, 1, 100)}),
        ):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(stock={"coffee": coffee, "milk": milk})
                self.assertEqual(shop.plan_purchase("latte", 3), expected)

    def test_rounds_up_only_missing_amount(self):
        shop = CoffeeShop(stock={"coffee": 2, "milk": 800})
        self.assertEqual(shop.plan_purchase("latte", 14), {
            "coffee": PurchaseNeed(250, 1, 300),
            "milk": PurchaseNeed(2000, 2, 200),
        })
        shop = CoffeeShop(stock={"coffee": 1, "milk": 799})
        self.assertEqual(shop.plan_purchase("latte", 14), {
            "coffee": PurchaseNeed(251, 2, 600),
            "milk": PurchaseNeed(2001, 3, 300),
        })

    def test_espresso_requires_no_milk_purchase(self):
        shop = CoffeeShop()
        self.assertEqual(shop.plan_purchase("espresso", 2), {
            "coffee": PurchaseNeed(36, 1, 300),
        })

    def test_invalid_input_preserves_state(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        before = (shop.budget, shop.stock.copy())
        for quantity in (True, False, 1.0, 1.5, 0, -1, "2", None):
            with self.subTest(quantity=quantity):
                with self.assertRaisesRegex(ValueError, "положительное целое количество чашек"):
                    shop.plan_purchase("latte", quantity)
                self.assertEqual((shop.budget, shop.stock), before)
        with self.assertRaisesRegex(ValueError, "Неизвестный напиток"):
            shop.plan_purchase("unknown", 1)
        self.assertEqual((shop.budget, shop.stock), before)

    def test_report_total_budget_and_no_mutations(self):
        for budget, message in ((400, "Бюджета хватает."), (399, "нужно ещё 1 руб.")):
            with self.subTest(budget=budget):
                shop = CoffeeShop(budget=budget)
                before = (shop.budget, shop.stock.copy())
                output = StringIO()
                with redirect_stdout(output):
                    shop.show_purchase_plan("latte", 3)
                self.assertIn("Общая стоимость закупки: 400 руб.", output.getvalue())
                self.assertIn(message, output.getvalue())
                self.assertEqual((shop.budget, shop.stock), before)

    def test_menu_plan_does_not_buy_or_prepare(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["9", "5", "3", "1", "0"]):
            with redirect_stdout(output):
                main()
        text = output.getvalue()
        self.assertIn("Общая стоимость закупки: 400 руб.", text)
        self.assertEqual(text.count("Бюджет: 3000 руб.\nКофе: 0 г\nМолоко: 0 мл"), 2)
        self.assertNotIn("Партия готова", text)


class BuyMissingTests(unittest.TestCase):
    def test_buys_both_ingredients_without_preparing_drinks(self):
        shop = CoffeeShop(stock={"coffee": 10, "milk": 100})
        self.assertEqual(shop.buy_missing("latte", 3), 400)
        self.assertEqual(shop.stock, {"coffee": 260, "milk": 1100})
        self.assertEqual(shop.budget, 2600)

    def test_exact_budget_is_enough(self):
        shop = CoffeeShop(budget=400)
        self.assertEqual(shop.buy_missing("latte", 3), 400)
        self.assertEqual(shop.budget, 0)
        self.assertEqual(shop.stock, {"coffee": 250, "milk": 1000})

    def test_insufficient_total_budget_does_not_buy_part_of_plan(self):
        shop = CoffeeShop(budget=399)
        before = (shop.budget, shop.stock.copy())
        with self.assertRaisesRegex(ValueError, "Недостаточно денег: нужно 400 руб."):
            shop.buy_missing("latte", 3)
        self.assertEqual((shop.budget, shop.stock), before)

    def test_no_shortage_costs_nothing_even_with_empty_budget(self):
        shop = CoffeeShop(budget=0, stock={"coffee": 54, "milk": 600})
        before = (shop.budget, shop.stock.copy())
        self.assertEqual(shop.buy_missing("latte", 3), 0)
        self.assertEqual((shop.budget, shop.stock), before)

    def test_only_missing_ingredient_is_bought(self):
        shop = CoffeeShop(stock={"coffee": 54, "milk": 599})
        self.assertEqual(shop.buy_missing("latte", 3), 100)
        self.assertEqual(shop.stock, {"coffee": 54, "milk": 1599})

    def test_invalid_input_leaves_state_unchanged(self):
        shop = CoffeeShop()
        before = (shop.budget, shop.stock.copy())
        for quantity in (0, -1, True, False, 1.0, 1.5, "2", None):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    shop.buy_missing("latte", quantity)
                self.assertEqual((shop.budget, shop.stock), before)
        with self.assertRaisesRegex(ValueError, "Неизвестный напиток"):
            shop.buy_missing("unknown")
        self.assertEqual((shop.budget, shop.stock), before)

    def run_menu(self, shop, inputs):
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=inputs):
                with redirect_stdout(output):
                    main()
        return output.getvalue()

    def test_menu_requires_explicit_confirmation(self):
        for answer in ("нет", "", "yes", "непонятно"):
            with self.subTest(answer=answer):
                shop = CoffeeShop()
                before = (shop.budget, shop.stock.copy())
                text = self.run_menu(shop, ["10", "5", "3", answer, "0"])
                self.assertIn("Общая стоимость закупки: 400 руб.", text)
                self.assertIn("Закупка отменена", text)
                self.assertEqual((shop.budget, shop.stock), before)

    def test_menu_confirmed_purchase(self):
        shop = CoffeeShop()
        text = self.run_menu(shop, ["10", "5", "3", " Да ", "0"])
        self.assertIn("Закупка выполнена. Потрачено: 400 руб.", text)
        self.assertEqual(shop.budget, 2600)
        self.assertEqual(shop.stock, {"coffee": 250, "milk": 1000})

    def test_menu_handles_insufficient_budget_and_no_shortage(self):
        for shop, message in (
            (CoffeeShop(budget=399), "Закупка не выполнена"),
            (CoffeeShop(stock={"coffee": 54, "milk": 600}), "Покупка не требуется"),
        ):
            with self.subTest(message=message):
                before = (shop.budget, shop.stock.copy())
                text = self.run_menu(shop, ["10", "5", "3", "0"])
                self.assertIn(message, text)
                self.assertEqual((shop.budget, shop.stock), before)

    def test_menu_rejects_invalid_drink_and_quantity(self):
        for inputs in (
            ["10", "11", "0"], ["10", "5", "abc", "0"],
            ["10", "5", "0", "0"], ["10", "5", "-1", "0"],
        ):
            with self.subTest(inputs=inputs):
                shop = CoffeeShop()
                before = (shop.budget, shop.stock.copy())
                text = self.run_menu(shop, inputs)
                self.assertNotIn("Закупка выполнена", text)
                self.assertEqual((shop.budget, shop.stock), before)


class VisitorTests(unittest.TestCase):
    def test_invitation_creates_catalog_order_without_spending_resources(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        before = (shop.budget, shop.stock.copy())
        order = shop.invite_visitor()
        self.assertEqual(order, Order("espresso", 1))
        self.assertIs(shop.current_order, order)
        self.assertEqual(shop.visitors_invited, 1)
        self.assertEqual((shop.budget, shop.stock), before)

    def test_deterministic_cycle_uses_catalog_and_positive_quantities(self):
        for index, expected in enumerate((
            Order("espresso", 1), Order("latte", 2),
            Order("cappuccino", 3), Order("espresso", 1),
        )):
            with self.subTest(index=index):
                shop = CoffeeShop(visitors_invited=index)
                self.assertEqual(shop.invite_visitor(), expected)

    def test_active_order_is_not_replaced(self):
        shop = CoffeeShop()
        order = shop.invite_visitor()
        before = (shop.budget, shop.stock.copy(), shop.visitors_invited)
        with self.assertRaisesRegex(ValueError, "незавершённый заказ"):
            shop.invite_visitor()
        self.assertIs(shop.current_order, order)
        self.assertEqual((shop.budget, shop.stock, shop.visitors_invited), before)

    def test_order_rejects_unknown_drink_and_invalid_quantities(self):
        with self.assertRaisesRegex(ValueError, "Неизвестный напиток"):
            Order("unknown", 1)
        for quantity in (0, -1, True, 1.5, "2"):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    Order("latte", quantity)

    def test_view_is_read_only_with_and_without_order(self):
        for order in (None, Order("latte", 2)):
            with self.subTest(order=order):
                shop = CoffeeShop(current_order=order)
                before = (shop.budget, shop.stock.copy(), shop.current_order, shop.visitors_invited)
                output = StringIO()
                with redirect_stdout(output):
                    shop.show_order()
                    shop.show_order()
                self.assertEqual(
                    (shop.budget, shop.stock, shop.current_order, shop.visitors_invited), before
                )
                expected = "Текущего заказа нет" if order is None else "Латте, чашек: 2"
                self.assertIn(expected, output.getvalue())

    def test_preparing_drink_does_not_complete_order(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        order = shop.invite_visitor()
        shop.prepare_drink(order.drink, order.quantity)
        self.assertIs(shop.current_order, order)
        self.assertEqual(shop.budget, 3000)

    def test_menu_invites_views_and_rejects_second_invitation(self):
        shop = CoffeeShop()
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=["12", "11", "12", "11", "0"]):
                with redirect_stdout(output):
                    main()
        text = output.getvalue()
        self.assertIn("Текущего заказа нет", text)
        self.assertIn("Текущий заказ: Эспрессо, чашек: 1", text)
        self.assertIn("незавершённый заказ", text)
        self.assertEqual(shop.visitors_invited, 1)
        self.assertEqual(shop.budget, 3000)
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})


class ServiceTests(unittest.TestCase):
    def snapshot(self, shop):
        return (shop.budget, shop.stock.copy(), shop.current_order,
                shop.revenue, shop.visitors_invited)

    def test_serves_entire_order_with_exact_stock(self):
        shop = CoffeeShop(stock={"coffee": 36, "milk": 400}, current_order=Order("latte", 2))
        self.assertEqual(shop.serve_order(), 400)
        self.assertEqual(shop.stock, {"coffee": 0, "milk": 0})
        self.assertEqual(shop.budget, 3400)
        self.assertEqual(shop.revenue, 400)
        self.assertIsNone(shop.current_order)

    def test_shortage_of_either_ingredient_preserves_everything(self):
        for coffee, milk, message in (
            (35, 400, "Недостаточно кофе"), (36, 399, "Недостаточно молока"),
        ):
            with self.subTest(coffee=coffee, milk=milk):
                shop = CoffeeShop(
                    stock={"coffee": coffee, "milk": milk},
                    current_order=Order("latte", 2), revenue=120, visitors_invited=2,
                )
                before = self.snapshot(shop)
                with self.assertRaisesRegex(ValueError, message):
                    shop.serve_order()
                self.assertEqual(self.snapshot(shop), before)

    def test_no_order_or_repeated_service_cannot_charge(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 0})
        before = self.snapshot(shop)
        with self.assertRaisesRegex(ValueError, "Текущего заказа нет"):
            shop.serve_order()
        self.assertEqual(self.snapshot(shop), before)
        shop.invite_visitor()
        shop.serve_order()
        after_sale = self.snapshot(shop)
        with self.assertRaisesRegex(ValueError, "Текущего заказа нет"):
            shop.serve_order()
        self.assertEqual(self.snapshot(shop), after_sale)
        self.assertEqual(shop.revenue, 120)
        self.assertEqual(shop.budget, 3120)
        self.assertEqual(shop.stock["coffee"], 232)

    def test_sequential_visitors_accumulate_gross_revenue(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy("milk", 1)
        for drink, quantity, total in (
            ("espresso", 1, 120), ("latte", 2, 400), ("cappuccino", 3, 540),
        ):
            self.assertEqual(shop.invite_visitor(), Order(drink, quantity))
            self.assertEqual(shop.serve_order(), total)
        self.assertEqual(shop.revenue, 1060)
        self.assertEqual(shop.budget, 3660)
        self.assertEqual(shop.stock, {"coffee": 142, "milk": 240})
        shop.buy("milk", 1)
        self.assertEqual(shop.revenue, 1060)
        self.assertEqual(shop.budget, 3560)
        self.assertEqual(shop.invite_visitor(), Order("espresso", 1))

    def test_training_preparation_does_not_sell_or_complete_order(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        order = shop.invite_visitor()
        shop.prepare_espresso()
        shop.prepare_latte()
        shop.prepare_drink("cappuccino", 2)
        self.assertIs(shop.current_order, order)
        self.assertEqual(shop.revenue, 0)
        self.assertEqual(shop.budget, 3000)

    def test_order_total_and_price_validation(self):
        self.assertEqual(Order("espresso", 1).total, 120)
        self.assertEqual(Order("latte", 2).total, 400)
        self.assertEqual(Order("cappuccino", 3).total, 540)
        for price in (0, -1, True, 1.5):
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    Recipe("Тест", 18, price=price)

    def test_order_and_status_show_amounts(self):
        shop = CoffeeShop(current_order=Order("latte", 2), revenue=120)
        before = self.snapshot(shop)
        output = StringIO()
        with redirect_stdout(output):
            shop.show_order()
            shop.show_status()
        self.assertIn("Сумма заказа: 400 руб.", output.getvalue())
        self.assertIn("Выручка (валовые продажи, не прибыль): 120 руб.", output.getvalue())
        self.assertEqual(self.snapshot(shop), before)

    def test_menu_service_retry_then_next_visitor(self):
        shop = CoffeeShop()
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=[
                "11", "13", "2", "1", "13", "13", "11", "12", "0",
            ]):
                with redirect_stdout(output):
                    main()
        text = output.getvalue()
        self.assertIn("Недостаточно кофе", text)
        self.assertEqual(text.count("Заказ выполнен! Получено: 120 руб."), 1)
        self.assertIn("Сумма заказа: 400 руб.", text)
        self.assertEqual(shop.current_order, Order("latte", 2))
        self.assertEqual(shop.revenue, 120)
        self.assertEqual(shop.budget, 2820)


class SalesStatisticsTests(unittest.TestCase):
    def test_multiple_orders_accumulate_cups_and_revenue_by_drink(self):
        shop = CoffeeShop(stock={"coffee": 500, "milk": 2000})
        for _ in range(4):
            shop.invite_visitor()
            shop.serve_order()
        self.assertEqual(shop.served_orders, 4)
        self.assertEqual(shop.sold_cups, 7)
        self.assertEqual(shop.revenue, 1180)
        self.assertEqual(
            {key: (sale.cups, sale.revenue) for key, sale in shop.sales.items()},
            {"espresso": (2, 240), "latte": (2, 400), "cappuccino": (3, 540)},
        )
        self.assertEqual(sum(sale.revenue for sale in shop.sales.values()), shop.revenue)

    def test_failed_service_and_repeat_do_not_change_statistics(self):
        for stock in ({"coffee": 35, "milk": 400}, {"coffee": 36, "milk": 399}):
            with self.subTest(stock=stock):
                shop = CoffeeShop(stock=stock.copy(), current_order=Order("latte", 2))
                before = deepcopy(shop)
                with self.assertRaises(ValueError):
                    shop.serve_order()
                self.assertEqual(shop, before)
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        for after_sale in (False, True):
            with self.subTest(after_sale=after_sale):
                if after_sale:
                    shop.invite_visitor()
                    shop.serve_order()
                before = deepcopy(shop)
                with self.assertRaises(ValueError):
                    shop.serve_order()
                self.assertEqual(shop, before)

    def test_training_and_purchases_do_not_count_as_sales(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        shop.buy_missing("latte", 3)
        order = shop.invite_visitor()
        shop.prepare_espresso()
        shop.prepare_latte()
        shop.prepare_drink("cappuccino", 2)
        self.assertEqual(shop.served_orders, 0)
        self.assertEqual(shop.sold_cups, 0)
        self.assertEqual(shop.revenue, 0)
        self.assertTrue(all(sale.cups == sale.revenue == 0 for sale in shop.sales.values()))
        self.assertIs(shop.current_order, order)

    def test_view_is_read_only_before_and_after_sales(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        for after_sale in (False, True):
            with self.subTest(after_sale=after_sale):
                if after_sale:
                    shop.invite_visitor()
                    shop.serve_order()
                before = deepcopy(shop)
                output = StringIO()
                with redirect_stdout(output):
                    shop.show_sales()
                    shop.show_sales()
                self.assertEqual(shop, before)
                count = 1 if after_sale else 0
                self.assertIn(f"Обслужено заказов: {count}", output.getvalue())
                self.assertIn(f"Продано чашек: {count}", output.getvalue())
                self.assertIn("Латте: чашек — 0, выручка — 0 руб.", output.getvalue())

    def test_shops_have_independent_statistics(self):
        first = CoffeeShop(stock={"coffee": 18, "milk": 0})
        second = CoffeeShop()
        first.invite_visitor()
        first.serve_order()
        self.assertEqual(second.sales["espresso"].cups, 0)
        self.assertEqual(second.served_orders, 0)

    def test_menu_shows_statistics_after_service(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=["14", "11", "13", "14", "0"]):
                with redirect_stdout(output):
                    main()
        text = output.getvalue()
        self.assertIn("Обслужено заказов: 0", text)
        self.assertIn("Обслужено заказов: 1", text)
        self.assertIn("Эспрессо: чашек — 1, выручка — 120 руб.", text)
        self.assertEqual(shop.sold_cups, 1)


class DeclineOrderTests(unittest.TestCase):
    def shop_with_sale_and_waiting_order(self):
        shop = CoffeeShop(stock={"coffee": 250, "milk": 1000})
        shop.invite_visitor()
        shop.serve_order()
        shop.invite_visitor()
        return shop

    def run_menu(self, shop, inputs):
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=inputs):
                with redirect_stdout(output):
                    main()
        return output.getvalue()

    def test_decline_changes_only_current_order(self):
        shop = self.shop_with_sale_and_waiting_order()
        before = deepcopy(shop)
        self.assertEqual(shop.decline_order(), Order("latte", 2))
        before.current_order = None
        self.assertEqual(shop, before)

    def test_no_order_and_repeated_decline_leave_state_unchanged(self):
        shop = self.shop_with_sale_and_waiting_order()
        shop.decline_order()
        before = deepcopy(shop)
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "Текущего заказа нет"):
                shop.decline_order()
            self.assertEqual(shop, before)

    def test_can_invite_next_visitor_after_decline(self):
        shop = CoffeeShop()
        shop.invite_visitor()
        shop.decline_order()
        self.assertEqual(shop.invite_visitor(), Order("latte", 2))
        self.assertEqual(shop.visitors_invited, 2)
        self.assertEqual(shop.served_orders, 0)
        self.assertEqual(shop.revenue, 0)

    def test_menu_shows_order_before_confirmation_and_declines(self):
        shop = self.shop_with_sale_and_waiting_order()
        before = deepcopy(shop)
        shown_when_prompted = []
        output = StringIO()

        def answer(prompt):
            if "Отказаться от этого заказа" in prompt:
                shown_when_prompted.append(output.getvalue())
                return " Да "
            return next(choices)

        choices = iter(["15", "0"])
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=answer):
                with redirect_stdout(output):
                    main()
        self.assertEqual(len(shown_when_prompted), 1)
        self.assertIn("Текущий заказ: Латте, чашек: 2", shown_when_prompted[0])
        self.assertIn("Сумма заказа: 400 руб.", shown_when_prompted[0])
        self.assertIn("Заказ отклонён", output.getvalue())
        before.current_order = None
        self.assertEqual(shop, before)

    def test_menu_without_explicit_confirmation_preserves_everything(self):
        for answer in ("нет", "", "yes", "непонятно"):
            with self.subTest(answer=answer):
                shop = self.shop_with_sale_and_waiting_order()
                before = deepcopy(shop)
                text = self.run_menu(shop, ["15", answer, "0"])
                self.assertIn("Текущий заказ сохранён", text)
                self.assertEqual(shop, before)

    def test_menu_without_order_does_not_request_confirmation(self):
        shop = CoffeeShop()
        before = deepcopy(shop)
        text = self.run_menu(shop, ["15", "0"])
        self.assertIn("Текущего заказа нет", text)
        self.assertEqual(shop, before)


class FinanceTests(unittest.TestCase):
    def test_initial_budget_is_not_revenue_or_result(self):
        shop = CoffeeShop(budget=5000)
        self.assertEqual((shop.revenue, shop.purchase_expenses, shop.cash_result), (0, 0, 0))

    def test_both_purchase_paths_accumulate_expenses_once(self):
        shop = CoffeeShop()
        shop.buy("coffee", 2)
        self.assertEqual(shop.purchase_expenses, 600)
        shop.buy_missing("latte", 6)
        self.assertEqual(shop.purchase_expenses, 800)
        self.assertEqual(shop.cash_result, -800)
        self.assertEqual(shop.budget, 2200)
        self.assertEqual(shop.revenue, 0)
        before = deepcopy(shop)
        self.assertEqual(shop.buy_missing("latte", 6), 0)
        self.assertEqual(shop, before)

    def test_rejected_purchases_preserve_expenses_and_state(self):
        shop = CoffeeShop(budget=399)
        for operation in (
            lambda: shop.buy("coffee", 2),
            lambda: shop.buy("milk", 0),
            lambda: shop.buy_missing("latte", 3),
            lambda: shop.buy_missing("latte", -1),
        ):
            before = deepcopy(shop)
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual(shop, before)

    def test_sales_change_result_without_changing_expenses(self):
        shop = CoffeeShop()
        shop.buy_missing("latte", 3)
        self.assertEqual(shop.cash_result, -400)
        shop.invite_visitor()
        shop.serve_order()
        self.assertEqual(shop.cash_result, -280)
        shop.invite_visitor()
        shop.serve_order()
        self.assertEqual(shop.cash_result, 120)
        self.assertEqual(shop.purchase_expenses, 400)
        self.assertEqual(shop.revenue, 520)
        self.assertEqual(shop.budget, 3000 + shop.cash_result)
        before = (shop.revenue, shop.purchase_expenses, shop.cash_result)
        shop.prepare_drink("cappuccino", 2)
        self.assertEqual((shop.revenue, shop.purchase_expenses, shop.cash_result), before)
        shop.invite_visitor()
        shop.decline_order()
        self.assertEqual((shop.revenue, shop.purchase_expenses, shop.cash_result), before)

    def test_cancelled_purchase_menu_and_order_decline_do_not_add_expenses(self):
        shop = CoffeeShop()
        before = deepcopy(shop)
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=["10", "5", "3", "нет", "0"]):
                with redirect_stdout(StringIO()):
                    main()
        self.assertEqual(shop, before)
        shop.invite_visitor()
        shop.decline_order()
        self.assertEqual(shop.purchase_expenses, 0)

    def test_finance_view_in_menu_is_read_only(self):
        shop = CoffeeShop()
        shop.buy("coffee", 1)
        before = deepcopy(shop)
        output = StringIO()
        with patch("main.CoffeeShop", return_value=shop):
            with patch("builtins.input", side_effect=["14", "14", "0"]):
                with redirect_stdout(output):
                    main()
        self.assertEqual(shop, before)
        self.assertIn("Расходы на закупки: 300 руб.", output.getvalue())
        self.assertIn("Денежный результат сессии (выручка минус закупки): -300 руб.", output.getvalue())
        self.assertIn("Это не бухгалтерская прибыль", output.getvalue())


if __name__ == "__main__":
    unittest.main()
