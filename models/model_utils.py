import os
import joblib
import pandas as pd
from tensorflow.keras.models import Sequential, load_model, save_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Tuple
import tensorflow as tf

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'trained_model')


def create_model(input_shape):
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
    """Обучает модель и сохраняет все компоненты"""
    X, y, label_encoder = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)

    model = create_model(X_train.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    model.fit(X_train, y_train,
              epochs=50,
              batch_size=32,
              validation_split=0.2,
              callbacks=[early_stopping],
              verbose=0)

    save_trained_components(model, scaler, label_encoder)
    return model, scaler, label_encoder


def save_trained_components(model, scaler, label_encoder):
    """Сохраняет все компоненты модели"""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Сохраняем модель в формате HDF5
    model.save(os.path.join(MODEL_DIR, 'model.h5'))

    # Сохраняем дополнительные компоненты
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, 'label_encoder.pkl'))


def load_trained_components():
    """Загружает сохраненные компоненты модели"""
    try:
        # Проверяем существование всех необходимых файлов
        if not all(os.path.exists(os.path.join(MODEL_DIR, f)) for f in ['model.h5', 'scaler.pkl', 'label_encoder.pkl']):
            return None, None, None

        # Загружаем модель с явным указанием custom_objects
        model = tf.keras.models.load_model(
            os.path.join(MODEL_DIR, 'model.h5'),
            custom_objects={
                'Adam': Adam,
                'binary_crossentropy': tf.keras.losses.binary_crossentropy,
            },
            compile=False
        )

        # Загружаем scaler и label_encoder
        scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
        label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))

        return model, scaler, label_encoder

    except Exception as e:
        print(f"Ошибка загрузки модели: {str(e)}")
        return None, None, None


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    """Предобработка данных для модели"""
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
        data['Дата создания'] = pd.to_datetime(data['Дата создания'], format='%d.%m.%Y')
        data['Дата создания'] = (data['Дата создания'] - pd.Timestamp('2000-01-01')).dt.days

    label_encoder = LabelEncoder()
    if 'Шрифт' in data.columns:
        data['Шрифт'] = label_encoder.fit_transform(data['Шрифт'])

    X = data.drop(['Название документа', 'Автор', 'Соответствует ГОСТ'], axis=1, errors='ignore')
    y = data['Соответствует ГОСТ']

    return X, y, label_encoder