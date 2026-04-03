import json

GOALS_FILE = "goals.json"
CATEGORIES_FILE = "categories.json"

def load_goals():
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=4)

def load_categories():
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        default = {
            "еда": 0.3,
            "транспорт": 0.2,
            "сбережения": 0.3
        }
        save_categories(default)
        return default

def save_categories(categories):
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

def normalize_categories(categories):
    if not categories:
        return
    total = sum(categories.values())
    if total == 0:
        return
    if total == 1:
        print("Сумма коэффициентов уже равна 1.")
        return
    factor = 1.0 / total
    for cat in categories:
        categories[cat] *= factor
    save_categories(categories)
    print(f"Коэффициенты нормализованы. Сумма была {total:.2f}, теперь 1.00.")

def menu():
    print('\n---Выберите функцию---')
    print('1 - распределение расходов')
    print('2 - создание и отслеживание целей')
    print('3 - управление категориями и коэффициентами')
    while True:
        choice = input('Ваш выбор (1, 2 или 3): ')
        if choice in ('1', '2', '3'):
            return choice
        else:
            print('Ошибка: введите 1, 2 или 3')

def get_bud():
    while True:
        try:
            budget = float(input("Добавь свой бюджет: "))
            if budget <= 0:
                print('ХАХЗАХАХАХ НИЩЕТА')
            else:
                return budget
        except ValueError:
            print('ОШИБКА! Неправильный ввод')

def get_kategorie(categories):
    expenses = {category: 0 for category in categories}
    print('\nДоступные категории:', ', '.join(categories.keys()))
    print("Введите расходы (введите 'стоп' для завершения):")
    while True:
        category = input("Категория: ")
        if category.lower() == "стоп":
            break
        if category not in categories:
            print("Ошибка, такой категории нет!")
            print(f"Доступные категории: {', '.join(categories.keys())}")
            continue
        while True:
            try:
                value = float(input(f'Сколько вы потратили на {category}: '))
                if value < 0:
                    print('Траты не могут быть отрицательными')
                    continue
                expenses[category] += value
                break
            except ValueError:
                print('Ошибка')
    return expenses

def anal(budget, expenses, limits):
    print('\n---Анализ бюджета---')
    total_spend = sum(expenses.values())
    print(f"Общий бюджет: {budget}")
    print(f"Всего потрачено: {total_spend}")
    if total_spend > budget:
        print("😈 Вы превысили бюджет!")
    else:
        print('😎 Вы уложились в бюджет!')

    print('\n---Анализ по категориям---')
    for category in expenses:
        spent = expenses[category]
        limit = budget * limits.get(category, 0)
        print(f'--{category}--')
        print(f'Потрачено: {spent:.2f}')
        print(f'Рекомендуемо тратить: {limit:.2f}')
        if spent > limit:
            print('Перерасход на этой категории')
        else:
            print('В пределах нормы')

    if total_spend > budget:
        print('\n---Рекомендации---')
        for category in expenses:
            spent = expenses[category]
            limit = budget * limits.get(category, 0)
            if spent > limit:
                diff = spent - limit
                print(f'Вы превысили бюджет по категории {category} на {diff:.2f}')

def list_goals_with_numbers(goals):
    if not goals:
        print("Нет созданных целей.")
        return []
    goal_names = list(goals.keys())
    print("Список целей:")
    for i, name in enumerate(goal_names, start=1):
        saved = goals[name]['saved']
        target = goals[name]['target']
        print(f"{i}. {name} — накоплено: {saved:.2f} / {target:.2f}")
    return goal_names

def create_goal(goals):
    name = input("Введите название цели: ")
    try:
        target = float(input("Введите нужную сумму: "))
        if target <= 0:
            print("Сумма должна быть положительной.")
            return
        goals[name] = {'target': target, 'saved': 0.0}
        save_goals(goals)
        print(f"Цель '{name}' создана. Нужно накопить {target}.")
    except ValueError:
        print("Ошибка ввода суммы.")

def add_to_goal(goals):
    if not goals:
        print("Нет созданных целей. Сначала создайте цель.")
        return

    goal_names = list_goals_with_numbers(goals)
    if not goal_names:
        return

    try:
        choice = int(input("Выберите номер цели: "))
        if choice < 1 or choice > len(goal_names):
            print("Неверный номер.")
            return
        selected_name = goal_names[choice - 1]
    except ValueError:
        print("Ошибка: введите число.")
        return

    try:
        amount = float(input(f"Сколько вы откладываете на '{selected_name}'? "))
        if amount <= 0:
            print("Сумма должна быть положительной.")
            return
        goals[selected_name]['saved'] += amount
        save_goals(goals)
        print(f"Добавлено {amount} к цели '{selected_name}'.")
    except ValueError:
        print("Ошибка ввода суммы.")

def show_progress(goals):
    if not goals:
        print("Нет созданных целей.")
        return
    print("\n--- Прогресс по целям ---")
    for i, (name, data) in enumerate(goals.items(), start=1):
        saved = data['saved']
        target = data['target']
        percent = (saved / target) * 100 if target > 0 else 0
        print(f"{i}. {name}: {saved:.2f} / {target:.2f} ({percent:.1f}%)")
        if saved >= target:
            print("   Цель достигнута! Поздравляем!")
        else:
            print(f"   Осталось: {target - saved:.2f}")

def delete_goal(goals):
    if not goals:
        print("Нет целей для удаления.")
        return

    goal_names = list_goals_with_numbers(goals)
    if not goal_names:
        return

    try:
        choice = int(input("Выберите номер цели для удаления: "))
        if choice < 1 or choice > len(goal_names):
            print("Неверный номер.")
            return
        selected_name = goal_names[choice - 1]
    except ValueError:
        print("Ошибка: введите число.")
        return

    del goals[selected_name]
    save_goals(goals)
    print(f"Цель '{selected_name}' удалена.")

def manage_goals():
    goals = load_goals()
    while True:
        print("\n--- Управление целями ---")
        print("1 - Создать цель")
        print("2 - Добавить средства")
        print("3 - Показать прогресс")
        print("4 - Удалить цель")
        print("5 - В меню")
        choice = input("Ваш выбор: ")
        if choice == '1':
            create_goal(goals)
        elif choice == '2':
            add_to_goal(goals)
        elif choice == '3':
            show_progress(goals)
        elif choice == '4':
            delete_goal(goals)
        elif choice == '5':
            break
        else:
            print("Неверный ввод. Попробуйте снова.")

def view_categories(categories):
    if not categories:
        print("Нет ни одной категории.")
        return
    print("\n--- Текущие категории и коэффициенты ---")
    for cat, coeff in categories.items():
        print(f"{cat}: {coeff * 100:.1f}% от бюджета")
    total_coeff = sum(categories.values())
    print(f"Сумма коэффициентов: {total_coeff:.2f} (рекомендуется 1.0)")

def add_category(categories):
    name = input("Введите название новой категории: ").strip()
    if not name:
        print("Название не может быть пустым.")
        return
    if name in categories:
        print("Такая категория уже существует.")
        return
    try:
        coeff = float(input("Введите коэффициент (доля от бюджета, например 0.2 для 20%): "))
        if coeff < 0:
            print("Коэффициент не может быть отрицательным.")
            return
        temp_cats = categories.copy()
        temp_cats[name] = coeff
        total = sum(temp_cats.values())
        if total > 1.0:
            print(f"Предупреждение: сумма коэффициентов станет {total:.2f} > 1.")
            answer = input("Автоматически нормализовать все коэффициенты? (y/n): ").lower()
            if answer == 'y':
                categories[name] = coeff
                normalize_categories(categories)
                print("Категория добавлена, все коэффициенты нормализованы.")
            else:
                print("Добавление отменено.")
            return
        categories[name] = coeff
        save_categories(categories)
        print(f"Категория '{name}' добавлена с коэффициентом {coeff}.")
    except ValueError:
        print("Ошибка: введите число.")

def edit_category(categories):
    if not categories:
        print("Нет категорий для редактирования.")
        return
    view_categories(categories)
    name = input("Введите название категории для редактирования: ").strip()
    if name not in categories:
        print("Категория не найдена.")
        return
    try:
        new_coeff = float(input(f"Введите новый коэффициент для '{name}': "))
        if new_coeff < 0:
            print("Коэффициент не может быть отрицательным.")
            return
        old_coeff = categories[name]
        categories[name] = new_coeff
        total = sum(categories.values())
        if total > 1.0:
            print(f"Сумма коэффициентов стала {total:.2f} > 1.")
            answer = input("Вернуть старое значение? (n) / нормализовать все (y): ").lower()
            if answer == 'n':
                categories[name] = old_coeff
                print("Изменение отменено, коэффициент восстановлен.")
            elif answer == 'y':
                normalize_categories(categories)
                print("Коэффициенты нормализованы.")
            else:
                print("ОШИБКА")
            save_categories(categories)
            return
        save_categories(categories)
        print(f"Коэффициент категории '{name}' обновлён на {new_coeff}.")
    except ValueError:
        print("Ошибка: введите число.")

def delete_category(categories):
    if not categories:
        print("Нет категорий для удаления.")
        return
    view_categories(categories)
    name = input("Введите название категории для удаления: ").strip()
    if name not in categories:
        print("Категория не найдена.")
        return
    del categories[name]
    if not categories:
        save_categories(categories)
        print(f"Категория '{name}' удалена. Категорий не осталось.")
        return
    total = sum(categories.values())
    if total != 1.0:
        factor = 1.0 / total
        for cat in categories:
            categories[cat] *= factor
        print(f"Коэффициенты перераспределены. Сумма была {total:.2f}, теперь 1.00.")
    save_categories(categories)
    print(f"Категория '{name}' удалена, коэффициенты остальных категорий пересчитаны.")

def manage_categories():
    categories = load_categories()
    while True:
        print("\n--- Управление категориями и коэффициентами ---")
        print("1 - Просмотреть категории")
        print("2 - Добавить категорию")
        print("3 - Изменить коэффициент категории")
        print("4 - Удалить категорию")
        print("5 - В главное меню")
        choice = input("Ваш выбор: ")
        if choice == '1':
            view_categories(categories)
        elif choice == '2':
            add_category(categories)
            categories = load_categories()
        elif choice == '3':
            edit_category(categories)
            categories = load_categories()
        elif choice == '4':
            delete_category(categories)
            categories = load_categories()

        elif choice == '5':
            break
        else:
            print("Неверный ввод. Попробуйте снова.")

def main():
    while True:
        choice = menu()
        if choice == '1':
            categories = load_categories()
            if not categories:
                print("Нет ни одной категории. Пожалуйста, сначала создайте категории (пункт 3).")
                continue
            budget = get_bud()
            expenses = get_kategorie(categories)
            anal(budget, expenses, categories)
        elif choice == '2':
            manage_goals()
        elif choice == '3':
            manage_categories()

if __name__ == '__main__':
    main()
