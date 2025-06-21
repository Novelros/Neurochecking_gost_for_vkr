import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Tuple
import tensorflow as tf

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'trained_model')


def create_model(input_shape):
    """
    Создает и компилирует модель нейронной сети для бинарной классификации.
    Архитектура: 3 полносвязных слоя с Dropout для регуляризации.
    Возвращает скомпилированную модель Keras.
    """
    model = Sequential([
        Dense(128, activation='relu', input_shape=(input_shape,)),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001),
                  loss='binary_crossentropy',
                  metrics=['accuracy', 'Precision', 'Recall', 'AUC'])
    return model


def train_and_save_model(df):
    """
    Основной метод обучения модели. Выполняет:
    1. Предобработку данных
    2. Разделение на train/test
    3. Масштабирование признаков
    4. Обучение модели с ранней остановкой
    5. Сохранение всех компонентов
    Возвращает модель, препроцессоры и историю обучения.
    """
    X, y, label_encoder = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)  # Масштабируем только трейн

    model = create_model(X_train_scaled.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    # Сохраняем историю обучения
    history = model.fit(X_train_scaled, y_train,
                        epochs=50,
                        batch_size=32,
                        validation_split=0.2,
                        callbacks=[early_stopping],
                        verbose=0)  # verbose=0 чтобы не засорять лог Streamlit

    save_trained_components(model, scaler, label_encoder, history.history)

    # Возвращаем все, что нужно для графиков
    return model, scaler, label_encoder, history.history, X_test, y_test


def save_trained_components(model, scaler, label_encoder, history_data):
    """
    Сохраняет все компоненты модели в указанную директорию:
    - Модель Keras (.h5)
    - Объекты масштабирования и кодирования (.pkl)
    - Данные истории обучения (.pkl)
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(os.path.join(MODEL_DIR, 'model.h5'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    joblib.dump(history_data, os.path.join(MODEL_DIR, 'history.pkl'))


def load_trained_components():
    """
    Загружает ранее сохраненные компоненты модели.
    Проверяет наличие всех необходимых файлов перед загрузкой.
    Возвращает кортеж (model, scaler, label_encoder, history) или None при ошибке.
    """
    try:
        model_path = os.path.join(MODEL_DIR, 'model.h5')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
        encoder_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
        history_path = os.path.join(MODEL_DIR, 'history.pkl')

        if not all(os.path.exists(p) for p in [model_path, scaler_path, encoder_path, history_path]):
            return None, None, None, None

        model = tf.keras.models.load_model(model_path, compile=False)
        scaler = joblib.load(scaler_path)
        label_encoder = joblib.load(encoder_path)
        history_data = joblib.load(history_path)

        return model, scaler, label_encoder, history_data

    except Exception as e:
        print(f"Ошибка загрузки компонентов: {str(e)}")
        return None, None, None, None


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    """
    Подготавливает сырые данные для обучения:
    - Конвертирует булевы значения в числовые
    - Преобразует даты в числовой формат (дни с 2000-01-01)
    - Кодирует категориальные признаки (LabelEncoder)
    - Удаляет неиспользуемые колонки
    Возвращает (X, y, label_encoder).
    """
    data = df.copy()
    bool_cols = ['Наличие колонтитулов', 'Наличие нумерации страниц', 'Наличие титульного листа',
                 'Верно ли оформлены заголовки', 'Есть ли содержание с правильными отступами',
                 'Верно ли оформлены ссылки', 'Верно ли оформлены таблицы', 'Верно ли оформлены рисунки',
                 'Соответствует ли оформление списков', 'Правильно ли оформлены приложения',
                 'Верно ли указаны реквизиты документа', 'Соответствует ГОСТ']
    for col in bool_cols:
        if col in data.columns:
            data[col] = data[col].map({True: 1, False: 0, 'True': 1, 'False': 0})
    if 'Дата создания' in data.columns:
        data['Дата создания'] = pd.to_datetime(data['Дата создания'], errors='coerce', format='%d.%m.%Y')
        data['Дата создания'] = (data['Дата создания'] - pd.Timestamp('2000-01-01')).dt.days
    label_encoder = LabelEncoder()
    if 'Шрифт' in data.columns:
        data['Шрифт'] = label_encoder.fit_transform(data['Шрифт'])

    # Убедимся, что все колонки существуют перед удалением
    cols_to_drop = ['Название документа', 'Автор', 'Соответствует ГОСТ']
    X = data.drop(columns=[col for col in cols_to_drop if col in data.columns], axis=1)
    y = data['Соответствует ГОСТ']
    return X, y, label_encoder



def plot_learning_curves(history_data):
    """
    Визуализирует процесс обучения модели:
    - Строит графики accuracy/loss для train и validation
    - Позволяет анализировать сходимость и переобучение
    Возвращает объект matplotlib Figure.
    """
    # history_data - это уже и есть нужный нам словарь
    if not isinstance(history_data, dict) or not history_data:
        return None  # Защита на случай, если придут некорректные данные

    fig, ax = plt.subplots(figsize=(12, 5))
    pd.DataFrame(history_data).plot(ax=ax)
    ax.grid(True)
    ax.set_ylim(0, 1)
    ax.set_title('Кривые обучения')
    ax.set_xlabel('Эпохи')
    ax.set_ylabel('Значение метрики/потерь')
    return fig


def plot_confusion_matrix(model, X_test, y_test, scaler):
    """
    Строит матрицу ошибок для оценки качества модели:
    - Показывает распределение TP, TN, FP, FN
    - Визуализирует основные типы ошибок классификации
    Возвращает объект matplotlib Figure.
    """
    X_test_scaled = scaler.transform(X_test)
    y_pred = (model.predict(X_test_scaled) > 0.5).astype("int32")
    cm = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Не соответствует ГОСТ', 'Соответствует ГОСТ'],
                yticklabels=['Не соответствует ГОСТ', 'Соответствует ГОСТ'])
    ax.set_title('Матрица ошибок на тестовой выборке')
    ax.set_ylabel('Истинный класс')
    ax.set_xlabel('Предсказанный класс')
    return fig