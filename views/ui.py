import streamlit as st
import pandas as pd


def show_main_interface():
    st.title("📄 Система проверки документов на соответствие ГОСТ")
    st.write("""
    **Функционал системы:**
    - Проверка соответствия документов требованиям ГОСТ
    - Анализ частых ошибок оформления
    - Рекомендации по исправлению
    - Поиск документов по автору
    """)


def show_dataset_analysis(df):
    st.subheader("🔍 Анализ датасета")
    total_docs = len(df)
    compliant_docs = df['Соответствует ГОСТ'].sum()

    st.write(f"📂 Всего документов: {total_docs}")
    st.write(f"✅ Соответствует ГОСТ: {compliant_docs} ({compliant_docs / total_docs * 100:.1f}%)")
    st.write(f"❌ Не соответствует ГОСТ: {total_docs - compliant_docs} ({(1 - compliant_docs / total_docs) * 100:.1f}%)")


def show_model_metrics(metrics):
    st.subheader("📊 Метрики модели")
    cols = st.columns(4)
    cols[0].metric("Точность", f"{metrics['accuracy'] * 100:.1f}%")
    cols[1].metric("Precision", f"{metrics['precision'] * 100:.1f}%")
    cols[2].metric("Recall", f"{metrics['recall'] * 100:.1f}%")
    cols[3].metric("AUC-ROC", f"{metrics['auc']:.3f}")


def show_error_analysis(analysis):
    st.write("\n🔝 Топ-5 ошибок:")
    for error, count in analysis['error_counts'][:5]:
        st.write(f"- {error}: {count} документов ({count / analysis['total_docs'] * 100:.1f}%)")


def show_author_search(df):
    """Интерфейс поиска документов по автору"""
    st.subheader("👤 Поиск по автору")

    # Поле ввода с подсказкой
    author_name = st.text_input(
        "Введите ФИО автора:",
        key="author_search",
        help="Начните вводить фамилию и имя автора"
    )

    # Кнопка поиска (чтобы не искать при каждом изменении текста)
    if st.button("Найти") or author_name:
        if not author_name or len(author_name.strip()) < 2:
            st.warning("Введите хотя бы 2 символа для поиска")
            return

        with st.spinner("Ищем документы автора..."):
            author_analysis = analyze_author(df, author_name)

        if author_analysis:
            st.success(f"Найдено документов: {author_analysis['total_docs']}")

            # Визуализация соответствия ГОСТу
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Соответствует ГОСТ",
                          f"{author_analysis['compliant_docs']}",
                          f"{author_analysis['compliance_rate']:.1f}%")
            with col2:
                st.metric("Не соответствует",
                          f"{author_analysis['total_docs'] - author_analysis['compliant_docs']}",
                          f"{100 - author_analysis['compliance_rate']:.1f}%",
                          delta_color="off")

            # Вывод ошибок
            if author_analysis['author_errors']:
                st.subheader("Частые ошибки в документах:")
                for error, count in author_analysis['author_errors']:
                    st.write(f"▪️ {error} — {count} документ(ов)")

                # Визуализация ошибок
                errors_df = pd.DataFrame(author_analysis['author_errors'],
                                         columns=['Ошибка', 'Количество'])
                st.bar_chart(errors_df.set_index('Ошибка'))
            else:
                st.success("🎉 Все документы автора соответствуют ГОСТ!")
        else:
            st.warning("Автор не найден. Попробуйте изменить запрос.")

        # Подсказка для пользователя
        st.info("💡 Совет: для точного поиска вводите фамилию полностью")


def show_document_checker():
    st.subheader("📝 Проверка документа")
    check_option = st.radio("Способ проверки:",
                            ("Загрузить DOCX", "Ручной ввод"),
                            horizontal=True)

    if check_option == "Загрузить DOCX":
        uploaded_file = st.file_uploader("Загрузите документ DOCX", type=["docx"])
        if uploaded_file is not None:
            st.warning("Функция проверки DOCX в разработке. Пока можно использовать ручной ввод.")
    else:
        with st.form("manual_check_form"):
            st.write("**Основные параметры**")

            col1, col2 = st.columns(2)
            with col1:
                doc_name = st.text_input("Название документа", value="Отчет", key="doc_name")
                author = st.text_input("Автор", value="Иванов И.И.", key="author")
                date = st.text_input("Дата создания (ДД.ММ.ГГГГ)", value="01.01.2023", key="date",
                                     help="Введите дату создания документа в формате ДД.ММ.ГГГГ")
                font = st.selectbox("Шрифт", options=['Times New Roman', 'Arial', 'Calibri'], key="font")
                font_size = st.number_input("Размер шрифта", min_value=8, max_value=36, value=14, key="font_size")

            with col2:
                top_margin = st.number_input("Верхнее поле (см)", min_value=1.0, max_value=5.0, value=2.0,
                                             step=0.1, key="top_margin")
                bottom_margin = st.number_input("Нижнее поле (см)", min_value=1.0, max_value=5.0, value=2.0,
                                                step=0.1, key="bottom_margin")
                left_margin = st.number_input("Левое поле (см)", min_value=1.0, max_value=5.0, value=3.0,
                                              step=0.1, key="left_margin")
                right_margin = st.number_input("Правое поле (см)", min_value=1.0, max_value=5.0, value=1.0,
                                               step=0.1, key="right_margin")

            st.write("**Дополнительные параметры**")
            line_spacing = st.number_input("Межстрочный интервал", min_value=0.5, max_value=2.0, value=1.5,
                                           step=0.1, key="line_spacing")
            paragraph_indent = st.number_input("Отступ абзаца (см)", min_value=0.5, max_value=2.0, value=1.25,
                                               step=0.05, key="paragraph_indent")
            has_headers = st.checkbox("Колонтитулы", value=True, key="has_headers")
            has_pagination = st.checkbox("Нумерация страниц", value=True, key="has_pagination")
            has_title_page = st.checkbox("Титульный лист", value=True, key="has_title_page")

            st.write("**Другие параметры ГОСТ**")
            col3, col4 = st.columns(2)
            with col3:
                correct_headers = st.checkbox("Заголовки оформлены верно", value=True, key="correct_headers")
                correct_images = st.checkbox("Рисунки оформлены верно", value=True, key="correct_images")
                correct_links = st.checkbox("Ссылки оформлены верно", value=True, key="correct_links")
                correct_tables = st.checkbox("Таблицы оформлены верно", value=True, key="correct_tables")
            with col4:
                correct_details = st.checkbox("Реквизиты указаны верно", value=True, key="correct_details")
                has_contents = st.checkbox("Содержание с отступами", value=True, key="has_contents")
                correct_lists = st.checkbox("Списки оформлены верно", value=True, key="correct_lists")
                correct_appendix = st.checkbox("Приложения оформлены верно", value=True, key="correct_appendix")

            submitted = st.form_submit_button("Проверить")
            if submitted:
                st.session_state.submitted = True


def analyze_author(df, author_name):
    """Анализирует документы автора и выявляет ошибки"""
    if not author_name or len(author_name.strip()) < 2:  # Проверка на минимальную длину
        return None

    try:
        # Ищем документы автора (без учета регистра)
        author_docs = df[df['Автор'].str.strip().str.lower() == author_name.strip().lower()]

        if author_docs.empty:
            return None

        total_docs = len(author_docs)
        compliant_docs = author_docs['Соответствует ГОСТ'].sum()

        # Анализ ошибок в документах автора
        error_list = []

        # Проверяем только несоответствующие ГОСТу документы
        non_compliant = author_docs[author_docs['Соответствует ГОСТ'] == 0]

        if not non_compliant.empty:
            # Анализ частых ошибок
            errors = {
                'Неправильные поля': ((non_compliant['Верхнее поле (см)'] != 2.0) |
                                      (non_compliant['Нижнее поле (см)'] != 2.0) |
                                      (non_compliant['Левое поле (см)'] != 3.0) |
                                      (non_compliant['Правое поле (см)'] != 1.0)).sum(),
                'Неверный шрифт': (non_compliant['Шрифт'] != 'Times New Roman').sum(),
                'Неправильные отступы': (non_compliant['Отступ абзаца (см)'] != 1.25).sum(),
                'Отсутствует нумерация': (non_compliant['Наличие нумерации страниц'] == 0).sum(),
                'Ошибки в колонтитулах': (non_compliant['Наличие колонтитулов'] == 0).sum(),
                'Неправильные заголовки': (non_compliant['Верно ли оформлены заголовки'] == 0).sum(),
                'Неправильные рисунки': (non_compliant['Верно ли оформлены рисунки'] == 0).sum(),
                'Неправильные ссылки': (non_compliant['Верно ли оформлены ссылки'] == 0).sum(),
                'Неправильные таблицы': (non_compliant['Верно ли оформлены таблицы'] == 0).sum(),
                'Неправильные реквизиты': (non_compliant['Верно ли указаны реквизиты документа'] == 0).sum()
            }

            # Фильтруем только ошибки, которые встречаются
            error_list = [(error, count) for error, count in errors.items() if count > 0]

            # Сортируем по количеству ошибок (от большего к меньшему)
            error_list.sort(key=lambda x: x[1], reverse=True)

        return {
            'total_docs': total_docs,
            'compliant_docs': compliant_docs,
            'compliance_rate': compliant_docs / total_docs * 100 if total_docs > 0 else 0,
            'author_errors': error_list
        }

    except Exception as e:
        print(f"Ошибка при анализе автора: {str(e)}")
        return None
