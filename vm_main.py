import streamlit as st
import pandas as pd
import os
import numpy as np
from sklearn.model_selection import train_test_split
from models.model_utils import train_and_save_model, load_trained_components, preprocess_data
from views.ui import (
    show_main_interface,
    show_dataset_analysis,
    show_model_metrics,
    show_error_analysis,
    show_author_search,
    show_document_checker,
    show_training_analysis
)



def predict_compliance(input_data, model, scaler, label_encoder):
    """Предсказание соответствия ГОСТ с помощью нейросети"""
    try:
        input_df = pd.DataFrame([input_data])

        if 'Шрифт' in input_df.columns:
            input_df['Шрифт'] = label_encoder.transform(input_df['Шрифт'])

        bool_cols = ['Наличие колонтитулов', 'Наличие нумерации страниц', 'Наличие титульного листа']
        for col in bool_cols:
            if col in input_df.columns:
                input_df[col] = input_df[col].astype(int)

        scaled_data = scaler.transform(input_df)
        prediction = model.predict(scaled_data)
        return prediction[0][0]
    except Exception as e:
        st.error(f"Ошибка при предсказании: {str(e)}")
        return None


def main():
    show_main_interface()

    # Загрузка датасетов
    datasets = {}
    default_df = pd.read_csv('data/default_dataset.csv')
    datasets['default'] = default_df

    uploaded_file = st.file_uploader("Загрузите свой датасет (CSV)", type=["csv"])
    if uploaded_file is not None:
        try:
            custom_df = pd.read_csv(uploaded_file)
            datasets['custom'] = custom_df
            st.success("Датасет успешно загружен!")
        except Exception as e:
            st.error(f"Ошибка загрузки файла: {str(e)}")

    dataset_choice = st.selectbox("Выберите датасет для работы",
                                  list(datasets.keys()))
    df = datasets[dataset_choice]

    # Инициализируем переменные для данных обучения
    X, y, _ = preprocess_data(df)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 2. Кнопка принудительного переобучения
    force_retrain = st.button("Переобучить модель на текущем датасете")

    history_data = None
    model_exists = os.path.exists('models/trained_model/model.h5')

    # 3. Определяем, нужно ли обучать модель
    if force_retrain or not model_exists:
        with st.spinner("Модель обучается... Это может занять некоторое время."):
            model, scaler, label_encoder, history_data, _, _ = train_and_save_model(df)
        st.success("✅ Модель обучена и сохранена!")
    else:
        # Загружаем существующую модель
        model, scaler, label_encoder, history_data = load_trained_components()
        if model is not None:
            st.success("✅ Используется сохраненная модель")
        else:
            # Если загрузка не удалась, все равно обучаем
            st.warning("⚠️ Не удалось загрузить модель. Будет выполнено переобучение...")
            with st.spinner("Модель обучается..."):
                model, scaler, label_encoder, history_data, _, _ = train_and_save_model(df)
            st.success("✅ Модель обучена и сохранена!")

    if model:
        # Метрики и графики теперь можно показывать всегда
        show_training_analysis(history_data, model, X_test, y_test, scaler)

    if 'metrics' not in st.session_state:
        X, y, _ = preprocess_data(df)
        X_scaled = scaler.transform(X)
        y_pred = (model.predict(X_scaled) > 0.5).astype(int)

        from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
        st.session_state.metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'auc': roc_auc_score(y, y_pred)
        }

    show_model_metrics(st.session_state.metrics)
    show_dataset_analysis(df)

    error_counts = []
    if 'Соответствует ГОСТ' in df.columns:
        # Получаем только документы, не соответствующие ГОСТ
        non_compliant = df[df['Соответствует ГОСТ'] == 0]
        total_non_compliant = len(non_compliant)

        if total_non_compliant > 0:
            # Считаем ошибки по каждому параметру отдельно
            error_counts = [
                ("Неправильные верхние поля", (non_compliant['Верхнее поле (см)'] != 2.0).sum()),
                ("Неправильные нижние поля", (non_compliant['Нижнее поле (см)'] != 2.0).sum()),
                ("Неправильные левые поля", (non_compliant['Левое поле (см)'] != 3.0).sum()),
                ("Неправильные правые поля", (non_compliant['Правое поле (см)'] != 1.0).sum()),
                ("Неверный шрифт", (non_compliant['Шрифт'] != 'Times New Roman').sum()),
                ("Неправильные отступы", (non_compliant['Отступ абзаца (см)'] != 1.25).sum()),
                ("Отсутствует нумерация", (non_compliant['Наличие нумерации страниц'] == 0).sum()),
                ("Ошибки в колонтитулах", (non_compliant['Наличие колонтитулов'] == 0).sum())
            ]

            # Фильтруем только те ошибки, которые встречаются
            error_counts = [err for err in error_counts if err[1] > 0]

            # Сортируем по количеству ошибок (от большего к меньшему)
            error_counts.sort(key=lambda x: x[1], reverse=True)

            # Берем топ-5 ошибок
            error_counts = error_counts[:5]

    show_error_analysis({
        'error_counts': error_counts,
        'total_docs': len(df)
    })

    show_author_search(df)
    show_document_checker()

    if 'submitted' in st.session_state and st.session_state.submitted:
        # Преобразование даты в количество дней
        try:
            date_dt = pd.to_datetime(st.session_state.date, format='%d.%m.%Y')
            days_since_2000 = (date_dt - pd.Timestamp('2000-01-01')).days
        except:
            days_since_2000 = 0

        # Создаем словарь с данными в правильном порядке
        input_data = {
            'Шрифт': st.session_state.font,
            'Размер шрифта': st.session_state.font_size,
            'Верхнее поле (см)': st.session_state.top_margin,
            'Нижнее поле (см)': st.session_state.bottom_margin,
            'Левое поле (см)': st.session_state.left_margin,
            'Правое поле (см)': st.session_state.right_margin,
            'Межстрочный интервал': st.session_state.line_spacing,
            'Отступ абзаца (см)': st.session_state.paragraph_indent,
            'Наличие колонтитулов': int(st.session_state.has_headers),
            'Наличие нумерации страниц': int(st.session_state.has_pagination),
            'Наличие титульного листа': int(st.session_state.has_title_page),
            'Верно ли оформлены заголовки': int(st.session_state.correct_headers),
            'Есть ли содержание с правильными отступами': int(st.session_state.has_contents),
            'Верно ли оформены ссылки': int(st.session_state.correct_links),
            'Верно ли оформены таблицы': int(st.session_state.correct_tables),
            'Верно ли оформены рисунки': int(st.session_state.correct_images),
            'Соответствует ли оформление списков': int(st.session_state.correct_lists),
            'Правильно ли оформлены приложения': int(st.session_state.correct_appendix),
            'Верно ли указаны реквизиты документа': int(st.session_state.correct_details),
            'Дата создания': days_since_2000
        }

        compliance_prob = predict_compliance(input_data, model, scaler, label_encoder)

        if compliance_prob is not None:
            st.subheader("🔍 Результаты проверки")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Вероятность соответствия ГОСТ", f"{compliance_prob * 100:.1f}%")

                if compliance_prob > 0.7:
                    st.success("✅ Соответствует ГОСТ")
                elif compliance_prob > 0.4:
                    st.warning("⚠️ Требуется проверка")
                else:
                    st.error("❌ Не соответствует ГОСТ")

            with col2:
                st.write("**Рекомендации:**")
                if st.session_state.font != 'Times New Roman':
                    st.write("- Используйте шрифт Times New Roman")
                if st.session_state.font_size != 14:
                    st.write(f"- Установите размер шрифта 14 (текущий: {st.session_state.font_size})")
                if st.session_state.top_margin != 2.0:
                    st.write(f"- Верхнее поле должно быть 2.0 см (текущее: {st.session_state.top_margin} см)")
                if st.session_state.bottom_margin != 2.0:
                    st.write(f"- Нижнее поле должно быть 2.0 см (текущее: {st.session_state.bottom_margin} см)")
                if st.session_state.left_margin != 3.0:
                    st.write(f"- Левое поле должно быть 3.0 см (текущее: {st.session_state.left_margin} см)")
                if st.session_state.right_margin != 1.0:
                    st.write(f"- Правое поле должно быть 1.0 см (текущее: {st.session_state.right_margin} см)")
                if st.session_state.line_spacing != 1.5:
                    st.write(f"- Межстрочный интервал должен быть 1.5 (текущий: {st.session_state.line_spacing})")
                if st.session_state.paragraph_indent != 1.25:
                    st.write(f"- Отступ абзаца должен быть 1.25 см (текущий: {st.session_state.paragraph_indent} см)")
                if not st.session_state.has_headers:
                    st.write("- Добавьте колонтитулы")
                if not st.session_state.has_pagination:
                    st.write("- Добавьте нумерацию страниц")
                if not st.session_state.has_title_page:
                    st.write("- Добавьте титульный лист")

                # Добавляем рекомендации для новых параметров
                st.write("\n**Проверьте также:**")
                st.write("- Правильность оформления заголовков")
                st.write("- Корректность оформления рисунков")
                st.write("- Правильность оформления ссылок")
                st.write("- Соответствие таблиц требованиям ГОСТ")
                st.write("- Наличие и правильность реквизитов документа")
                st.write("- Наличие содержания с правильными отступами")
                st.write("- Оформление списков по ГОСТу")
                st.write("- Правильность оформления приложений")


if __name__ == "__main__":
    main()