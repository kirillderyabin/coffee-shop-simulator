"""Первый этап симулятора кофейни: бюджет и закупка ингредиентов."""

from dataclasses import dataclass, field


# Все суммы указаны в целых рублях, ингредиенты покупаются упаковками.
INGREDIENTS = {
    "coffee": ("Кофе", "пачка 250 г", 300),
    "milk": ("Молоко", "пакет 1 л", 100),
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
        cost = INGREDIENTS[ingredient][2] * quantity
        if cost > self.budget:
            raise ValueError(
                f"Недостаточно денег: нужно {cost} руб., доступно {self.budget} руб."
            )
        self.budget -= cost
        self.stock[ingredient] += quantity
        return cost

    def show_status(self) -> None:
        print(f"\nБюджет: {self.budget} руб.")
        for key, (name, unit, _) in INGREDIENTS.items():
            print(f"{name} ({unit}): {self.stock[key]} шт.")


def main() -> None:
    shop = CoffeeShop()
    print("Добро пожаловать в Coffee Shop Simulator!")
    shop.show_status()
    try:
        while True:
            print("\n1 — Бюджет и запасы")
            for number, (_, (name, unit, price)) in enumerate(
                INGREDIENTS.items(), start=2
            ):
                print(f"{number} — Купить: {name}, {unit} — {price} руб.")
            print("0 — Выход (прогресс пока не сохраняется)")
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            if choice == "1":
                shop.show_status()
                continue
            ingredient = {"2": "coffee", "3": "milk"}.get(choice)
            if ingredient is None:
                print("Выберите пункт меню: 0, 1, 2 или 3.")
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
