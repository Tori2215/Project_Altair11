import streamlit as st
import json
import os
from PIL import Image
from typing import Dict, Optional
from streamlit.components.v1 import html as st_html
import plotly.express as px
import pandas as pd

# ================================
# РАБОТА С ФАЙЛАМИ (логика хранения)
# ================================
# Эти функции читают и сохраняют данные в JSON-файлы.
# Вы можете менять имена файлов, но не меняйте структуру данных,
# иначе другие функции перестанут работать.

GOALS_FILE = "goals.json"  # файл для целей
CATEGORIES_FILE = "categories.json"  # файл для категорий и их коэффициентов
WALLET_FILE = "wallet.json"  # файл для хранения бюджета и расходов
WEIGHTS_FILE = "weights.json"  # файл для хранения важности категорий (1-10)


def load_weights():
    """Загружает важность категорий из JSON-файла.
       Возвращает: { "Еда": 5, "Транспорт": 7, ... }
    """
    try:
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_weights(weights):
    """Сохраняет важность категорий в JSON-файл."""
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(weights, f, ensure_ascii=False, indent=4)


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


def load_categories():
    """Загружает категории и их коэффициенты (доли бюджета).
       Возвращает: { "Еда": 0.09, "Авто": 0.09, ... }
       Если файла нет, создаёт категории с равными коэффициентами.
    """
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Создаем стандартные категории с равными коэффициентами
        default = {"Еда": 0.25, "Транспорт": 0.25, "Досуг": 0.25, "Сбережения": 0.25}
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


def recalc_coefficients_from_weights(weights):
    """Пересчитывает коэффициенты из весов (важности) и сохраняет категории.
       weights: { "Еда": 5, "Транспорт": 7, ... }
       Возвращает новые категории
    """
    if not weights:
        return None
    total_weight = sum(weights.values())
    if total_weight == 0:
        return None

    new_categories = {}
    for cat, w in weights.items():
        new_categories[cat] = w / total_weight

    save_categories(new_categories)
    return new_categories


def sync_weights_with_categories():
    """Синхронизирует веса (важность) с категориями.
       Если появляются новые категории, добавляет их с важностью 5.
       Если категории удалены, удаляет их из весов.
       Сохраняет веса в файл.
    """
    categories = load_categories()
    weights = load_weights()

    # Получаем текущие категории
    current_categories = set(categories.keys())
    saved_weights_categories = set(weights.keys())

    # Удаляем веса для категорий, которых больше нет
    for cat in list(weights.keys()):
        if cat not in current_categories:
            del weights[cat]

    # Добавляем веса для новых категорий (по умолчанию важность 5)
    for cat in current_categories:
        if cat not in weights:
            weights[cat] = 5

    # Убеждаемся, что все веса в диапазоне 1-10
    for cat in weights:
        if weights[cat] < 1:
            weights[cat] = 1
        if weights[cat] > 10:
            weights[cat] = 10

    # Сохраняем веса
    save_weights(weights)

    # Пересчитываем коэффициенты из весов
    recalc_coefficients_from_weights(weights)

    return weights


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
# но не удаляйте вызовы функций загрузки данных.

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
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown(
        '''
            <h3 style='text-align: center'>Факт</h3>

            <table style='width: 100%; border: 2px dashed #FEE120;'>
                <td style="width: 50%">
                    <p style='text-align: center'>Попробуйте правило 50/30/20.<br> 50% дохода — на обязательные траты (еда, проезд, связь), 30% — на желания (кино, кофе, подписки), 20% — на накопления.</p>
                </td>
            </table>
        ''',
        unsafe_allow_html=True
    )
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("<img src='https://sun9-81.userapi.com/s/v1/ig2/0ANE6YikjLVBq3iKn8EtojDsLcIWMLcl_lAGPkl_OLF0-Dw5Jj2uHueb6L9QR6TvshNTzM22PdF7BcsUPBYL8lyt.jpg?quality=95&as=32x8,48x12,72x18,108x28,160x41,240x61,360x92,480x123,540x138,640x163,720x184,1080x276,1280x327,1440x368,2294x586&from=bu&u=B340kev8Er_eQ8szXbzjP7N9gP4g8pQ-PcYWdyhf8mw&cs=2294x0' style='box-shadow: 0px 2px 5px 0px rgba(0,0,0,0.5); border-radius: 30px'/>", unsafe_allow_html=True)

    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

    st.markdown(
        '''
            <div style='text-align: center; border-radius: 8px; padding: 1rem'><h4>Присоединяйтесь к комьюнити</h4></div>
            <div style='text-align: center'><p>Подписывайтесь на нас в соцсетях: узнавайте о старте наборов, вдохновляйтесь<br> историями участников и следите за анонсами мероприятий</p></div>
            <br><br>
        ''',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4=st.columns(4)
    with col1:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/128/3800/3800059.png' height='40px' width='40px' /><br>
                    <a href='https://t.me/+lOWsSXCcg0NmZGYy'>Публикуем анонсы программ<br> и мероприятий</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/512/16546/16546797.png' height='45px' width='45px' /><br>
                    <a href='https://vk.com/teducation'>Все, что есть в Телеграме, доступно<br> и в ВК</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
        with col3:
            st.markdown(
                '''
                    <div style='text-align: center '>
                        <img src='https://cdn-icons-png.flaticon.com/128/1077/1077046.png' height='45px' width='45px' /><br>
                        <a href='https://www.youtube.com/@tbank_education'>Выкладываем разборы задач<br> и записи лекций</a>
                    </div>
                ''',
                unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                '''
                    <div style='text-align: center'>
                        <img src='https://www.svgrepo.com/show/504824/rutube.svg' height='45px' width='45px' /><br>
                        <a href='https://rutube.ru/channel/45817137/'>Дублируем все, что есть на<br>Ютубе</a>
                    </div>
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

import plotly.express as px  # добавьте этот импорт в начало файла
import pandas as pd

def page_expenses():
    # CSS для кнопок в стиле второго экрана
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #FFFFE7 !important;
        border-color: #B09545 !important;
        color: #B09545 !important;
        text-align: center !important;
        justify-content: center !important;
        font-weight: 500 !important;
    }
    div.stButton > button:hover {
        background-color: #F8D980 !important;
        border-color: #F8D980 !important;
        color: white !important;
    }
    div.stButton > button:active {
        background-color: #FFFFE7 !important;
        border-color: #B09545 !important;
        color: #B09545 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.image(
        "https://imgproxy.cdn-tinkoff.ru/compressed95/aHR0cHM6Ly9jZG4udGJhbmsucnUvc3RhdGljL3BhZ2VzL2ZpbGVzLzUyNWRlYWYzLTVkMzItNDhkMS04ZjYwLTFkOWFmZThjNTBkNi5wbmc=")

    st.markdown("<h2 style='text-align:center'>Распределение расходов по категориям</h2>", unsafe_allow_html=True)

    # Синхронизируем веса с категориями
    weights = sync_weights_with_categories()
    categories = load_categories()

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
    if st.button("Сохранить изменения", use_container_width=True, type="primary"):
        wallet_data["budget"] = budget
        save_wallet(wallet_data)
        st.warning(f"Бюджет {budget:.2f} ₽ сохранен в кошелек!")
        st.rerun()

    # Используем сохраненный бюджет из файла
    budget = wallet_data.get("budget", 0.0)

    if budget == 0:
        st.warning("Введите бюджет и нажмите Сохранить бюджет, чтобы начать анализ.")
        return

    # Вычисляем остаток бюджета
    remaining = get_remaining_budget()

    # Показываем остаток бюджета вверху страницы
    st.markdown("---")
    if remaining >= 0:
        st.markdown(
            f"<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
            f"Ваш остаток бюджета: {remaining:.2f} ₽"
            f"</div></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div style='text-align: center;'><div class='stWarning' style='background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
            f"Внимание! Превышение бюджета на {abs(remaining):.2f} ₽ (бюджет: {budget:.2f} ₽"
            f"</div></div>",
            unsafe_allow_html=True
        )
    st.markdown("---")

    # Показываем информацию о распределении бюджета с важностью
    with st.expander("Информация о распределении бюджета"):
        total_categories = len(categories)
        st.warning(f"Бюджет распределяется между {total_categories} категориями на основе их важности (1-10).")

        # Показываем распределение по категориям с важностью
        category_data = []
        for cat, coeff in sorted(categories.items()):
            limit = budget * coeff
            importance = weights.get(cat, 5)
            category_data.append({
                "Категория": cat,
                "Важность (1-10)": f"{importance:.0f}",
                "Доля бюджета": f"{coeff * 100:.2f}%",
                "Лимит": f"{limit:.2f} ₽"
            })
        st.dataframe(category_data, use_container_width=True)

        total_coeff = sum(categories.values())
        if abs(total_coeff - 1.0) > 0.001:
            st.warning(f"Сумма коэффициентов: {total_coeff:.3f} (должна быть 1.000)")
            st.warning("Для нормализации коэффициентов перейдите в раздел Управление категориями.")

    # --- Добавление нового расхода ---
    st.markdown("<h2 style='text-align: center'>Добавить расход</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 2])

    with col1:
        selected_category = st.selectbox(
            "Категория расхода",
            options=list(categories.keys()),
            key="category_select"
        )

        if selected_category:
            coeff = categories[selected_category]
            importance = weights.get(selected_category, 5)
            limit = budget * coeff
            st.warning(f"Лимит категории: {limit:.2f} ₽ (важность: {importance:.0f})")

    with col2:
        amount = st.number_input("Сумма расхода (₽)", min_value=0.01, step=100.0, format="%.2f", key="amount_input")

    st.write("")
    st.write("")

    add_button = st.button("Добавить расход", use_container_width=True, type="primary")

    # Загрузка изображения чека (опционально)
    with st.expander("Или загрузите чек (в разработке)"):
        uploaded_file = st.file_uploader("Загрузите изображение чека", type=["png", "jpg", "jpeg"],
                                         key="receipt_uploader")
        if uploaded_file is not None:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="Загруженное изображение", use_container_width=True)
                st.warning("Распознавание чека находится в разработке. Пожалуйста, используйте ручной ввод категории.")
            except Exception as e:
                st.warning(f"Ошибка при загрузке изображения: {e}")

    # Обработка добавления расхода
    if add_button and amount > 0 and selected_category:
        if amount > remaining:
            st.warning(f"Недостаточно средств! Остаток бюджета: {remaining:.2f} ₽, а расход: {amount:.2f} ₽")
        else:
            category = selected_category
            coeff = categories[category]
            recommended_limit = budget * coeff

            spent_in_category = sum(
                item['amount'] for item in st.session_state.expense_items if item['category'] == category)
            new_total = spent_in_category + amount

            if new_total > recommended_limit:
                over = new_total - recommended_limit
                st.warning(
                    f"Внимание! После добавления расхода будет превышение лимита категории {category} на {over:.2f} ₽")

            new_expense = {'category': category, 'amount': amount}
            st.session_state.expense_items.append(new_expense)
            wallet_data["expense_items"] = st.session_state.expense_items
            save_wallet(wallet_data)

            importance = weights.get(category, 5)
            st.warning(f"Добавлен расход: {category} (важность: {importance:.0f}) -> {amount:.2f} ₽")
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
            coeff = categories.get(category, 0)
            recommended_limit = budget * coeff
            percent_of_limit = (spent / recommended_limit * 100) if recommended_limit > 0 else 0
            importance = weights.get(category, 5)

            if spent > recommended_limit:
                status = "Перерасход"
            elif spent == recommended_limit:
                status = "Точно в лимит"
            else:
                status = "В пределах нормы"

            expense_data.append({
                "Категория": category,
                "Важность": f"{importance:.0f}",
                "Потрачено": f"{spent:.2f} ₽",
                "Лимит": f"{recommended_limit:.2f} ₽",
                "Использовано": f"{percent_of_limit:.1f}%",
                "Статус": status
            })

        st.dataframe(expense_data, use_container_width=True, height=400)

        st.markdown("<h3 style='text-align:center'>Визуализация расходов</h3>", unsafe_allow_html=True)
        
        # Агрегируем расходы по категориям для диаграммы
        if category_total:
            df_chart = pd.DataFrame({
                'Категория': list(category_total.keys()),
                'Сумма (₽)': list(category_total.values())
            }).sort_values('Сумма (₽)', ascending=False)
            
            # Горизонтальная столбчатая диаграмма в стиле кнопок Т-Банк
            fig = px.bar(
                df_chart,
                x='Сумма (₽)',
                y='Категория',
                orientation='h',
                text='Сумма (₽)',
                title='Расходы по категориям',
                color_discrete_sequence=['#F8D980']  # цвет как при ховере на кнопках
            )
            fig.update_traces(
                texttemplate='%{text:.2f} ₽',
                textposition='outside',
                marker=dict(line=dict(color='#B09545', width=1))  # золотистая обводка
            )
            fig.update_layout(
                font=dict(size=12, color='#B09545'),
                title_font=dict(size=16, color='#FFFFE7'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Сумма (₽)',
                yaxis_title='Категория',
                margin=dict(l=0, r=0, t=40, b=0),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для построения диаграммы. Добавьте хотя бы один расход.")

        remaining = budget - total_spent
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Бюджет", f"{budget:.2f} ₽")
        with col2:
            delta_color = "inverse" if total_spent > budget else "normal"
            st.metric("Всего потрачено", f"{total_spent:.2f} ₽",
                      delta=f"{total_spent - budget:+.2f}" if budget > 0 else None,
                      delta_color=delta_color)
        with col3:
            if remaining >= 0:
                st.metric("Остаток", f"{remaining:.2f} ₽")
            else:
                st.metric("Перерасход", f"{remaining:.2f} ₽", delta="Превышение!", delta_color="inverse")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Очистить все расходы", use_container_width=True, type="primary"):
                st.session_state.expense_items = []
                wallet_data["expense_items"] = []
                save_wallet(wallet_data)
                st.warning("Все расходы очищены!")
                st.rerun()

        with col2:
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
                for category in categories.keys():
                    spent = category_expenses.get(category, 0)
                    limit = budget * categories.get(category, 0)
                    percent = (spent / limit * 100) if limit > 0 else 0
                    importance = weights.get(category, 5)
                    categories_with_stats.append((category, spent, limit, percent, importance))

                categories_with_stats.sort(key=lambda x: x[3], reverse=True)

                for category, spent, limit, percent, importance in categories_with_stats:
                    with st.expander(
                            f"{category} (важность: {importance:.0f}) - потрачено {spent:.2f} ₽ / лимит {limit:.2f} ₽ ({percent:.1f}%)"):
                        if limit > 0:
                            progress = min(spent / limit, 1.0)
                            st.progress(progress, text=f"Использовано {percent:.1f}% от лимита")

                        if spent > limit:
                            over = spent - limit
                            st.warning(f"Перерасход на {over:.2f} ₽")
                            if limit > 0:
                                st.warning(f"Превышение на {(spent / limit - 1) * 100:.1f}%")
                            st.warning(
                                f"Рекомендация: Постарайтесь сократить траты в категории {category} на {over:.2f} ₽")
                        elif spent == 0:
                            st.warning(f"Нет расходов в категории {category}")
                            st.warning(f"У вас есть свободный лимит {limit:.2f} ₽")
                        else:
                            remaining_limit = limit - spent
                            st.warning(f"В пределах нормы. Остаток лимита: {remaining_limit:.2f} ₽")
                            st.warning(f"Использовано {percent:.1f}% от лимита")

                if total_spent > budget:
                    st.subheader("Рекомендации по оптимизации")
                    st.warning(
                        "Совет: Пересмотрите траты в категориях с перерасходом или измените важность категорий в разделе Управление категориями.")

                    over_budget_cats = [(cat, spent - limit) for cat, spent, limit, _, _ in categories_with_stats if
                                        spent > limit]
                    if over_budget_cats:
                        st.warning("Категории с перерасходом:")
                        for cat, over in sorted(over_budget_cats, key=lambda x: x[1], reverse=True):
                            st.write(f"  - {cat}: перерасход {over:.2f} ₽")
    else:
        st.warning("Пока нет добавленных расходов. Добавьте первый расход выше.")
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

    st.markdown(
        '''
            <div style='text-align: center; border-radius: 8px; padding: 1rem'><h4>Присоединяйтесь к комьюнити</h4></div>
            <div style='text-align: center'><p>Подписывайтесь на нас в соцсетях: узнавайте о старте наборов, вдохновляйтесь<br> историями участников и следите за анонсами мероприятий</p></div>
            <br><br>
        ''',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4=st.columns(4)
    with col1:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/128/3800/3800059.png' height='40px' width='40px' /><br>
                    <a href='https://t.me/+lOWsSXCcg0NmZGYy'>Публикуем анонсы программ<br> и мероприятий</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/512/16546/16546797.png' height='45px' width='45px' /><br>
                    <a href='https://vk.com/teducation'>Все, что есть в Телеграме, доступно<br> и в ВК</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
        with col3:
            st.markdown(
                '''
                    <div style='text-align: center '>
                        <img src='https://cdn-icons-png.flaticon.com/128/1077/1077046.png' height='45px' width='45px' /><br>
                        <a href='https://www.youtube.com/@tbank_education'>Выкладываем разборы задач<br> и записи лекций</a>
                    </div>
                ''',
                unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                '''
                    <div style='text-align: center'>
                        <img src='https://www.svgrepo.com/show/504824/rutube.svg' height='45px' width='45px' /><br>
                        <a href='https://rutube.ru/channel/45817137/'>Дублируем все, что есть на<br>Ютубе</a>
                    </div>
                ''',
                unsafe_allow_html=True
            )

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
    display_budget_remaining()
    goals = load_goals()
    remaining_budget = get_remaining_budget()
    st.image("https://imgproxy.cdn-tinkoff.ru/compressed95/aHR0cHM6Ly9jZG4udGJhbmsucnUvc3RhdGljL3BhZ2VzL2ZpbGVzLzEyM2ExNWRlLTgxYTEtNGM4ZC1hMzYxLWYyY2RlYzVhZGIzOS5wbmc=")

    # Стиль кнопок
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #FFFFE7;
        border-color: #B09545;
        color: #B09545;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #F8D980;
        border-color: #F8D980;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

       # ---------- ОТОБРАЖЕНИЕ ЦЕЛЕЙ В РАМКЕ (через компонент HTML) ----------
    if goals:
        st.markdown("<h4 style='text-align: center'>Существующие цели</h4>", unsafe_allow_html=True)
        
        html_rows = []
        for i, (name, data) in enumerate(goals.items(), 1):
            saved = data['saved']
            target = data['target']
            percent = (saved / target * 100) if target > 0 else 0
            if saved >= target:
                status = "Цель достигнута! Поздравляем!"
            else:
                status = f"Осталось: {target - saved:.2f} ₽"
            
            html_rows.append(f"""
            <div style="margin-bottom: 12px; padding: 8px; border-bottom: 1px solid #ddd;">
                <b>{i}. {name}</b><br>
                Накоплено: {saved:.2f} / {target:.2f} ({percent:.1f}%)<br>
                <span style="color: #B09545;">{status}</span>
            </div>
            """)
        
        goals_html = f"""
        <div style="width: 100%; border: 2px dashed #FEE120; border-radius: 12px; padding: 15px; background-color: #fefef7; box-sizing: border-box; overflow-x: auto; text-align: center;">
            {''.join(html_rows)}
        </div>
        """
        # Указываем ширину 100% и убираем фиксированную высоту, чтобы не было прокрутки
        st_html(goals_html, height=len(goals) * 100 + 50, width=None)
    else:
        st_html("""
        <div style="width: 100%; border: 2px dashed #FEE120; border-radius: 12px; padding: 20px; background-color: #FFFFE7; box-sizing: border-box; text-align: center;">
            Пока нет целей. Создайте первую цель.
        </div>
        """, height=150, width=None)

    # ---------- ОСТАЛЬНЫЕ EXPANDER'Ы (без изменений, они работают) ----------
    with st.expander("Создать новую цель"):
        new_name = st.text_input("Название цели")
        new_target = st.number_input("Нужная сумма", min_value=0.01, step=100.0, format="%.2f")
        if st.button("Создать цель", use_container_width=True, type="primary"):
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
        with st.expander("Перевод между бюджетом и целью"):
            selected = st.selectbox("Выберите цель", list(goals.keys()), key="goal_transfer_select")
            direction = st.radio(
                "Направление перевода",
                ["В цель", "Из цели в бюджет"],
                horizontal=True,
                key="goal_transfer_direction"
            )
            amount = st.number_input(
                "Сумма перевода",
                min_value=0.01,
                step=100.0,
                format="%.2f",
                key="goal_transfer_amount"
            )
            saved_amount = goals[selected]['saved']
            st.markdown(
                f"<div style='text-align: center; background-color: #FFFFE7; color: #B09545; padding: 1rem; border-radius: 8px;'>"
                f"Остаток бюджета: {remaining_budget:.2f} ₽<br>"
                f"Сейчас в цели: {saved_amount:.2f} ₽"
                f"</div>",
                unsafe_allow_html=True
            )
            if st.button("Выполнить перевод", use_container_width=True, type="primary"):
                if amount <= 0:
                    st.warning("Сумма должна быть положительной.")
                elif direction == "В цель" and amount > remaining_budget:
                    st.warning(f"Недостаточно средств! Доступно: {remaining_budget:.2f} ₽")
                elif direction == "Из цели в бюджет" and amount > saved_amount:
                    st.warning(f"На цели недостаточно средств! Доступно для возврата: {saved_amount:.2f} ₽")
                else:
                    transfer_amount = amount if direction == "В цель" else -amount
                    goals[selected]['saved'] = round(goals[selected]['saved'] + transfer_amount, 2)
                    if goals[selected]['saved'] < 0:
                        goals[selected]['saved'] = 0.0
                    save_goals(goals)
                    record_goal_transfer(selected, transfer_amount)
                    if direction == "В цель":
                        st.warning(f"Переведено {amount:.2f} ₽ в цель '{selected}'")
                        st.warning("Сумма учтена как расход в категории 'Сбережения'")
                    else:
                        st.warning(f"Возвращено {amount:.2f} ₽ из цели '{selected}' в бюджет")
                        st.warning("Сумма вычтена из расходов по категории 'Сбережения'")
                    st.rerun()

        with st.expander("Удалить цель"):
            selected_del = st.selectbox("Выберите цель для удаления", list(goals.keys()), key="del_goal")
            saved_amount = goals[selected_del]['saved']
            if saved_amount > 0:
                st.info(f"При удалении цели {saved_amount:.2f} ₽ автоматически вернутся в бюджет.")
            if st.button("Удалить цель", use_container_width=True, type="primary"):
                if saved_amount > 0:
                    record_goal_transfer(selected_del, -saved_amount)
                del goals[selected_del]
                save_goals(goals)
                if saved_amount > 0:
                    st.warning(f"Цель '{selected_del}' удалена. {saved_amount:.2f} ₽ возвращено в бюджет.")
                else:
                    st.warning(f"Цель '{selected_del}' удалена.")
                st.rerun()
        st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

    st.markdown(
        '''
            <div style='text-align: center; border-radius: 8px; padding: 1rem'><h4>Присоединяйтесь к комьюнити</h4></div>
            <div style='text-align: center'><p>Подписывайтесь на нас в соцсетях: узнавайте о старте наборов, вдохновляйтесь<br> историями участников и следите за анонсами мероприятий</p></div>
            <br><br>
        ''',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4=st.columns(4)
    with col1:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/128/3800/3800059.png' height='40px' width='40px' /><br>
                    <a href='https://t.me/+lOWsSXCcg0NmZGYy'>Публикуем анонсы программ<br> и мероприятий</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '''
                <div style='text-align: center'>
                    <img src='https://cdn-icons-png.flaticon.com/512/16546/16546797.png' height='45px' width='45px' /><br>
                    <a href='https://vk.com/teducation'>Все, что есть в Телеграме, доступно<br> и в ВК</a>
                </div>
            ''',
            unsafe_allow_html=True
        )
        with col3:
            st.markdown(
                '''
                    <div style='text-align: center '>
                        <img src='https://cdn-icons-png.flaticon.com/128/1077/1077046.png' height='45px' width='45px' /><br>
                        <a href='https://www.youtube.com/@tbank_education'>Выкладываем разборы задач<br> и записи лекций</a>
                    </div>
                ''',
                unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                '''
                    <div style='text-align: center'>
                        <img src='https://www.svgrepo.com/show/504824/rutube.svg' height='45px' width='45px' /><br>
                        <a href='https://rutube.ru/channel/45817137/'>Дублируем все, что есть на<br>Ютубе</a>
                    </div>
                ''',
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

    # Синхронизируем веса с категориями (это загрузит сохранённые веса из файла)
    weights = sync_weights_with_categories()
    categories = load_categories()

    # Получаем текущий бюджет для расчета рекомендуемых сумм
    wallet_data = load_wallet()
    current_budget = wallet_data.get("budget", 0.0)

    st.subheader("Текущие категории")

    # Проверяем, есть ли категории
    if categories and len(categories) > 0:
        total = sum(categories.values())

        category_data = []
        for cat, coeff in sorted(categories.items()):
            importance = weights.get(cat, 5)
            recommended_limit = current_budget * coeff

            category_data.append({
                "Категория": cat,
                "Важность (1-10)": f"{importance:.0f}",
                "Процент бюджета": f"{coeff * 100:.2f}%",
                "Рекомендуемая сумма": f"{recommended_limit:.2f} ₽"
            })

        st.dataframe(category_data, use_container_width=True)

        if current_budget > 0:
            st.info(f"Текущий бюджет: {current_budget:.2f} ₽ - рекомендуемые суммы пересчитаны исходя из него.")
        else:
            st.warning(
                "Бюджет не установлен. Рекомендуемые суммы появятся после установки бюджета в разделе Распределение расходов.")

        if abs(total - 1.0) > 0.001:
            st.warning(f"Сумма коэффициентов не равна 1. Текущая сумма: {total:.4f}")
            if st.button("Нормализовать коэффициенты", use_container_width=True):
                recalc_coefficients_from_weights(weights)
                st.success("Коэффициенты нормализованы. Важность категорий сохранена.")
                st.rerun()
    else:
        st.warning("Нет категорий. Создайте первую категорию ниже.")
    st.divider()

    # Добавление новой категории (всегда доступно)
    with st.expander("Добавить новую категорию", expanded=(not categories or len(categories) == 0)):
        st.markdown("### Создание новой категории расходов")

        new_category_name = st.text_input(
            "Название новой категории",
            placeholder="Например: Кофе, Такси, Книги...",
            key="new_category_name"
        )

        importance = st.number_input(
            "Важность категории (приоритет)",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="1 - почти не важно (минимальная доля бюджета), 10 - максимальный приоритет (самая большая доля бюджета)",
            key="importance_add"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Создать категорию", use_container_width=True, type="primary", key="create_category_btn"):
                if not new_category_name:
                    st.error("Название категории не может быть пустым!")
                elif categories and new_category_name in categories:
                    st.error(f"Категория '{new_category_name}' уже существует!")
                else:
                    # Если нет категорий, создаём словарь весов
                    if not weights:
                        weights = {}

                    # Добавляем новую категорию в веса
                    weights[new_category_name] = importance
                    save_weights(weights)

                    # Пересчитываем коэффициенты
                    recalc_coefficients_from_weights(weights)

                    new_categories = load_categories()
                    new_coeff = new_categories.get(new_category_name, 0)
                    recommended = current_budget * new_coeff
                    st.success(
                        f"Категория '{new_category_name}' добавлена!\n"
                        f"Важность: {importance} -> Доля бюджета: {new_coeff * 100:.1f}%\n"
                        f"-> Рекомендуемая сумма трат: {recommended:.2f} ₽"
                    )
                    st.rerun()

        with col2:
            if weights:
                total_weight = sum(weights.values()) + importance
                preview_coeff = importance / total_weight if total_weight > 0 else 0
                preview_limit = current_budget * preview_coeff
                st.info(f"При добавлении категории с важностью {importance}\n"
                        f"её доля бюджета составит примерно {preview_coeff * 100:.1f}%\n"
                        f"-> рекомендуемая сумма: {preview_limit:.2f} ₽")
            else:
                st.info(f"Это будет первая категория. Её доля бюджета составит 100%.")

    # Если категории есть, показываем остальные функции управления
    if categories and len(categories) > 0:
        # Изменение важности существующей категории
        with st.expander("Изменить важность категории"):
            cat_to_edit = st.selectbox(
                "Выберите категорию",
                sorted(list(categories.keys())),
                key="edit_category_select"
            )

            current_importance = weights.get(cat_to_edit, 5)
            current_coeff = categories[cat_to_edit]
            current_limit = current_budget * current_coeff

            st.info(
                f"Текущая важность: {current_importance:.0f} (доля бюджета: {current_coeff * 100:.1f}% -> {current_limit:.2f} ₽)")

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
                    weights[cat_to_edit] = new_importance
                    save_weights(weights)

                    # Пересчитываем коэффициенты
                    recalc_coefficients_from_weights(weights)

                    categories = load_categories()
                    new_coeff = categories.get(cat_to_edit, 0)
                    new_limit = current_budget * new_coeff
                    st.success(
                        f"Важность категории '{cat_to_edit}' изменена!\n"
                        f"Было: важность {current_importance:.0f} (доля {current_coeff * 100:.1f}% -> {current_limit:.2f} ₽)\n"
                        f"Стало: важность {new_importance} (доля {new_coeff * 100:.1f}% -> {new_limit:.2f} ₽)"
                    )
                    st.rerun()

        # Удаление категории (только если больше одной категории)
        with st.expander("Удалить категорию"):
            st.markdown("### Удаление существующей категории")
            st.warning("Внимание: удаление категории удалит все связанные с ней расходы!")

            cat_to_delete = st.selectbox(
                "Выберите категорию для удаления",
                sorted(list(categories.keys())),
                key="delete_category_select"
            )

            # Показываем статистику по удаляемой категории
            wallet_data = load_wallet()
            expenses = wallet_data.get("expense_items", [])
            category_expenses = [exp for exp in expenses if exp.get('category') == cat_to_delete]
            total_category_amount = sum(exp['amount'] for exp in category_expenses)

            if total_category_amount > 0:
                st.warning(
                    f"В категории '{cat_to_delete}' есть расходы на сумму {total_category_amount:.2f} ₽. Они будут полностью удалены.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Удалить категорию", use_container_width=True, key="delete_category_btn"):
                    if len(categories) <= 1:
                        st.error(
                            "Нельзя удалить единственную категорию! Добавьте хотя бы одну новую категорию перед удалением.")
                    else:
                        deleted_name = cat_to_delete

                        # 1. Удаляем все расходы, связанные с этой категорией
                        wallet_data = load_wallet()
                        expenses = wallet_data.get("expense_items", [])
                        original_count = len(expenses)
                        new_expenses = [exp for exp in expenses if exp.get('category') != deleted_name]
                        removed_count = original_count - len(new_expenses)
                        removed_amount = sum(exp['amount'] for exp in expenses if exp.get('category') == deleted_name)

                        wallet_data["expense_items"] = new_expenses
                        save_wallet(wallet_data)

                        # 2. Обновляем session_state
                        st.session_state.expense_items = new_expenses

                        # 3. Удаляем категорию из весов
                        del weights[deleted_name]
                        save_weights(weights)

                        # 4. Пересчитываем коэффициенты для оставшихся категорий
                        recalc_coefficients_from_weights(weights)

                        st.success(f"Категория '{deleted_name}' полностью удалена!")
                        if removed_count > 0:
                            st.info(f"Удалено расходов: {removed_count} на сумму {removed_amount:.2f} ₽")
                        st.rerun()

            with col2:
                st.info(f"Количество категорий после удаления: {len(categories) - 1}")

        # Сброс важности всех категорий к 5
        with st.expander("Сбросить важность всех категорий"):
            if st.button("Сбросить важность всех категорий к значению 5", use_container_width=True,
                         key="reset_weights_btn"):
                # Устанавливаем всем категориям одинаковую важность = 5
                for cat in weights:
                    weights[cat] = 5
                save_weights(weights)

                # Пересчитываем коэффициенты
                recalc_coefficients_from_weights(weights)

                st.success("Важность всех категорий сброшена к 5! Все категории имеют равные доли бюджета.")
                st.rerun()


# ================================
# ГЛАВНОЕ МЕНЮ
# ================================
# ВОТ ЭТО ВНИЗУ ЛУЧШЕ НЕ ТРОГАТЬ

def main():
    st.set_page_config(page_title="Т-Финансы", layout="wide")

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

    menu = st.pills(
        "Навигация",
        ["Главная", "Распределение расходов", "Управление целями", "Управление категориями"],
        selection_mode="single",
        default="Главная"
    )

    if menu == "Главная":
        main_page()
    elif menu == "Распределение расходов":
        page_expenses()
    elif menu == "Управление целями":
        page_goals()
    else:
        page_categories()


if __name__ == "__main__":
    main()
