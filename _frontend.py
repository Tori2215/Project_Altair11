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


def display_budget_remaining():
    """Отображает остаток бюджета вверху страницы"""
    remaining = get_remaining_budget()
    wallet_data = load_wallet()
    budget = wallet_data.get("budget", 0.0)
    expenses = wallet_data.get("expense_items", [])
    total_spent = sum(item['amount'] for item in expenses)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Бюджет", f"{budget:.2f} ₽")
    with col2:
        st.metric("Потрачено", f"{total_spent:.2f} ₽", delta=f"{total_spent - budget:.2f}" if budget > 0 else None,
                  delta_color="inverse")
    with col3:
        if remaining >= 0:
            st.metric("Остаток", f"{remaining:.2f} ₽")
        else:
            st.metric("Остаток", f"{remaining:.2f} ₽", delta="Перерасход!", delta_color="inverse")
    st.markdown("---")


# ================================
# СТРАНИЦА 1: ГЛАВНАЯ СТРАНИЦА
# ================================
# Здесь отображается информация о программе и её возможностях.
# Вы можете менять текст, добавлять картинки, менять оформление,
# но не удаляйте вызовы функций загрузки MCC данных.

def main_page():
    st.markdown("<h1 style='text-align:center'>Т-Финансы</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center'>Данная программа разработана для двух ключевых аудиторий: для подростков, которые только начинают знакомиться с управлением личными финансами, и для взрослых людей, уже имеющих свой бюджет и нуждающихся в его контроле</p>", unsafe_allow_html=True)
    st.markdown(
        "<div style='background: #f0f2f6; padding:1rem; text-align:center; border-radius: 8px; color: #73797F'><strong>Помогает распределять доход по категориям, автоматически классифицирует транзакции, предупреждает о риске превышения лимитов и ведёт цели-накопления</strong></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<style>.frffrfr img{height: 100px;}</style>", 
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown("<div class='frffrfr'>", unsafe_allow_html=True)
        st.image("https://imgproxy.cdn-tinkoff.ru/compressed95/aHR0cHM6Ly9jZG4udGJhbmsucnUvc3RhdGljL3BhZ2VzL2ZpbGVzL2JmYzY4ZGYxLTUyOWQtNDBlZi1iNTk2LWM0NThjMmM0MjA3Mi5wbmc=")
        st.markdown("</div>", unsafe_allow_html=True)

    # Показываем информацию о текущем бюджете
    wallet_data = load_wallet()
    if wallet_data["budget"] > 0:
        expenses_count = len(wallet_data["expense_items"])
        if expenses_count > 0:
            remaining = get_remaining_budget()
            st.markdown(
                f"<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
                f"Текущий бюджет: {remaining:.2f} ₽<br>"
                f"Добавлено расходов: {expenses_count} на сумму {remaining:.2f} ₽"
                f"</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
                f"Текущий бюджет: {wallet_data['budget']:.2f} ₽<br>"
                f"Добавлено расходов: 0"
                f"</div></div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            "<div style='padding: 1rem; text-align: center; border-radius: 8px; color: #B09545; background: #FFFFE7'>"
            "Бюджет ещё не установлен. Перейдите в раздел настроек.</div>",
            unsafe_allow_html=True
        )

    st.markdown(
        '''
            <h3 style='text-align: center'>Короткий факт</h3>

            <table style='width: 100%; border: 2px dashed #FEE120;'>
                <td style="width: 50%">
                    <p style='text-align: center'>Попробуйте правило 50/30/20.<br> 50% дохода — на обязательные траты (еда, проезд, связь), 30% — на желания (кино, кофе, подписки), 20% — на накопления.</p>
                </td>
            </table>
        ''',
        unsafe_allow_html=True
    )

    st.markdown(
        '''
            <div style='text-align: center; border-radius: 8px; padding: 1rem'><h4>Присоединяйтесь к комьюнити</h4></div>
            <div style='text-align: center'><p>Подписывайтесь на нас в соцсетях: узнавайте о старте наборов, вдохновляйтесь<br> историями участников и следите за анонсами мероприятий</p></div>
        ''',
        unsafe_allow_html=True
    )
    st.markdown(
        '''
        <table style='margin-left: auto; margin-right: auto; border-collapse: separate; border-spacing: 10px; width: 100%'>
                <td>
                    <div style='text-align: center'>
                        <img src='https://cdn-icons-png.flaticon.com/128/3800/3800059.png' height='40px' width='40px' /><br>
                        <a href='https://t.me/+lOWsSXCcg0NmZGYy'>Публикуем анонсы программ<br> и мероприятий</a>
                    </div>
                </td>
                <td>
                    <div style='text-align: center'>
                        <img src='https://cdn-icons-png.flaticon.com/512/16546/16546797.png' height='45px' width='45px' /><br>
                        <a href='https://vk.com/teducation'>Все, что есть в Телеграме, доступно<br> и в ВК</a>
                    </div>
                </td>
                <td>
                    <div style='text-align: center '>
                        <img src='https://cdn-icons-png.flaticon.com/128/1077/1077046.png' height='45px' width='45px' /><br>
                        <a href='https://www.youtube.com/@tbank_education'>Выкладываем разборы задач<br> и записи лекций</a>
                    </div>
                </td>
                <td>
                    <div style='text-align: center'>
                        <img src='https://www.svgrepo.com/show/504824/rutube.svg' height='45px' width='45px' /><br>
                        <a href='https://rutube.ru/channel/45817137/'>Дублируем все, что есть на<br>Ютубе</a>
                    </div>
                </td>
        </table>
        ''',
        unsafe_allow_html=True
    )

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
    st.image("https://imgproxy.cdn-tinkoff.ru/compressed95/aHR0cHM6Ly9jZG4udGJhbmsucnUvc3RhdGljL3BhZ2VzL2ZpbGVzLzUyNWRlYWYzLTVkMzItNDhkMS04ZjYwLTFkOWFmZThjNTBkNi5wbmc=")

    st.markdown("<h2 style='text-align:center'>Распределение расходов по MCC кодам</h2>", unsafe_allow_html=True)

    # Загружаем соответствие MCC категориям
    mcc_map = load_mcc_categories()
    if not mcc_map:
        st.warning("Не удалось загрузить базу MCC кодов.")
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
    
    st.markdown("<h5>Добавьте бюджет</h5>", unsafe_allow_html=True)
    budget = st.number_input("", min_value=0.01, step=100.0, format="%.2f",
                                 value=current_budget if current_budget > 0 else 0.01, key="budget_input")
    if st.button("Сохранить изменения", use_container_width=True):
        wallet_data["budget"] = budget
        save_wallet(wallet_data)
        st.warning(f"Бюджет {budget:.2f} ₽ сохранен в кошелек!")
        st.rerun()

    # Используем сохраненный бюджет из файла
    budget = wallet_data.get("budget", 0.0)

    if budget == 0:
        st.warning("Введите бюджет и нажмите «Сохранить бюджет», чтобы начать анализ.")
        return

    # Вычисляем остаток бюджета
    remaining = get_remaining_budget()

    # Показываем остаток бюджета вверху страницы
    st.markdown("---")
    if remaining >= 0:
        st.warning(f"**Ваш остаток бюджета:** {remaining:.2f} ₽")
    else:
        st.warning(f"**Внимание! Превышение бюджета на {abs(remaining):.2f} ₽** (бюджет: {budget:.2f} ₽)")
    st.markdown("---")

    # Показываем информацию о распределении бюджета
    with st.expander("Информация о распределении бюджета"):
        total_categories = len(budget_categories)
        st.warning(f"Бюджет распределяется между **{total_categories}** категориями.")

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
            st.warning(f"Сумма коэффициентов: {total_coeff:.3f} (должна быть 1.000)")
            if st.button("Нормализовать коэффициенты"):
                normalize_categories(budget_categories)
                st.rerun()

    # --- Добавление нового расхода по MCC ---
    st.markdown("<h2 style='text-align: center'>Добавить расход по MCC коду</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 2])

    with col1:
        mcc_code = st.number_input("MCC код", min_value=0, max_value=9999, step=1, format="%d", key="mcc_input")
        if mcc_code > 0:
            preview_category = get_category_by_mcc(mcc_code, mcc_map)
            if preview_category:
                st.warning(f"Определяется как: **{preview_category}**")
            else:
                st.warning(f"MCC код {mcc_code} не найден в базе")

    with col2:
        amount = st.number_input("Сумма расхода (₽)", min_value=0.01, step=100.0, format="%.2f", key="amount_input")

    st.write("")
    st.write("")
    st.markdown("""
        <style>
            div.stButton > button[kind="primary"] {
                background-color: #FFFFE7;
                border-color: #B09545;
                color: #B09545;
            }

            /* При наведении */
            div.stButton > button[kind="primary"]:hover {
                background-color: #F8D980;
                border-color: #F8D980; 
                color: white;
            }

            /* При нажатии */
            div.stButton > button[kind="primary"]:active {
                background-color: #FFFFE7;
                border-color: #B09545;
                color: #B09545;
            }
        </style>
    """, unsafe_allow_html=True)

    add_button = st.button("Добавить расход", use_container_width=True, type="primary")

    uploaded_file = st.file_uploader("Загрузите изображение чека", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)    
        recognized_text = st.image(image, caption="Загруженное изображение", use_container_width=True)

        st.markdown("""
        <style>
            div.stButton > button[kind="primary"] {
                background-color: #FFFFE7;
                border-color: #B09545;
                color: #B09545;
            }

            /* При наведении */
            div.stButton > button[kind="primary"]:hover {
                background-color: #F8D980;
                border-color: #F8D980; 
                color: white;
            }

            /* При нажатии */
            div.stButton > button[kind="primary"]:active {
                background-color: #FFFFE7;
                border-color: #B09545;
                color: #B09545;
            }
        </style>
    """, unsafe_allow_html=True)
        
        if st.button("Добавить расход", type="primary"):
            # Здесь ваша логика сохранения расхода
            st.success("Расход добавлен (демо)")
    else:
        st.markdown(
            "<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1px; border-radius: 8px;'><p>Загрузите изображение чека, чтобы начать распознавание</p></div></div>",
            unsafe_allow_html=True
        )

    # Обработка добавления расхода
    if add_button and amount > 0 and mcc_code > 0:
        # Проверяем, хватит ли денег в бюджете
        if amount > remaining:
            st.warning(f"Недостаточно средств! Остаток бюджета: {remaining:.2f} ₽, а расход: {amount:.2f} ₽")
        else:
            category = get_category_by_mcc(mcc_code, mcc_map)

            if category is None:
                st.warning(f"MCC код {mcc_code} не найден в базе. Пожалуйста, проверьте код.")
            elif category not in budget_categories:
                st.warning(
                    f"Категория '{category}' не найдена в бюджете. Она будет добавлена автоматически с коэффициентом 0.01.")
                budget_categories[category] = 0.01
                save_categories(budget_categories)
                new_expense = {'mcc': mcc_code, 'amount': amount, 'category': category}
                st.session_state.expense_items.append(new_expense)
                wallet_data["expense_items"] = st.session_state.expense_items
                save_wallet(wallet_data)
                st.warning(f"Категория '{category}' добавлена. Расход добавлен: {amount:.2f} ₽")
                st.rerun()
            else:
                new_expense = {'mcc': mcc_code, 'amount': amount, 'category': category}
                st.session_state.expense_items.append(new_expense)
                wallet_data["expense_items"] = st.session_state.expense_items
                save_wallet(wallet_data)
                st.warning (f"Добавлен расход: MCC {mcc_code} → {category} → {amount:.2f} ₽")
                st.rerun()

    st.divider()

    # --- Отображение текущих расходов ---
    if st.session_state.expense_items:
        st.markdown("<h2 style='text-align: center'>Текущие расходы</h2>", unsafe_allow_html=True)

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
                status = "Перерасход"
            elif spent == recommended_limit:
                status = "✓ Точно в лимит"
            else:
                status = "В пределах нормы"

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
        col1.metric("Бюджет", f"{budget:.2f} ₽")
        col2.metric("Всего потрачено", f"{total_spent:.2f} ₽", delta=f"{total_spent - budget:.2f}",
                    delta_color="inverse")
        col3.metric("Остаток", f"{remaining:.2f} ₽", delta_color="normal")

        if st.button("Очистить все расходы", use_container_width=True, type="primary"):
            st.session_state.expense_items = []
            wallet_data["expense_items"] = []
            save_wallet(wallet_data)
            st.warning("Все расходы очищены!")
            st.rerun()

        if st.button("Провести анализ", use_container_width=True, type="primary"):
            st.subheader("Анализ расходов")

            if total_spent > budget:
                st.warning("Вы превысили бюджет!")
            else:
                st.warning("Вы уложились в бюджет!")

            category_expenses = {}
            for item in st.session_state.expense_items:
                cat = item['category']
                category_expenses[cat] = category_expenses.get(cat, 0) + item['amount']

            st.subheader("Детальный анализ по категориям")

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
                        st.warning(f"Перерасход на {over:.2f} ₽")
                        if limit > 0:
                            st.warning(f"Превышение на {(spent / limit - 1) * 100:.1f}%")
                        st.warning(
                            f"Рекомендация: Постарайтесь сократить траты в категории «{category}» на {over:.2f} ₽")
                    elif spent == 0:
                        st.warning("Нет расходов в этой категории")
                        st.warning(f"У вас есть свободный лимит {limit:.2f} ₽ в категории «{category}»")
                    else:
                        remaining_limit = limit - spent
                        st.warning(f"В пределах нормы. Остаток бюджета: {remaining_limit:.2f} ₽")
                        if limit > 0:
                            st.warning(f"Использовано {percent:.1f}% от лимита")

            if total_spent > budget:
                st.subheader("Рекомендации по оптимизации")
                st.warning(
                    "Совет: Пересмотрите траты в категориях с перерасходом или перераспределите бюджет в разделе «Управление категориями».")



    else:
        st.warning("Пока нет добавленных расходов. Добавьте первый расход по MCC коду выше.")



# ================================
# СТРАНИЦА 3: УПРАВЛЕНИЕ ЦЕЛЯМИ
# ================================
# Здесь много виджетов: selectbox, expander, st.write, st.button.
# Все они отвечают только за интерфейс. Основные действия (создание,
# добавление, удаление) происходят в обработчиках кнопок.
# Вы можете переставить кнопки, изменить цвета (через CSS), добавить иконки,
# но не меняйте вызовы save_goals, load_goals и имена ключей в словаре goals.

def page_goals():
    st.markdown("<h2 style='text-align: center'>Управление целями</h2>", unsafe_allow_html=True)

    # Отображаем остаток бюджета
    display_budget_remaining()

    goals = load_goals()

    if goals:
        st.markdown("<h4 style='text-align: center'>Существующие цели</h4>", unsafe_allow_html=True)
        goal_names = list(goals.keys())
        for i, name in enumerate(goal_names, 1):
            saved = goals[name]['saved']
            target = goals[name]['target']
            percent = (saved / target * 100) if target > 0 else 0

            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i}. **{name}** — накоплено {saved:.2f} / {target:.2f} ({percent:.1f}%)")
                if saved >= target:
                    st.warning("Цель достигнута! Поздравляем!")
                else:
                    st.write(f"   Осталось: {target - saved:.2f}")
        st.divider()

    with st.expander("Создать новую цель"):
        new_name = st.text_input("Название цели")
        new_target = st.number_input("Нужная сумма", min_value=0.01, step=100.0, format="%.2f")
        if st.button("Создать цель"):
            if not new_name:
                st.warning("Название не может быть пустым.")
            elif new_target <= 0:
                st.warning("Сумма должна быть положительной.")
            elif new_name in goals:
                st.warning("Цель с таким названием уже существует.")
            else:
                goals[new_name] = {'target': new_target, 'saved': 0.0}
                save_goals(goals)
                st.warning(f"Цель '{new_name}' создана. Нужно накопить {new_target}.")
                st.rerun()

    if goals:
        with st.expander("Добавить средства к цели"):
            selected = st.selectbox("Выберите цель", list(goals.keys()))
            amount = st.number_input("Сумма для добавления", min_value=0.01, step=100.0, format="%.2f")

            # Повторно показываем остаток для удобства (можно оставить или убрать)
            remaining = get_remaining_budget()
            st.markdown(
                f"<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
                f"Остаток бюджета: {remaining:.2f} ₽"
                f"</div></div>",
                unsafe_allow_html=True
            )

            if st.button("Добавить"):
                if amount <= 0:
                    st.warning("Сумма должна быть положительной.")
                elif amount > remaining:
                    st.warning(f"Недостаточно средств! Доступно: {remaining:.2f} ₽")
                else:
                    goals[selected]['saved'] += amount
                    save_goals(goals)

                    wallet_data = load_wallet()
                    expenses = wallet_data.get("expense_items", [])
                    new_expense = {
                        'mcc': 0,
                        'amount': amount,
                        'category': 'Сбережения'
                    }
                    expenses.append(new_expense)
                    wallet_data["expense_items"] = expenses
                    save_wallet(wallet_data)

                    st.warning(f"Добавлено {amount:.2f} ₽ к цели '{selected}'")
                    st.warning("Сумма учтена как расход (сбережения)")
                    st.rerun()

    if goals:
        with st.expander("Удалить цель"):
            selected_del = st.selectbox("Выберите цель для удаления", list(goals.keys()), key="del_goal")
            if st.button("Удалить цель"):
                del goals[selected_del]
                save_goals(goals)
                st.warning(f"Цель '{selected_del}' удалена.")
                st.rerun()
    else:
        st.markdown(
            "<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1px; border-radius: 8px;'><p>Пока нет целей. Создайте первую цель.</p></div></div>",
            unsafe_allow_html=True
        )

# ================================
# СТРАНИЦА 4: УПРАВЛЕНИЕ КАТЕГОРИЯМИ
# ================================
# Здесь можно просматривать и изменять коэффициенты существующих категорий.
# Все UI-элементы – st.number_input, st.button, st.expander.
# Вы можете менять их расположение, добавлять пояснения, но не трогайте
# структуру словаря categories и вызовы save_categories / normalize_categories.

def page_categories():
    st.header("Управление категориями и коэффициентами")

    # Отображаем остаток бюджета
    display_budget_remaining()

    categories = load_categories()

    # Получаем текущий бюджет для расчета рекомендуемых сумм
    wallet_data = load_wallet()
    current_budget = wallet_data.get("budget", 0.0)

    # --- ИНИЦИАЛИЗАЦИЯ ВЕСОВ (важности) НА ОСНОВЕ КОЭФФИЦИЕНТОВ ---
    # Веса нужны для интерфейса "важность 1..10". Сумма весов не фиксирована,
    # коэффициенты вычисляются как вес категории / сумма всех весов
    if 'weights' not in st.session_state:
        # При первом заходе вычисляем веса из коэффициентов:
        # вес = коэффициент * 100 (чтобы получить целые числа для удобства)
        st.session_state.weights = {cat: coeff * 100 for cat, coeff in categories.items()}

    # Функция пересчёта коэффициентов из текущих весов и сохранения
    def recalc_and_save_from_weights():
        total_weight = sum(st.session_state.weights.values())
        if total_weight == 0:
            return None
        new_categories = {}
        for cat, w in st.session_state.weights.items():
            new_categories[cat] = w / total_weight
        save_categories(new_categories)
        return new_categories

    # Если категории изменились извне (например, после нормализации), синхронизируем веса
    if set(categories.keys()) != set(st.session_state.weights.keys()):
        # Какая-то категория добавлена/удалена извне – пересоздаём веса
        st.session_state.weights = {cat: coeff * 100 for cat, coeff in categories.items()}
    else:
        # Проверяем, не рассинхронизировались ли значения коэффициентов с весами
        total_weight = sum(st.session_state.weights.values())
        if total_weight > 0:
            for cat in categories:
                expected_coeff = st.session_state.weights[cat] / total_weight
                if abs(categories[cat] - expected_coeff) > 0.001:
                    # Если разница большая – пересчитываем веса из коэффициентов
                    st.session_state.weights = {cat: coeff * 100 for cat, coeff in categories.items()}
                    break

    st.subheader("Текущие категории")
    if categories:
        total = sum(categories.values())

        category_data = []
        for cat, coeff in sorted(categories.items()):
            # Получаем важность (вес) для отображения
            importance = st.session_state.weights.get(cat, coeff * 100)
            # Рассчитываем рекомендуемую сумму трат (лимит) для категории
            recommended_limit = current_budget * coeff

            category_data.append({
                "Категория": cat,
                "Важность (1-10)": f"{importance:.0f}",
                "Процент бюджета": f"{coeff * 100:.2f}%",
                "Рекомендуемая сумма": f"{recommended_limit:.2f} ₽"
            })

        st.dataframe(category_data, use_container_width=True)

        # Дополнительная информация о бюджете
        if current_budget > 0:
            st.info(f"**Текущий бюджет:** {current_budget:.2f} ₽ — рекомендуемые суммы пересчитаны исходя из него.")
        else:
            st.warning(
                "Бюджет не установлен. Рекомендуемые суммы появятся после установки бюджета в разделе «Распределение расходов».")

        st.info(f"**Сумма коэффициентов:** {total:.4f} (рекомендуется 1.0000)")

        if abs(total - 1.0) > 0.001:
            st.warning(f"Сумма коэффициентов не равна 1. Текущая сумма: {total:.4f}")
            if st.button("Нормализовать коэффициенты", use_container_width=True):
                normalize_categories(categories)
                # После нормализации обновляем веса
                categories = load_categories()
                st.session_state.weights = {cat: coeff * 100 for cat, coeff in categories.items()}
                st.rerun()
    else:
        st.warning("Нет категорий. Невозможно управлять.")
        return
    st.divider()

    # НОВЫЙ EXPANDER: Добавление новой категории (через важность)
    with st.expander("Добавить новую категорию"):
        st.markdown("### Создание новой категории расходов")

        new_category_name = st.text_input(
            "Название новой категории",
            placeholder="Например: Кофе, Такси, Книги...",
            key="new_category_name"
        )

        # Вместо коэффициента – выбор важности от 1 до 10
        importance = st.number_input(
            "Важность категории (приоритет)",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="1 — почти не важно (минимальная доля бюджета), 10 — максимальный приоритет (самая большая доля бюджета)",
            key="importance_add"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Создать категорию", use_container_width=True, type="primary", key="create_category_btn"):
                if not new_category_name:
                    st.error("Название категории не может быть пустым!")
                elif new_category_name in categories:
                    st.error(f"Категория '{new_category_name}' уже существует!")
                else:
                    # Добавляем новую категорию с заданной важностью
                    st.session_state.weights[new_category_name] = importance
                    # Пересчитываем коэффициенты из весов и сохраняем
                    new_categories = recalc_and_save_from_weights()
                    if new_categories:
                        # Показываем какой коэффициент получился
                        new_coeff = new_categories[new_category_name]
                        recommended = current_budget * new_coeff
                        st.success(
                            f"Категория '{new_category_name}' добавлена!\n"
                            f"Важность: {importance} → Доля бюджета: {new_coeff * 100:.1f}%\n"
                            f"→ Рекомендуемая сумма трат: {recommended:.2f} ₽"
                        )
                        st.rerun()
                    else:
                        st.error("Ошибка при пересчёте коэффициентов")

        with col2:
            # Показываем пример распределения
            if st.session_state.weights:
                total_weight = sum(st.session_state.weights.values()) + importance
                preview_coeff = importance / total_weight if total_weight > 0 else 0
                preview_limit = current_budget * preview_coeff
                st.info(f"При добавлении категории с важностью {importance}\n"
                        f"её доля бюджета составит примерно {preview_coeff * 100:.1f}%\n"
                        f"→ рекомендуемая сумма: {preview_limit:.2f} ₽")

    # Изменение важности существующей категории
    with st.expander("Изменить важность категории"):
        cat_to_edit = st.selectbox(
            "Выберите категорию",
            sorted(list(categories.keys())),
            key="edit_category_select"
        )

        # Текущая важность берётся из session_state.weights
        current_importance = st.session_state.weights.get(cat_to_edit, 5)
        current_coeff = categories[cat_to_edit]
        current_limit = current_budget * current_coeff

        st.info(
            f"Текущая важность: **{current_importance:.0f}** (доля бюджета: {current_coeff * 100:.1f}% → {current_limit:.2f} ₽)")

        new_importance = st.number_input(
            "Новая важность (1-10)",
            min_value=1,
            max_value=10,
            value=int(current_importance),
            step=1,
            key="importance_edit"
        )

        if st.button("Сохранить изменение", use_container_width=True, key="save_importance_btn"):
            if new_importance == current_importance:
                st.info("Значение не изменилось.")
            else:
                st.session_state.weights[cat_to_edit] = new_importance
                new_categories = recalc_and_save_from_weights()
                if new_categories:
                    new_coeff = new_categories[cat_to_edit]
                    new_limit = current_budget * new_coeff
                    st.success(
                        f"Важность категории '{cat_to_edit}' изменена!\n"
                        f"Было: важность {current_importance:.0f} (доля {current_coeff * 100:.1f}% → {current_limit:.2f} ₽)\n"
                        f"Стало: важность {new_importance} (доля {new_coeff * 100:.1f}% → {new_limit:.2f} ₽)"
                    )
                    st.rerun()
                else:
                    st.error("Ошибка при пересчёте коэффициентов")

    # Удаление категории
    with st.expander("Удалить категорию"):
        st.markdown("### Удаление существующей категории")
        st.warning("Внимание: удаление категории удалит все связанные с ней расходы!")

        cat_to_delete = st.selectbox(
            "Выберите категорию для удаления",
            sorted(list(categories.keys())),
            key="delete_category_select"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Удалить категорию", use_container_width=True, key="delete_category_btn"):
                if len(categories) <= 1:
                    st.error(
                        "Нельзя удалить единственную категорию! Добавьте хотя бы одну новую категорию перед удалением.")
                else:
                    deleted_name = cat_to_delete
                    # Удаляем из весов
                    del st.session_state.weights[deleted_name]
                    # Пересчитываем коэффициенты
                    new_categories = recalc_and_save_from_weights()
                    # Удаляем расходы, связанные с этой категорией
                    wallet_data = load_wallet()
                    expenses = wallet_data.get("expense_items", [])
                    original_count = len(expenses)
                    new_expenses = [exp for exp in expenses if exp.get('category') != deleted_name]
                    removed_count = original_count - len(new_expenses)
                    wallet_data["expense_items"] = new_expenses
                    save_wallet(wallet_data)

                    st.success(f"Категория '{deleted_name}' удалена!")
                    if removed_count > 0:
                        st.info(f"Также удалено {removed_count} расходов, связанных с этой категорией.")
                    st.rerun()

        with col2:
            st.info(f"Количество категорий после удаления: {len(categories) - 1}")

    # Сброс коэффициентов к равным
    with st.expander("Сбросить важность всех категорий"):
        if st.button("Сбросить важность всех категорий к значению 5", use_container_width=True,
                     key="reset_weights_btn"):
            # Устанавливаем всем категориям одинаковую важность = 5
            for cat in st.session_state.weights:
                st.session_state.weights[cat] = 5
            # Пересчитываем коэффициенты
            new_categories = recalc_and_save_from_weights()
            if new_categories:
                st.success("Важность всех категорий сброшена к 5! Все категории имеют равные доли бюджета.")
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
                    background: #FFFFE7;
                    color: #B09545;
                    border: 1px solid;
                }
            </style>
        ''',
        unsafe_allow_html=True,
    )

    #вот эту штуку можно менять ес че вспомни про размер пжпжпжпж
    # st.markdown(
    #     '''
    #         <style>
    #             /* Увеличиваем отступы вокруг всего блока */
    #             .stPills {
    #                 margin: 30px 0 40px 0;
    #             }

    #             /* Увеличиваем расстояние между кнопками */
    #             [data-testid="stPillsContainer"] {
    #                 gap: 20px !important;
    #             }
        
    #             /* Увеличиваем размер самих кнопок */
    #             button[data-testid="stBaseButton-pills"],
    #             button[data-testid="stBaseButton-pillsActive"] {
    #                 padding: 22px 38px !important;  /* больше внутренних отступов */
    #                 font-size: 28px !important;      /* крупный шрифт */
    #                 border-radius: 30px !important;  /* более круглые углы (опционально) */
    #             }
        
    #             /* Активная кнопка – можно добавить тень */
    #             button[data-testid="stBaseButton-pillsActive"] {
    #                 background: #FFFFE7 !important;
    #                 color: #B09545 !important;
    #                 order: 2px solid #B09545 !important;
    #             }
        
    #             /* Обычные кнопки – тоже увеличиваем */
    #             button[data-testid="stBaseButton-pills"] {
    #                 background: #f0f0f0 !important;
    #                 font-weight: 500 !important;
    #             }
    #         </style>
    #     ''',
    #     unsafe_allow_html=True,
    # )

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
