"""Симулятор кофейни: закупка ингредиентов и приготовление напитков."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Ingredient:
    name: str
    package: str
    price: int
    amount: int
    unit: str


# Все суммы указаны в целых рублях, ингредиенты покупаются упаковками.
# Запасы хранятся в граммах для кофе и миллилитрах для молока.
INGREDIENTS = {
    "coffee": Ingredient("Кофе", "пачка 250 г", 300, 250, "г"),
    "milk": Ingredient("Молоко", "пакет 1 л", 100, 1000, "мл"),
}
ESPRESSO_COFFEE_GRAMS = 18
LATTE_COFFEE_GRAMS = 18
LATTE_MILK_ML = 200


@dataclass(frozen=True)
class Recipe:
    name: str
    coffee_grams: int
    price: int
    milk_ml: int = 0

    def __post_init__(self) -> None:
        if type(self.price) is not int or self.price <= 0:
            raise ValueError("Цена напитка должна быть положительным целым числом рублей.")

    def requirements(self) -> dict[str, int]:
        amounts = {"coffee": self.coffee_grams, "milk": self.milk_ml}
        return {key: amount for key, amount in amounts.items() if amount > 0}

    def describe(self) -> str:
        return ", ".join(
            f"{INGREDIENTS[item].name.lower()}: {amount} {INGREDIENTS[item].unit}"
            for item, amount in self.requirements().items()
        )


# Порядок каталога сохраняет пункты меню: 4 — эспрессо, 5 — латте, 6 — капучино.
RECIPES = {
    "espresso": Recipe("Эспрессо", ESPRESSO_COFFEE_GRAMS, price=120),
    "latte": Recipe("Латте", LATTE_COFFEE_GRAMS, price=200, milk_ml=LATTE_MILK_ML),
    "cappuccino": Recipe("Капучино", 18, price=180, milk_ml=120),
}


def required_ingredients(drink: str, quantity: int) -> dict[str, int]:
    if drink not in RECIPES:
        raise ValueError("Неизвестный напиток.")
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Введите положительное целое количество чашек.")
    return {
        ingredient: amount * quantity
        for ingredient, amount in RECIPES[drink].requirements().items()
    }


@dataclass(frozen=True)
class PurchaseNeed:
    missing: int
    packages: int
    cost: int


@dataclass(frozen=True)
class Order:
    drink: str
    quantity: int

    def __post_init__(self) -> None:
        required_ingredients(self.drink, self.quantity)

    @property
    def total(self) -> int:
        return RECIPES[self.drink].price * self.quantity


@dataclass
class DrinkSales:
    cups: int = 0
    revenue: int = 0


@dataclass
class CoffeeShop:
    budget: int = 3000
    stock: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in INGREDIENTS}
    )
    current_order: Order | None = None
    visitors_invited: int = 0
    revenue: int = 0
    served_orders: int = 0
    sales: dict[str, DrinkSales] = field(
        default_factory=lambda: {key: DrinkSales() for key in RECIPES}
    )

    @property
    def sold_cups(self) -> int:
        return sum(sale.cups for sale in self.sales.values())

    def show_sales(self) -> None:
        print("\nСтатистика продаж за текущую сессию:")
        print(f"Обслужено заказов: {self.served_orders}")
        print(f"Продано чашек: {self.sold_cups}")
        print(f"Выручка (валовые продажи, не прибыль): {self.revenue} руб.")
        for key, recipe in RECIPES.items():
            sale = self.sales[key]
            print(f"{recipe.name}: чашек — {sale.cups}, выручка — {sale.revenue} руб.")

    def invite_visitor(self) -> Order:
        """Пригласить посетителя по предсказуемому циклу без замены заказа."""
        if self.current_order is not None:
            raise ValueError("Уже есть незавершённый заказ. Новый посетитель пока не приглашён.")
        drinks = tuple(RECIPES)
        order = Order(
            drinks[self.visitors_invited % len(drinks)],
            self.visitors_invited % 3 + 1,
        )
        self.current_order = order
        self.visitors_invited += 1
        return order

    def show_order(self) -> None:
        if self.current_order is None:
            print("Текущего заказа нет. Пригласите посетителя через пункт 11.")
            return
        order = self.current_order
        print(f"Текущий заказ: {RECIPES[order.drink].name}, чашек: {order.quantity}.")
        print(f"Цена за чашку: {RECIPES[order.drink].price} руб. Сумма заказа: {order.total} руб.")
        print("Заказ ожидает обслуживания. Для приготовления и продажи выберите пункт 13.")

    def serve_order(self) -> int:
        """Приготовить весь заказ и получить оплату ровно один раз."""
        if self.current_order is None:
            raise ValueError("Текущего заказа нет. Пригласите посетителя через пункт 11.")
        order = self.current_order
        total = order.total
        self.prepare_drink(order.drink, order.quantity)
        self.budget += total
        self.revenue += total
        self.served_orders += 1
        self.sales[order.drink].cups += order.quantity
        self.sales[order.drink].revenue += total
        self.current_order = None
        return total

    def buy(self, ingredient: str, quantity: int) -> int:
        """Купить упаковки и вернуть стоимость; при ошибке сохранить состояние."""
        if ingredient not in INGREDIENTS:
            raise ValueError("Неизвестный ингредиент.")
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Введите положительное целое количество упаковок.")
        item = INGREDIENTS[ingredient]
        cost = item.price * quantity
        if cost > self.budget:
            raise ValueError(
                f"Недостаточно денег: нужно {cost} руб., доступно {self.budget} руб."
            )
        self.budget -= cost
        self.stock[ingredient] += item.amount * quantity
        return cost

    def prepare_drink(self, drink: str, quantity: int = 1) -> None:
        """Проверить всю партию перед списанием; по умолчанию готовить чашку."""
        requirements = required_ingredients(drink, quantity)
        for ingredient, amount in requirements.items():
            if self.stock[ingredient] < amount:
                item = INGREDIENTS[ingredient]
                name = {"coffee": "кофе", "milk": "молока"}[ingredient]
                raise ValueError(
                    f"Недостаточно {name}: нужно {amount} {item.unit}, "
                    f"в запасе {self.stock[ingredient]} {item.unit}. "
                    f"Купите {item.name.lower()}."
                )
        for ingredient, amount in requirements.items():
            self.stock[ingredient] -= amount

    def prepare_espresso(self) -> None:
        self.prepare_drink("espresso")

    def prepare_latte(self) -> None:
        self.prepare_drink("latte")

    def plan_purchase(self, drink: str, quantity: int = 1) -> dict[str, PurchaseNeed]:
        """Рассчитать только недостающие упаковки, не совершая покупок."""
        plan = {}
        for ingredient, amount in required_ingredients(drink, quantity).items():
            item = INGREDIENTS[ingredient]
            missing = max(0, amount - self.stock[ingredient])
            packages = (missing + item.amount - 1) // item.amount
            plan[ingredient] = PurchaseNeed(missing, packages, packages * item.price)
        return plan

    def buy_missing(self, drink: str, quantity: int = 1) -> int:
        """Купить весь план после проверки общей суммы; вернуть стоимость."""
        plan = self.plan_purchase(drink, quantity)
        total = sum(need.cost for need in plan.values())
        if total > self.budget:
            raise ValueError(
                f"Недостаточно денег: нужно {total} руб., доступно {self.budget} руб."
            )
        for ingredient, need in plan.items():
            self.stock[ingredient] += need.packages * INGREDIENTS[ingredient].amount
        self.budget -= total
        return total

    def show_purchase_plan(self, drink: str, quantity: int) -> int:
        plan = self.plan_purchase(drink, quantity)
        print(f"\nПлан закупки: {RECIPES[drink].name}, чашек: {quantity}.")
        for ingredient, need in plan.items():
            item = INGREDIENTS[ingredient]
            print(
                f"{item.name}: не хватает {need.missing} {item.unit}; "
                f"купить упаковок ({item.package}): {need.packages}; "
                f"стоимость: {need.cost} руб."
            )
        total = sum(need.cost for need in plan.values())
        print(f"Общая стоимость закупки: {total} руб. Бюджет: {self.budget} руб.")
        if total <= self.budget:
            print("Бюджета хватает.")
        else:
            print(f"Бюджета не хватает: нужно ещё {total - self.budget} руб.")
        print("Это только расчёт: покупки не выполнены, запасы и бюджет не изменены.")
        return total

    def available_cups(self, drink: str) -> int:
        """Сколько чашек одного напитка можно приготовить из текущих запасов."""
        if drink not in RECIPES:
            raise ValueError("Неизвестный напиток.")
        return min(
            self.stock[ingredient] // amount
            for ingredient, amount in RECIPES[drink].requirements().items()
        )

    def show_recipes(self) -> None:
        print("\nРецепты и доступные чашки:")
        for key, recipe in RECIPES.items():
            print(
                f"{recipe.name} — на чашку: {recipe.describe()}; "
                f"доступно чашек: {self.available_cups(key)}; цена: {recipe.price} руб."
            )
        print("Каждый расчёт отдельный: напитки используют общие запасы.")

    def show_status(self) -> None:
        print(f"\nБюджет: {self.budget} руб.")
        for key, item in INGREDIENTS.items():
            print(f"{item.name}: {self.stock[key]} {item.unit}")
        print(f"Выручка (валовые продажи, не прибыль): {self.revenue} руб.")


def main() -> None:
    shop = CoffeeShop()
    drink_choices = {str(number): key for number, key in enumerate(RECIPES, start=4)}
    print("Добро пожаловать в Coffee Shop Simulator!")
    shop.show_status()
    try:
        while True:
            print("\n1 — Бюджет и запасы")
            for number, item in enumerate(
                INGREDIENTS.values(), start=2
            ):
                print(
                    f"{number} — Купить: {item.name}, {item.package} "
                    f"— {item.price} руб."
                )
            for number, key in drink_choices.items():
                recipe = RECIPES[key]
                print(f"{number} — Приготовить {recipe.name.lower()} (расход: {recipe.describe()})")
            print("7 — Рецепты и доступные чашки")
            print("8 — Приготовить несколько чашек одного напитка")
            print("9 — Рассчитать закупку под напиток")
            print("10 — Купить недостающие ингредиенты под напиток")
            print("11 — Пригласить посетителя")
            print("12 — Посмотреть текущий заказ")
            print("13 — Приготовить и продать текущий заказ")
            print("14 — Статистика продаж")
            print("0 — Выход (прогресс пока не сохраняется)")
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            if choice == "1":
                shop.show_status()
                continue
            if choice == "7":
                shop.show_recipes()
                continue
            if choice == "11":
                try:
                    shop.invite_visitor()
                except ValueError as error:
                    print(error)
                else:
                    print("Посетитель пришёл!")
                    shop.show_order()
                continue
            if choice == "12":
                shop.show_order()
                continue
            if choice == "14":
                shop.show_sales()
                continue
            if choice == "13":
                try:
                    total = shop.serve_order()
                except ValueError as error:
                    print(error)
                else:
                    print(f"Заказ выполнен! Получено: {total} руб. Можно пригласить следующего посетителя.")
                    shop.show_status()
                continue
            if choice in ("8", "9", "10"):
                print("Выберите напиток:")
                for number, key in drink_choices.items():
                    print(f"{number} — {RECIPES[key].name}")
                drink_key = drink_choices.get(input("Номер напитка: ").strip())
                if drink_key is None:
                    print("Неизвестный напиток. Выберите номер из списка.")
                    continue
                try:
                    quantity = int(input("Количество чашек: "))
                except ValueError:
                    print("Введите положительное целое количество чашек.")
                    continue
                try:
                    if choice in ("9", "10"):
                        total = shop.show_purchase_plan(drink_key, quantity)
                        if choice == "9":
                            continue
                        if total == 0:
                            print("Ингредиентов достаточно. Покупка не требуется.")
                            continue
                        if total > shop.budget:
                            print("Закупка не выполнена: недостаточно денег на весь план.")
                            continue
                        answer = input('Подтвердить покупку всех упаковок? Введите «да»: ')
                        if answer.strip().lower() != "да":
                            print("Закупка отменена. Бюджет и запасы не изменены.")
                            continue
                        cost = shop.buy_missing(drink_key, quantity)
                        print(f"Закупка выполнена. Потрачено: {cost} руб. Напитки не приготовлены.")
                        shop.show_status()
                        continue
                    shop.prepare_drink(drink_key, quantity)
                except ValueError as error:
                    print(error)
                else:
                    print(
                        f"Партия готова: {RECIPES[drink_key].name}, чашек: {quantity}. "
                        "Учебное приготовление без продажи; заказ не завершён."
                    )
                    shop.show_status()
                continue
            if choice in drink_choices:
                drink_key = drink_choices[choice]
                try:
                    shop.prepare_drink(drink_key)
                except ValueError as error:
                    print(error)
                else:
                    drink = RECIPES[drink_key].name
                    print(f"{drink} готов! Учебное приготовление без продажи; заказ не завершён.")
                    shop.show_status()
                continue
            ingredient = {"2": "coffee", "3": "milk"}.get(choice)
            if ingredient is None:
                options = ", ".join(["0", "1", "2", "3", *drink_choices, "7", "8", "9", "10", "11", "12", "13", "14"])
                print(f"Выберите пункт меню: {options}.")
                continue
            try:
                quantity = int(input("Количество упаковок: "))
            except ValueError:
                print("Введите положительное целое количество упаковок.")
                continue
            try:
                cost = shop.buy(ingredient, quantity)
            except ValueError as error:
                print(error)
            else:
                print(f"Покупка выполнена. Потрачено: {cost} руб.")
                shop.show_status()
    except (EOFError, KeyboardInterrupt):
        print()
    print("До встречи! Прогресс этой сессии не сохранён.")


if __name__ == "__main__":
    main()
