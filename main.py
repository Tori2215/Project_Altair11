import streamlit as st
import json
import os
from typing import Dict, Optional

# ================================
# РАБОТА С ФАЙЛАМИ (логика хранения)
# ================================
# Эти функции читают и сохраняют данные в JSON-файлы.
# Вы можете менять имена файлов, но не меняйте структуру данных,
# иначе другие функции перестанут работать.

GOALS_FILE = "goals.json"  # файл для целей
CATEGORIES_FILE = "categories.json"  # файл для категорий и их коэффициентов
MCC_FILE = "mcc_categories.json"  # файл для соответствия MCC кодов категориям
WALLET_FILE = "wallet.json"  # файл для хранения бюджета и расходов


def get_remaining_budget():
    """Возвращает остаток бюджета (единый для всего приложения)"""
    wallet_data = load_wallet()

    budget = wallet_data.get("budget", 0.0)
    expenses = wallet_data.get("expense_items", [])

    total_spent = sum(item['amount'] for item in expenses)

    return budget - total_spent

def load_goals():
    """Загружает словарь целей из JSON-файла.
       Возвращает: { "название цели": {"target": сумма, "saved": накоплено}, ... }
    """
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # если файла нет, возвращаем пустой словарь


def save_goals(goals):
    """Сохраняет словарь целей в JSON-файл."""
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=4)


def load_wallet():
    """Загружает данные кошелька (бюджет и расходы) из JSON-файла.
       Возвращает: { "budget": сумма, "expense_items": [список расходов] }
    """
    try:
        with open(WALLET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # если файла нет, возвращаем пустой кошелек
        return {"budget": 0.0, "expense_items": []}


def save_wallet(wallet_data):
    """Сохраняет данные кошелька в JSON-файл."""
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(wallet_data, f, ensure_ascii=False, indent=4)


def create_mcc_json_from_pdf():
    """Создает JSON файл с соответствием MCC кодов категориям на основе данных из PDF.
       Возвращает: { "5411": "Еда", "5541": "Авто", ... }
    """
    # Данные из PDF файла (извлеченные из description-mcc-categories.pdf)
    # Группы не учитываются, используются только категории
    mcc_mapping = {
        # ===== АВТО =====
        "Авто": [
            "5013", "5531", "5532", "5533", "5571", "7523", "7531", "7534", "7535", "7538", "7542", "7549",
            "5172", "5541", "5542", "5552", "5983",  # Заправки
            "4784"  # Платные дороги
        ],

        # ===== ДОМ И БЫТ =====
        "Дом и быт": [
            "5995", "0742",  # Животные
            "1520", "1711", "1731", "1740", "1750", "1761", "1771", "1799", "2842", "5021", "5039",
            "5046", "5051", "5065", "5072", "5074", "5085", "5198", "5200", "5211", "5231", "5251",
            "5261", "5415", "5712", "5713", "5714", "5718", "5719", "5950", "7622", "7623", "7629",
            "7641", "7692", "7699",  # Ремонт и мебель
            "7829", "7832"  # Кино
        ],

        # ===== ДОСУГ =====
        "Досуг": [
            "7841",  # Онлайн-кинотеатры
            "7929", "7932", "7933", "7993", "7994", "7996", "7998", "7999", "8664",  # Развлечения
            "0019", "5815", "5816", "5817", "5818"  # Цифровые товары
        ],

        # ===== КРАСОТА =====
        "Красота": [
            "5977", "7230", "7297", "7298"
        ],

        # ===== ЗДОРОВЬЕ =====
        "Здоровье": [
            "5122", "5292", "5295", "5912"
        ],

        # ===== ЕДА =====
        "Еда": [
            "5811", "5812", "5813",  # Рестораны
            "5297", "5298", "5411", "5412", "5422", "5441", "5451", "5462", "5499", "5715", "5921",  # Супермаркеты
            "5814"  # Фастфуд
        ],

        # ===== КУЛЬТУРА =====
        "Культура": [
            "5932", "5937", "5971", "5973", "7922", "7991",  # Искусство
            "5733", "5735",  # Музыка
            "8211", "8220", "8241", "8244", "8249", "8299", "8493", "8494", "8351"  # Образование
        ],

        # ===== ПУТЕШЕСТВИЯ =====
        "Путешествия": [
            "2741", "5111", "5192", "5942", "5943", "5994",  # Книги и канцтовары
            "3308", "3350", "4304", "4415", "4418", "4511", "4582",  # Авиабилеты (дополнительные)
            "4011", "4112",  # Ж/д билеты
            "5309"  # Duty Free
        ],

        # ===== СПОРТ =====
        "Спорт": [
            "5655", "5940", "5941",  # Спорттовары
            "7911", "7941", "7992", "7997"  # Тренировки
        ],

        # ===== ТРАНСПОРТ =====
        "Транспорт": [
            "7512", "7513", "7519",  # Каршеринг
            "4111",  # Местный транспорт
            "4121"  # Такси
        ],

        # ===== ШОППИНГ =====
        "Шоппинг": [
            "5722", "5732",  # Гаджеты и техника
            "5641", "5945",  # Детские товары
            "5137", "5139", "5611", "5621", "5631", "5651", "5661", "5681", "5691", "5697", "5698",
            "5699", "5931", "5948", "7296",  # Одежда и обувь
            "5947", "5949", "5970", "5972",  # Подарки и творчество
            "5193", "5992"  # Цветы
        ]
    }

    # Добавляем диапазоны MCC кодов (указываем все коды из диапазона)
    # Авиабилеты 3000-3303
    for code in range(3000, 3304):
        mcc_mapping["Путешествия"].append(str(code))

    # Каршеринг 3351-3441
    for code in range(3351, 3442):
        mcc_mapping["Транспорт"].append(str(code))

    # Создаем плоский словарь {MCC: категория}
    mcc_dict = {}
    for category, codes in mcc_mapping.items():
        for code in codes:
            # Приводим код к строке с ведущими нулями для 4-значных кодов
            code_str = code.zfill(4) if len(code) < 4 else code
            mcc_dict[code_str] = category

    # Сохраняем в JSON файл
    with open(MCC_FILE, "w", encoding="utf-8") as f:
        json.dump(mcc_dict, f, ensure_ascii=False, indent=4)

    return mcc_dict


def load_mcc_categories():
    """Загружает соответствие MCC кодов категориям из JSON файла.
       Возвращает: { "5411": "Еда", "5541": "Авто", ... }
       Если файла нет, создаёт его на основе данных из PDF.
    """
    try:
        with open(MCC_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # если файла нет, создаём его из данных PDF
        return create_mcc_json_from_pdf()


def load_categories():
    """Загружает категории и их коэффициенты (доли бюджета).
       Возвращает: { "Еда": 0.09, "Авто": 0.09, ... }
       Если файла нет, создаёт категории на основе MCC файла с равными коэффициентами.
    """
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Создаем категории на основе MCC файла с равными коэффициентами
        default = create_default_categories_from_mcc()
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
    if abs(total - 1.0) < 0.001:
        st.info("Сумма коэффициентов уже равна 1.")
        return
    factor = 1.0 / total
    for cat in categories:
        categories[cat] *= factor
    save_categories(categories)
    st.success(f"Коэффициенты нормализованы. Сумма была {total:.2f}, теперь 1.00.")


def create_default_categories_from_mcc():
    """Создает словарь категорий на основе MCC данных с равными коэффициентами.
       Возвращает: { "Еда": 0.09, "Авто": 0.09, "Досуг": 0.09, ... }
       Коэффициенты распределяются равномерно между всеми категориями (сумма = 1.0)
    """
    mcc_map = load_mcc_categories()
    if not mcc_map:
        # Если MCC карта пуста, возвращаем стандартные категории
        return {"еда": 0.33, "транспорт": 0.33, "сбережения": 0.34}

    # Получаем все уникальные категории из MCC маппинга
    unique_categories = sorted(set(mcc_map.values()))

    # Вычисляем равный коэффициент для каждой категории (сумма должна быть 1.0)
    equal_coeff = 1.0 / len(unique_categories) if unique_categories else 0

    # Создаем словарь категорий с равными коэффициентами
    categories = {category: equal_coeff for category in unique_categories}

    return categories


def get_category_by_mcc(mcc_code: int, mcc_map: Dict[str, str]) -> Optional[str]:
    """Определяет категорию по MCC коду.
       Возвращает название категории или None, если код не найден.
    """
    mcc_str = str(mcc_code).zfill(4)  # Добавляем ведущие нули если нужно
    return mcc_map.get(mcc_str)


# ================================
# СТРАНИЦА 1: ГЛАВНАЯ СТРАНИЦА
# ================================
# Здесь отображается информация о программе и её возможностях.
# Вы можете менять текст, добавлять картинки, менять оформление,
# но не удаляйте вызовы функций загрузки MCC данных.

def main_page():
    st.markdown("<h1 style='text-align:center'>Т-Финансы</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center'>Данная программа разработана для двух ключевых аудиторий: для подростков, которые только начинают знакомиться с управлением личными финансами, и для взрослых людей, уже имеющих свой бюджет и нуждающихся в его контроле.</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='background: #f0f2f6; padding:1rem; text-align:center; border-radius: 8px; color: #73797F'><strong>Помогает распределять доход по категориям, автоматически классифицирует транзакции, предупреждает о риске превышения лимитов и ведёт цели-накопления</strong></div>",
        unsafe_allow_html=True,
    )

    # Показываем информацию о текущем бюджете
    wallet_data = load_wallet()
    if wallet_data["budget"] > 0:
        expenses_count = len(wallet_data["expense_items"])
        if expenses_count > 0:
            remaining = get_remaining_budget()
            st.success(f"💰 **Текущий бюджет:** {remaining:.2f} ₽")
            st.info(f"📊 **Добавлено расходов:** {expenses_count} на сумму {remaining:.2f} ₽")
        else:
            st.success(f"💰 **Текущий бюджет:** {wallet_data['budget']:.2f} ₽")
            st.info("📊 **Добавлено расходов:** 0")
    else:
        st.info("💰 Бюджет ещё не установлен. Перейдите в раздел «Распределение расходов» для установки бюджета.")

    return


# ================================
# СТРАНИЦА 2: РАСПРЕДЕЛЕНИЕ РАСХОДОВ
# ================================
# ВСЕ ВИДЖЕТЫ STREAMLIT (st.number_input, st.button, st.write и т.д.)
# ОТВЕЧАЮТ ЗА ВНЕШНИЙ ВИД. ИХ МОЖНО ПЕРЕСТАВЛЯТЬ, МЕНЯТЬ НАДПИСИ,
# ДОБАВЛЯТЬ CSS (через st.markdown с style), НО НЕЛЬЗЯ УДАЛЯТЬ ЛОГИЧЕСКИЕ
# ВЫЗОВЫ ФУНКЦИЙ (анализ, сохранение и т.п.) И МЕНЯТЬ НАЗВАНИЯ ПЕРЕМЕННЫХ,
# КОТОРЫЕ ПЕРЕДАЮТСЯ В ЭТИ ФУНКЦИИ.

def page_expenses():
    st.markdown("<h2 style='text-align:center'>Распределение расходов по MCC кодам</h2>", unsafe_allow_html=True)

    # Загружаем соответствие MCC категориям
    mcc_map = load_mcc_categories()
    if not mcc_map:
        st.error("Не удалось загрузить базу MCC кодов.")
        return

    # Загружаем категории бюджета
    budget_categories = load_categories()
    if not budget_categories:
        st.warning("Нет ни одной категории бюджета.")
        return

    # Загружаем данные кошелька
    wallet_data = load_wallet()

    # Инициализация сессии для хранения расходов (синхронизируем с файлом)
    if 'expense_items' not in st.session_state:
        st.session_state.expense_items = wallet_data.get("expense_items", [])

    # --- Виджет для ввода бюджета ---
    current_budget = wallet_data.get("budget", 0.0)

    col1, col2 = st.columns([3, 1])
    with col1:
        budget = st.number_input("💰 Добавьте бюджет:", min_value=0.01, step=100.0, format="%.2f",
                                 value=current_budget if current_budget > 0 else 0.01, key="budget_input")
    with col2:
        if st.button("💾 Сохранить изменения", use_container_width=True):
            wallet_data["budget"] = budget
            save_wallet(wallet_data)
            st.success(f"✅ Бюджет {budget:.2f} ₽ сохранен в кошелек!")
            st.rerun()

    # Используем сохраненный бюджет из файла
    budget = wallet_data.get("budget", 0.0)

    if budget == 0:
        st.info("Введите бюджет и нажмите «Сохранить бюджет», чтобы начать анализ.")
        return

    # Вычисляем остаток бюджета
    remaining = get_remaining_budget()

    # Показываем остаток бюджета вверху страницы
    st.markdown("---")
    if remaining >= 0:
        st.success(f"💵 **Ваш остаток бюджета:** {remaining:.2f} ₽")
    else:
        st.error(f"⚠️ **Внимание! Превышение бюджета на {abs(remaining):.2f} ₽** (бюджет: {budget:.2f} ₽)")
    st.markdown("---")

    # Показываем информацию о распределении бюджета
    with st.expander("📊 Информация о распределении бюджета"):
        total_categories = len(budget_categories)
        st.info(f"💰 Бюджет распределяется между **{total_categories}** категориями.")

        # Показываем распределение по категориям
        category_data = []
        for cat, coeff in sorted(budget_categories.items()):
            limit = budget * coeff
            category_data.append({
                "Категория": cat,
                "Доля бюджета": f"{coeff * 100:.2f}%",
                "Лимит": f"{limit:.2f} ₽"
            })
        st.dataframe(category_data, use_container_width=True)

        total_coeff = sum(budget_categories.values())
        if abs(total_coeff - 1.0) > 0.001:
            st.warning(f"⚠️ Сумма коэффициентов: {total_coeff:.3f} (должна быть 1.000)")
            if st.button("🔧 Нормализовать коэффициенты"):
                normalize_categories(budget_categories)
                st.rerun()

    st.divider()

    # --- Добавление нового расхода по MCC ---
    st.subheader("➕ Добавить расход по MCC коду")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        mcc_code = st.number_input("MCC код", min_value=0, max_value=9999, step=1, format="%d", key="mcc_input")
        if mcc_code > 0:
            preview_category = get_category_by_mcc(mcc_code, mcc_map)
            if preview_category:
                st.success(f"🔍 Определяется как: **{preview_category}**")
            else:
                st.error(f"❌ MCC код {mcc_code} не найден в базе")

    with col2:
        amount = st.number_input("Сумма расхода (₽)", min_value=0.01, step=100.0, format="%.2f", key="amount_input")

    with col3:
        st.write("")
        st.write("")
        add_button = st.button("➕ Добавить расход", use_container_width=True, type="primary")

    # Обработка добавления расхода
    if add_button and amount > 0 and mcc_code > 0:
        # Проверяем, хватит ли денег в бюджете
        if amount > remaining:
            st.error(f"❌ Недостаточно средств! Остаток бюджета: {remaining:.2f} ₽, а расход: {amount:.2f} ₽")
        else:
            category = get_category_by_mcc(mcc_code, mcc_map)

            if category is None:
                st.error(f"❌ MCC код {mcc_code} не найден в базе. Пожалуйста, проверьте код.")
            elif category not in budget_categories:
                st.warning(
                    f"⚠️ Категория '{category}' не найдена в бюджете. Она будет добавлена автоматически с коэффициентом 0.01.")
                budget_categories[category] = 0.01
                save_categories(budget_categories)
                new_expense = {'mcc': mcc_code, 'amount': amount, 'category': category}
                st.session_state.expense_items.append(new_expense)
                wallet_data["expense_items"] = st.session_state.expense_items
                save_wallet(wallet_data)
                st.success(f"✅ Категория '{category}' добавлена. Расход добавлен: {amount:.2f} ₽")
                st.rerun()
            else:
                new_expense = {'mcc': mcc_code, 'amount': amount, 'category': category}
                st.session_state.expense_items.append(new_expense)
                wallet_data["expense_items"] = st.session_state.expense_items
                save_wallet(wallet_data)
                st.success(f"✅ Добавлен расход: MCC {mcc_code} → {category} → {amount:.2f} ₽")
                st.rerun()

    st.divider()

    # --- Отображение текущих расходов ---
    if st.session_state.expense_items:
        st.subheader("📋 Текущие расходы")

        expense_data = []
        total_spent = 0

        category_total = {}
        for item in st.session_state.expense_items:
            cat = item['category']
            category_total[cat] = category_total.get(cat, 0) + item['amount']
            total_spent += item['amount']

        for category, spent in sorted(category_total.items()):
            coeff = budget_categories.get(category, 0)
            recommended_limit = budget * coeff
            percent_of_limit = (spent / recommended_limit * 100) if recommended_limit > 0 else 0

            if spent > recommended_limit:
                status = "⚠️ Перерасход"
            elif spent == recommended_limit:
                status = "✓ Точно в лимит"
            else:
                status = "✅ В пределах нормы"

            expense_data.append({
                "Категория": category,
                "Потрачено": f"{spent:.2f} ₽",
                "Рекомендуемая сумма": f"{recommended_limit:.2f} ₽",
                "Процент от лимита": f"{percent_of_limit:.1f}%",
                "Статус": status
            })

        st.dataframe(expense_data, use_container_width=True, height=400)

        remaining = budget - total_spent
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Бюджет", f"{budget:.2f} ₽")
        col2.metric("💸 Всего потрачено", f"{total_spent:.2f} ₽", delta=f"{total_spent - budget:.2f}",
                    delta_color="inverse")
        col3.metric("💵 Остаток", f"{remaining:.2f} ₽", delta_color="normal")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Очистить все расходы", use_container_width=True):
                st.session_state.expense_items = []
                wallet_data["expense_items"] = []
                save_wallet(wallet_data)
                st.success("Все расходы очищены!")
                st.rerun()

        st.divider()

        # --- Кнопка запуска анализа ---
        if st.button("🔍 Провести анализ", use_container_width=True, type="primary"):
            st.subheader("📊 Анализ расходов")

            if total_spent > budget:
                st.error("😈 Вы превысили бюджет!")
            else:
                st.success("😎 Вы уложились в бюджет!")

            category_expenses = {}
            for item in st.session_state.expense_items:
                cat = item['category']
                category_expenses[cat] = category_expenses.get(cat, 0) + item['amount']

            st.subheader("📊 Детальный анализ по категориям")

            categories_with_stats = []
            for category in budget_categories.keys():
                spent = category_expenses.get(category, 0)
                limit = budget * budget_categories.get(category, 0)
                percent = (spent / limit * 100) if limit > 0 else 0
                categories_with_stats.append((category, spent, limit, percent))

            categories_with_stats.sort(key=lambda x: x[3], reverse=True)

            for category, spent, limit, percent in categories_with_stats:
                with st.expander(
                        f"**{category}** — потрачено {spent:.2f} ₽ / рекомендуемо {limit:.2f} ₽ ({percent:.1f}% от лимита)"):
                    if limit > 0:
                        progress = min(spent / limit, 1.0)
                        st.progress(progress)

                    if spent > limit:
                        over = spent - limit
                        st.warning(f"⚠️ Перерасход на {over:.2f} ₽")
                        if limit > 0:
                            st.warning(f"📈 Превышение на {(spent / limit - 1) * 100:.1f}%")
                        st.info(
                            f"💡 Рекомендация: Постарайтесь сократить траты в категории «{category}» на {over:.2f} ₽")
                    elif spent == 0:
                        st.info("💤 Нет расходов в этой категории")
                        st.info(f"💡 У вас есть свободный лимит {limit:.2f} ₽ в категории «{category}»")
                    else:
                        remaining_limit = limit - spent
                        st.success(f"✅ В пределах нормы. Остаток бюджета: {remaining_limit:.2f} ₽")
                        if limit > 0:
                            st.success(f"📊 Использовано {percent:.1f}% от лимита")

            if total_spent > budget:
                st.subheader("💡 Рекомендации по оптимизации")
                st.info(
                    "💡 Совет: Пересмотрите траты в категориях с перерасходом или перераспределите бюджет в разделе «Управление категориями».")



    else:
        st.info("💡 Пока нет добавленных расходов. Добавьте первый расход по MCC коду выше.")


# ================================
# СТРАНИЦА 3: УПРАВЛЕНИЕ ЦЕЛЯМИ
# ================================
# Здесь много виджетов: selectbox, expander, st.write, st.button.
# Все они отвечают только за интерфейс. Основные действия (создание,
# добавление, удаление) происходят в обработчиках кнопок.
# Вы можете переставить кнопки, изменить цвета (через CSS), добавить иконки,
# но не меняйте вызовы save_goals, load_goals и имена ключей в словаре goals.

def page_goals():
    st.header("🎯 Управление целями")
    goals = load_goals()

    if goals:
        st.subheader("📋 Существующие цели")
        goal_names = list(goals.keys())
        for i, name in enumerate(goal_names, 1):
            saved = goals[name]['saved']
            target = goals[name]['target']
            percent = (saved / target * 100) if target > 0 else 0

            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i}. **{name}** — накоплено {saved:.2f} / {target:.2f} ({percent:.1f}%)")
                if saved >= target:
                    st.success("✅ Цель достигнута! Поздравляем!")
                else:
                    st.write(f"   Осталось: {target - saved:.2f}")
        st.divider()

    with st.expander("➕ Создать новую цель"):
        new_name = st.text_input("Название цели")
        new_target = st.number_input("Нужная сумма", min_value=0.01, step=100.0, format="%.2f")
        if st.button("Создать цель"):
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
                st.rerun()

    if goals:
        with st.expander("💰 Добавить средства к цели"):
            selected = st.selectbox("Выберите цель", list(goals.keys()))
            amount = st.number_input("Сумма для добавления", min_value=0.01, step=100.0, format="%.2f")

            wallet_data = load_wallet()
            budget = wallet_data.get("budget", 0.0)
            expenses = wallet_data.get("expense_items", [])

            # считаем остаток
            remaining = get_remaining_budget()

            st.info(f"💰 Остаток бюджета: {remaining:.2f} ₽")

            if st.button("Добавить"):
                if amount <= 0:
                    st.error("Сумма должна быть положительной.")

                elif amount > remaining:
                    st.error(f"❌ Недостаточно средств! Доступно: {remaining:.2f} ₽")

                else:
                    # 1. добавляем в цель
                    goals[selected]['saved'] += amount
                    save_goals(goals)

                    # 2. добавляем как расход (уменьшает остаток)
                    new_expense = {
                        'mcc': 0,
                        'amount': amount,
                        'category': 'Сбережения'
                    }

                    expenses.append(new_expense)
                    wallet_data["expense_items"] = expenses
                    save_wallet(wallet_data)

                    st.success(f"✅ Добавлено {amount:.2f} ₽ к цели '{selected}'")
                    st.info("💸 Сумма учтена как расход (сбережения)")

                    st.rerun()

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
# СТРАНИЦА 4: УПРАВЛЕНИЕ КАТЕГОРИЯМИ
# ================================
# Здесь можно просматривать и изменять коэффициенты существующих категорий.
# Все UI-элементы – st.number_input, st.button, st.expander.
# Вы можете менять их расположение, добавлять пояснения, но не трогайте
# структуру словаря categories и вызовы save_categories / normalize_categories.

def page_categories():
    st.header("🏷️ Управление категориями и коэффициентами")
    categories = load_categories()

    st.subheader("📌 Текущие категории")
    if categories:
        total = sum(categories.values())

        category_data = []
        for cat, coeff in sorted(categories.items()):
            category_data.append({
                "Категория": cat,
                "Коэффициент": f"{coeff:.4f}",
                "Процент бюджета": f"{coeff * 100:.2f}%"
            })

        st.dataframe(category_data, use_container_width=True)
        st.info(f"**Сумма коэффициентов:** {total:.4f} (рекомендуется 1.0000)")

        if abs(total - 1.0) > 0.001:
            st.warning(f"Сумма коэффициентов не равна 1. Текущая сумма: {total:.4f}")
            if st.button("🔧 Нормализовать коэффициенты", use_container_width=True):
                normalize_categories(categories)
                st.rerun()
    else:
        st.warning("Нет категорий. Невозможно управлять.")
        return
    st.divider()

    with st.expander("✏️ Изменить коэффициент категории"):
        cat_to_edit = st.selectbox("Выберите категорию", sorted(list(categories.keys())))
        old_coeff = categories[cat_to_edit]
        new_val = st.number_input("Новый коэффициент", min_value=0.0, step=0.01, value=old_coeff, format="%.4f")

        if st.button("💾 Сохранить изменение", use_container_width=True):
            if new_val <= 0:
                st.error("Коэффициент должен быть положительным.")
            else:
                categories[cat_to_edit] = new_val
                total = sum(categories.values())
                if abs(total - 1.0) > 0.001:
                    st.warning(f"Сумма коэффициентов стала {total:.4f} (не равна 1.0)")
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

    with st.expander("🔄 Сбросить коэффициенты"):
        if st.button("Сбросить все коэффициенты к равным значениям", use_container_width=True):
            categories = create_default_categories_from_mcc()
            save_categories(categories)
            st.success("Коэффициенты сброшены к равным значениям!")
            st.rerun()


# ================================
# ГЛАВНОЕ МЕНЮ
# ================================
# ВОТ ЭТО ВНИЗУ ЛУЧШЕ НЕ ТРОГАТЬ

def main():
    # st.set_page_config настраивает заголовок вкладки браузера и ширину страницы
    st.set_page_config(page_title="Т-Финансы", layout="wide")

    # Кастомные стили для кнопок навигации (меняет цвет активной кнопки)
    st.markdown(
        '''
            <style>
                button[data-testid="stBaseButton-pillsActive"][kind="pillsActive"]{
                    background: #FFF7D2;
                    color: #D0AD00;
                    border: 1px solid;
                }
            </style>
        ''',
        unsafe_allow_html=True,
    )

    # st.pills создаёт горизонтальное меню навигации
    menu = st.pills(
        "Навигация",
        ["Главная", "Распределение расходов", "Управление целями", "Управление категориями"],
        selection_mode="single",
        default="Главная"
    )

    # Отображаем выбранную страницу
    if menu == "Главная":
        main_page()
    elif menu == "Распределение расходов":
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
