# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
import pandas as pd
import uuid
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

app = Flask(__name__)

# Настройки для загрузки файлов
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Ограничение размера файла 16 МБ
app.config['UPLOAD_FOLDER'] = 'static/results'  # Папка для загрузки файлов

# Создание директории для результатов, если она не существует
os.makedirs('static/results', exist_ok=True)

# Модель семантического поиска
class SemanticModel:
    def __init__(self, model_name='sberbank-ai/sbert_large_nlu_ru'):
        self.model_name = model_name
        self.model = None
        self.cache = {}

    def load(self):
        if self.model is None:
            print(f"Загрузка модели {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print("Модель успешно загружена")

    def semantic_search(self, document, query, threshhold=0.65, context_window_chars=10, context_weight_alpha=0.8):
        # Выделение кандидатов
        words_with_indices = []
        for match in re.finditer(r'\w+', document):
            words_with_indices.append({
                'text': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
        candidates = []
        for i in range(len(words_with_indices)):
            candidates.append(words_with_indices[i])
        for i in range(len(words_with_indices)-1):
            word1 = words_with_indices[i]
            word2 = words_with_indices[i+1]
            candidates.append({
                'text': f'{word1["text"]} {word2["text"]}',
                'start': word1['start'],
                'end': word2['end']
            })
        for i in range(len(words_with_indices)-2):
            word1 = words_with_indices[i]
            word2 = words_with_indices[i+1]
            word3 = words_with_indices[i+2]
            candidates.append({
                'text': f'{word1["text"]} {word2["text"]} {word3["text"]}',
                'start': word1['start'],
                'end': word3['end']
            })

        # Получение эмбеддингов
        query_embedding = self.model.encode(query)
        candidate_texts = [cand['text'] for cand in candidates]
        candidate_embeddings = self.model.encode(candidate_texts)

        # Вычисление сходства
        similarities = cosine_similarity([query_embedding], candidate_embeddings)[0]
        best_candidate_index = np.argmax(similarities)
        original_similarity = similarities[best_candidate_index]
        best_candidate = candidates[best_candidate_index]

        context_start = max(0, best_candidate['start'] - context_window_chars)
        context_end = min(len(document), best_candidate['end'] + context_window_chars)
        context_window_text = document[context_start:context_end]
        context_embedding = self.model.encode(context_window_text)
        context_similarity = cosine_similarity([query_embedding], [context_embedding])[0][0]
        context_similarity = float(context_similarity)

        final_score = context_weight_alpha * original_similarity + (1-context_weight_alpha)*context_similarity
        final_score = float(final_score)
        original_similarity = float(original_similarity)

        if final_score >= threshhold:
            position_str = f'{best_candidate["start"]} - {best_candidate["end"]}'
            probability = final_score
            return best_candidate, position_str, probability
        else:
            print(f"Макс. сходство {final_score:.4f} для '{best_candidate['text']}' не достигло порога {threshhold}")
            return None

    def predict(self, text, query="", threshold=0.65):
        # Проверка входных данных
        if not text:
            return "Текст не предоставлен"

        # Загрузка модели при необходимости
        self.load()

        # Если запрос не указан, используем первые 100 символов текста как запрос
        if not query:
            query = text[:min(100, len(text))]

        # Создание ключа кэша
        cache_key = f"{text}||{query}||{threshold}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Выполняем семантический поиск
        result = self.semantic_search(text, query, threshhold=threshold)

        # Формируем результат
        if result:
            best_candidate, position, probability = result
            result_text = f"Обработано: найдено '{best_candidate['text']}' (позиция: {position}, сходство: {probability:.4f})"
        else:
            result_text = f"Обработано: совпадений не найдено (порог: {threshold})"

        # Сохраняем в кэш
        self.cache[cache_key] = result_text

        return result_text

# Инициализация модели
model = SemanticModel()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """Обработка одиночного текста"""
    if 'input_text' not in request.form:
        return jsonify({'status': 'error', 'message': 'Текст не указан'})

    input_text = request.form.get('input_text')
    query = request.form.get('query', '')  # Получение запроса
    threshold = float(request.form.get('threshold', 0.65))  # Получение порога сходства

    try:
        # Обработка текста
        result = model.predict(input_text, query, threshold)

        return jsonify({
            'status': 'success',
            'result': result,
            'input': input_text[:100] + ('...' if len(input_text) > 100 else '')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
