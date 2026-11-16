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
    milk_ml: int = 0

    def requirements(self) -> dict[str, int]:
        amounts = {"coffee": self.coffee_grams, "milk": self.milk_ml}
        return {key: amount for key, amount in amounts.items() if amount > 0}


# Порядок каталога сохраняет пункты меню: 4 — эспрессо, 5 — латте, 6 — капучино.
RECIPES = {
    "espresso": Recipe("Эспрессо", ESPRESSO_COFFEE_GRAMS),
    "latte": Recipe("Латте", LATTE_COFFEE_GRAMS, LATTE_MILK_ML),
    "cappuccino": Recipe("Капучино", 18, 120),
}


@dataclass
class CoffeeShop:
    budget: int = 3000
    stock: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in INGREDIENTS}
    )

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

    def prepare_drink(self, drink: str) -> None:
        """Проверить весь рецепт перед списанием ингредиентов для одной чашки."""
        if drink not in RECIPES:
            raise ValueError("Неизвестный напиток.")
        requirements = RECIPES[drink].requirements()
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

    def show_status(self) -> None:
        print(f"\nБюджет: {self.budget} руб.")
        for key, item in INGREDIENTS.items():
            print(f"{item.name}: {self.stock[key]} {item.unit}")


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
                amounts = ", ".join(
                    f"{INGREDIENTS[item].name.lower()}: {amount} {INGREDIENTS[item].unit}"
                    for item, amount in recipe.requirements().items()
                )
                print(f"{number} — Приготовить {recipe.name.lower()} (расход: {amounts})")
            print("0 — Выход (прогресс пока не сохраняется)")
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            if choice == "1":
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
                    print(f"{drink} готов! Продажа напитков пока недоступна.")
                    shop.show_status()
                continue
            ingredient = {"2": "coffee", "3": "milk"}.get(choice)
            if ingredient is None:
                options = ", ".join(["0", "1", "2", "3", *drink_choices])
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
