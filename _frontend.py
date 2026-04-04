import streamlit as st
import json
import os

# ================================
# РАБОТА С ФАЙЛАМИ (логика хранения)
# ================================
# Эти функции читают и сохраняют данные в JSON-файлы.
# Вы можете менять имена файлов, но не меняйте структуру данных,
# иначе другие функции перестанут работать.

GOALS_FILE = "goals.json"        # файл для целей
CATEGORIES_FILE = "categories.json" # файл для категорий

def load_goals():
    """Загружает словарь целей из JSON-файла.
       Возвращает: { "название цели": {"target": сумма, "saved": накоплено}, ... }
    """
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}   # если файла нет, возвращаем пустой словарь

def save_goals(goals):
    """Сохраняет словарь целей в JSON-файл."""
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=4)

def load_categories():
    """Загружает категории и их коэффициенты (доли бюджета).
       Возвращает: { "еда": 0.3, "транспорт": 0.2, ... }
       Если файла нет, создаёт стандартные категории.
    """
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
    """Сохраняет словарь категорий в JSON-файл."""
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

def normalize_categories(categories):
    """Приводит сумму коэффициентов категорий к 1.0.
       Используется, когда после добавления/изменения сумма != 1.
    """
    if not categories:
        return
    total = sum(categories.values())
    if total == 0:
        return
    if total == 1.0:
        st.info("Сумма коэффициентов уже равна 1.")
        return
    factor = 1.0 / total
    for cat in categories:
        categories[cat] *= factor
    save_categories(categories)
    st.success(f"Коэффициенты нормализованы. Сумма была {total:.2f}, теперь 1.00.")

# ================================
# СТРАНИЦА 1: РАСПРЕДЕЛЕНИЕ РАСХОДОВ
# ================================
# ВСЕ ВИДЖЕТЫ STREAMLIT (st.number_input, st.button, st.write и т.д.)
# ОТВЕЧАЮТ ЗА ВНЕШНИЙ ВИД. ИХ МОЖНО ПЕРЕСТАВЛЯТЬ, МЕНЯТЬ НАДПИСИ,
# ДОБАВЛЯТЬ CSS (через st.markdown с style), НО НЕЛЬЗЯ УДАЛЯТЬ ЛОГИЧЕСКИЕ
# ВЫЗОВЫ ФУНКЦИЙ (analiz, сохранение и т.п.) И МЕНЯТЬ НАЗВАНИЯ ПЕРЕМЕННЫХ,
# КОТОРЫЕ ПЕРЕДАЮТСЯ В ЭТИ ФУНКЦИИ.

def page_expenses():
    st.header("📊 Распределение расходов")
    categories = load_categories()
    if not categories:
        st.warning("Нет ни одной категории. Сначала создайте категории в разделе «Управление категориями».")
        return

    # --- Виджет для ввода бюджета ---
    # st.number_input создаёт поле ввода числа. Меняя label, min_value, step, format
    # вы меняете только внешний вид, логика остаётся (budget = значение поля).
    budget = st.number_input("💰 Ваш бюджет на период", min_value=0.01, step=100.0, format="%.2f")
    if budget == 0:
        st.info("Введите бюджет, чтобы начать анализ.")
        return

    st.subheader("✏️ Введите расходы по категориям")
    expenses = {}
    # Используем две колонки для красивого расположения полей ввода.
    # Можно менять количество колонок или убрать их совсем – это только UI.
    cols = st.columns(2)
    for i, (cat, coeff) in enumerate(categories.items()):
        with cols[i % 2]:
            spent = st.number_input(f"{cat}", min_value=0.0, step=10.0, key=f"exp_{cat}", format="%.2f")
            expenses[cat] = spent

    # --- Кнопка запуска анализа ---
    if st.button("🔍 Провести анализ"):
        total_spent = sum(expenses.values())

        # Вывод метрик (два блока с большими цифрами)
        # st.metric – это виджет, который красиво показывает значение и изменение.
        # Его можно заменить на обычный st.write, если не нравится стиль.
        col1, col2 = st.columns(2)
        col1.metric("Общий бюджет", f"{budget:.2f}")
        col2.metric("Всего потрачено", f"{total_spent:.2f}", delta=f"{total_spent - budget:.2f}", delta_color="inverse")

        if total_spent > budget:
            st.error("😈 Вы превысили бюджет!")
        else:
            st.success("😎 Вы уложились в бюджет!")

        # Анализ по каждой категории с прогресс-баром
        # st.expander создаёт раскрывающийся блок – чисто визуальный элемент.
        for cat, spent in expenses.items():
            limit = budget * categories.get(cat, 0)
            with st.expander(f"**{cat}** — потрачено {spent:.2f} / рекомендуемо {limit:.2f}"):
                progress = min(spent / limit, 1.0) if limit > 0 else 0
                st.progress(progress)   # горизонтальная полоска прогресса
                if spent > limit:
                    st.warning(f"Перерасход на {spent - limit:.2f}")
                else:
                    st.success("В пределах нормы")

        # Рекомендации при перерасходе
        if total_spent > budget:
            st.subheader("💡 Рекомендации")
            for cat, spent in expenses.items():
                limit = budget * categories.get(cat, 0)
                if spent > limit:
                    st.write(f"- По категории **{cat}** перерасход **{spent - limit:.2f}**")

# ================================
# СТРАНИЦА 2: УПРАВЛЕНИЕ ЦЕЛЯМИ
# ================================
# Здесь много виджетов: selectbox, expander, st.write, st.button.
# Все они отвечают только за интерфейс. Основные действия (создание,
# добавление, удаление) происходят в обработчиках кнопок.
# Вы можете переставить кнопки, изменить цвета (через CSS), добавить иконки,
# но не меняйте вызовы save_goals, load_goals и имена ключей в словаре goals.

def page_goals():
    st.header("🎯 Управление целями")
    goals = load_goals()

    # Отображение существующих целей
    if goals:
        st.subheader("📋 Существующие цели")
        goal_names = list(goals.keys())
        for i, name in enumerate(goal_names, 1):
            saved = goals[name]['saved']
            target = goals[name]['target']
            percent = (saved / target * 100) if target > 0 else 0
            st.write(f"{i}. **{name}** — накоплено {saved:.2f} / {target:.2f} ({percent:.1f}%)")
            if saved >= target:
                st.success("✅ Цель достигнута! Поздравляем!")
            else:
                st.write(f"   Осталось: {target - saved:.2f}")
        st.divider()

    # Блок создания новой цели (обёрнут в st.expander – раскрывашку)
    with st.expander("➕ Создать новую цель"):
        new_name = st.text_input("Название цели")
        new_target = st.number_input("Нужная сумма", min_value=0.01, step=100.0, format="%.2f")
        if st.button("Создать цель"):
            # Валидация введённых данных
            if not new_name:
                st.error("Название не может быть пустым.")
            elif new_target <= 0:
                st.error("Сумма должна быть положительной.")
            elif new_name in goals:
                st.error("Цель с таким названием уже существует.")
            else:
                goals[new_name] = {'target': new_target, 'saved': 0.0}
                save_goals(goals)
                st.success(f"Цель '{new_name}' создана. Нужно накопить {new_target}.")
                st.rerun()   # перезагружает страницу, чтобы сразу показать новую цель

    # Блок добавления средств к существующей цели
    if goals:
        with st.expander("💰 Добавить средства к цели"):
            selected = st.selectbox("Выберите цель", list(goals.keys()))
            amount = st.number_input("Сумма для добавления", min_value=0.01, step=100.0, format="%.2f")
            if st.button("Добавить"):
                if amount <= 0:
                    st.error("Сумма должна быть положительной.")
                else:
                    goals[selected]['saved'] += amount
                    save_goals(goals)
                    st.success(f"Добавлено {amount} к цели '{selected}'.")
                    st.rerun()

    # Блок удаления цели
    if goals:
        with st.expander("🗑️ Удалить цель"):
            selected_del = st.selectbox("Выберите цель для удаления", list(goals.keys()), key="del_goal")
            if st.button("Удалить цель"):
                del goals[selected_del]
                save_goals(goals)
                st.success(f"Цель '{selected_del}' удалена.")
                st.rerun()
    else:
        st.info("Пока нет целей. Создайте первую цель.")

# ================================
# СТРАНИЦА 3: УПРАВЛЕНИЕ КАТЕГОРИЯМИ
# ================================
# Здесь можно добавлять/удалять категории и менять их веса (коэффициенты).
# Все UI-элементы – st.number_input, st.selectbox, st.button, st.expander.
# Вы можете менять их расположение, добавлять пояснения, но не трогайте
# структуру словаря categories и вызовы save_categories / normalize_categories.

def page_categories():
    st.header("🏷️ Управление категориями и коэффициентами")
    categories = load_categories()

    # Просмотр текущих категорий
    st.subheader("📌 Текущие категории")
    if categories:
        total = sum(categories.values())
        for cat, coeff in categories.items():
            st.write(f"- **{cat}**: {coeff*100:.1f}% от бюджета")
        st.info(f"Сумма коэффициентов: {total:.2f} (рекомендуется 1.0)")
        if abs(total - 1.0) > 0.001:
            if st.button("🔧 Нормализовать коэффициенты"):
                normalize_categories(categories)
                st.rerun()
    else:
        st.warning("Нет категорий. Добавьте первую.")
    st.divider()

    # Добавление категории
    with st.expander("➕ Добавить категорию"):
        new_cat = st.text_input("Название новой категории")
        new_coeff = st.number_input("Коэффициент (доля бюджета, например 0.2 для 20%)", min_value=0.0, step=0.05, format="%.3f")
        if st.button("Добавить категорию"):
            if not new_cat:
                st.error("Название не может быть пустым.")
            elif new_cat in categories:
                st.error("Такая категория уже существует.")
            elif new_coeff <= 0:
                st.error("Коэффициент должен быть положительным.")
            else:
                # Проверяем, не превысит ли сумма 1 после добавления
                temp_cats = categories.copy()
                temp_cats[new_cat] = new_coeff
                total_temp = sum(temp_cats.values())
                if total_temp > 1.0:
                    st.warning(f"Сумма коэффициентов станет {total_temp:.2f} > 1.")
                    # В Streamlit нельзя напрямую вложить кнопку в условие и ждать второго нажатия,
                    # поэтому предлагаем отдельную кнопку нормализации.
                    if st.button("✅ Нормализовать все коэффициенты"):
                        categories[new_cat] = new_coeff
                        normalize_categories(categories)
                        st.success("Категория добавлена, коэффициенты нормализованы.")
                        st.rerun()
                    else:
                        st.info("Добавление отменено. Нажмите кнопку выше, если хотите нормализовать.")
                else:
                    categories[new_cat] = new_coeff
                    save_categories(categories)
                    st.success(f"Категория '{new_cat}' добавлена с коэффициентом {new_coeff}.")
                    st.rerun()

    # Редактирование коэффициента существующей категории
    if categories:
        with st.expander("✏️ Изменить коэффициент категории"):
            cat_to_edit = st.selectbox("Выберите категорию", list(categories.keys()))
            old_coeff = categories[cat_to_edit]
            new_val = st.number_input("Новый коэффициент", min_value=0.0, step=0.05, value=old_coeff, format="%.3f")
            if st.button("Изменить"):
                if new_val <= 0:
                    st.error("Коэффициент должен быть положительным.")
                else:
                    categories[cat_to_edit] = new_val
                    total = sum(categories.values())
                    if total > 1.0:
                        st.warning(f"Сумма коэффициентов стала {total:.2f} > 1.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔙 Вернуть старое значение"):
                                categories[cat_to_edit] = old_coeff
                                save_categories(categories)
                                st.success("Изменение отменено, коэффициент восстановлен.")
                                st.rerun()
                        with col2:
                            if st.button("⚖️ Нормализовать все"):
                                normalize_categories(categories)
                                st.success("Коэффициенты нормализованы.")
                                st.rerun()
                    else:
                        save_categories(categories)
                        st.success(f"Коэффициент категории '{cat_to_edit}' обновлён на {new_val}.")
                        st.rerun()

    # Удаление категории
    if categories:
        with st.expander("🗑️ Удалить категорию"):
            cat_to_del = st.selectbox("Выберите категорию для удаления", list(categories.keys()), key="del_cat")
            if st.button("Удалить категорию"):
                del categories[cat_to_del]
                if not categories:
                    save_categories(categories)
                    st.success(f"Категория '{cat_to_del}' удалена. Категорий не осталось.")
                else:
                    total = sum(categories.values())
                    if total != 1.0:
                        factor = 1.0 / total
                        for cat in categories:
                            categories[cat] *= factor
                        st.info("Коэффициенты перераспределены, их сумма теперь 1.00.")
                    save_categories(categories)
                    st.success(f"Категория '{cat_to_del}' удалена, коэффициенты остальных категорий пересчитаны.")
                st.rerun()

# ================================
# ГЛАВНОЕ МЕНЮ (БОКОВАЯ ПАНЕЛЬ)
# ================================
#ВОТ ЭТО ВНИЗУ ЛУЧШЕ НЕ ТРОГАТЬ

def main():
    # st.set_page_config настраивает заголовок вкладки браузера и ширину страницы
    st.set_page_config(page_title="Т-Финансы", layout="wide")
    
    menu = st.radio(
        "Навигация",
        ["Меню", "Распределение расходов", "Управление целями", "Управление категориями"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if menu == "Распределение расходов":
        page_expenses()
    elif menu == "Управление целями":
        page_goals()
    else:
        page_categories()


# ================================
# ТОЧКА ВХОДА
# ================================
if __name__ == "__main__":
    main()