"""Симулятор кофейни: закупка ингредиентов и приготовление эспрессо."""

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

    def prepare_espresso(self) -> None:
        """Приготовить одну чашку; при нехватке кофе не менять состояние."""
        if self.stock["coffee"] < ESPRESSO_COFFEE_GRAMS:
            raise ValueError(
                f"Недостаточно кофе: нужно {ESPRESSO_COFFEE_GRAMS} г, "
                f"в запасе {self.stock['coffee']} г. Купите кофе."
            )
        self.stock["coffee"] -= ESPRESSO_COFFEE_GRAMS

    def show_status(self) -> None:
        print(f"\nБюджет: {self.budget} руб.")
        for key, item in INGREDIENTS.items():
            print(f"{item.name}: {self.stock[key]} {item.unit}")


def main() -> None:
    shop = CoffeeShop()
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
            print(f"4 — Приготовить эспрессо (расход: {ESPRESSO_COFFEE_GRAMS} г кофе)")
            print("0 — Выход (прогресс пока не сохраняется)")
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            if choice == "1":
                shop.show_status()
                continue
            if choice == "4":
                try:
                    shop.prepare_espresso()
                except ValueError as error:
                    print(error)
                else:
                    print("Эспрессо готов! Продажа напитков пока недоступна.")
                    shop.show_status()
                continue
            ingredient = {"2": "coffee", "3": "milk"}.get(choice)
            if ingredient is None:
                print("Выберите пункт меню: 0, 1, 2, 3 или 4.")
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
