#!/usr/bin/env python
# cli.py
import argparse
import os
import re
import json
import logging
import datetime
import time
import numpy as np
from logging.handlers import RotatingFileHandler
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Настройка логирования в формате JSON
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }

        # Добавление дополнительных полей, если они есть
        if hasattr(record, 'data') and record.data:
            log_record.update(record.data)

        return json.dumps(log_record, ensure_ascii=False)

def setup_logging(log_file=None):
    """Настройка логирования"""
    logger = logging.getLogger('semantic_search')
    logger.setLevel(logging.DEBUG)  # Всегда используем максимальный уровень детализации

    # Очистка обработчиков, если они были определены ранее
    if logger.handlers:
        logger.handlers = []

    # Форматтер для логов в JSON
    formatter = JSONFormatter()

    # Создаем директорию для логов, если она не существует
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Создаем обработчик с ротацией файлов (100 МБ на файл)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024 * 1024,  # 100 МБ
        backupCount=10,  # Количество файлов для ротации
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Расширенная функция логирования с дополнительными данными
def log(logger, level, message, **data):
    """Логирование с дополнительными данными в JSON-формате"""
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.data = data

    for handler in logger.handlers:
        handler.emit(record)

class SemanticModel:
    def __init__(self, model_name='sberbank-ai/sbert_large_nlu_ru', logger=None):
        self.model_name = model_name
        self.model = None
        self.cache = {}
        self.logger = logger or logging.getLogger('semantic_search')

    def load(self):
        if self.model is None:
            log(self.logger, logging.INFO, "Загрузка модели", model=self.model_name)
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            duration = time.time() - start_time
            log(self.logger, logging.INFO, "Модель успешно загружена",
                model=self.model_name, duration_sec=round(duration, 2))

    def semantic_search(self, document, query, threshhold=0.65, context_window_chars=10, context_weight_alpha=0.8):
        # Проверка входных данных
        if not document or not query:
            log(self.logger, logging.WARNING, "Пустой документ или запрос",
                document=document[:30] if document else None, query=query)
            return None

        # Загрузка модели при необходимости
        self.load()

        # Выделение кандидатов
        words_with_indices = []
        for match in re.finditer(r'\w+', document):
            words_with_indices.append({
                'text': match.group(0),
                'start': match.start(),
                'end': match.end()
            })

        candidates = []
        # Одиночные слова
        for i in range(len(words_with_indices)):
            candidates.append(words_with_indices[i])

        # Двухсловные фразы
        for i in range(len(words_with_indices)-1):
            word1 = words_with_indices[i]
            word2 = words_with_indices[i+1]
            candidates.append({
                'text': f'{word1["text"]} {word2["text"]}',
                'start': word1['start'],
                'end': word2['end']
            })

        # Трехсловные фразы
        for i in range(len(words_with_indices)-2):
            word1 = words_with_indices[i]
            word2 = words_with_indices[i+1]
            word3 = words_with_indices[i+2]
            candidates.append({
                'text': f'{word1["text"]} {word2["text"]} {word3["text"]}',
                'start': word1['start'],
                'end': word3['end']
            })

        log(self.logger, logging.DEBUG, "Сформированы кандидаты",
            count=len(candidates), document_length=len(document))

        # Получение эмбеддингов
        query_embedding = self.model.encode(query)
        candidate_texts = [cand['text'] for cand in candidates]

        if not candidate_texts:  # Обработка пустого документа
            log(self.logger, logging.WARNING, "Нет кандидатов для анализа", document=document[:30])
            return None

        candidate_embeddings = self.model.encode(candidate_texts)

        # Вычисление сходства
        similarities = cosine_similarity([query_embedding], candidate_embeddings)[0]
        best_candidate_index = np.argmax(similarities)
        original_similarity = similarities[best_candidate_index]
        best_candidate = candidates[best_candidate_index]

        # Получение контекстного окна для улучшения соответствия
        context_start = max(0, best_candidate['start'] - context_window_chars)
        context_end = min(len(document), best_candidate['end'] + context_window_chars)
        context_window_text = document[context_start:context_end]
        context_embedding = self.model.encode(context_window_text)
        context_similarity = cosine_similarity([query_embedding], [context_embedding])[0][0]
        context_similarity = float(context_similarity)

        # Вычисление финального результата
        final_score = context_weight_alpha * original_similarity + (1-context_weight_alpha)*context_similarity
        final_score = float(final_score)

        log(self.logger, logging.DEBUG, "Анализ сходства",
            best_candidate=best_candidate['text'],
            original_similarity=float(original_similarity),
            context_similarity=context_similarity,
            final_score=final_score,
            threshold=threshhold)

        # Возвращаем результат, если превышен порог
        if final_score >= threshhold:
            position_str = f'{best_candidate["start"]} - {best_candidate["end"]}'
            return best_candidate, position_str, final_score
        else:
            return None

def process_document(document, query, model, threshold, line_num=None, logger=None):
    if logger:
        context = {"query": query, "document": document}
        if line_num is not None:
            context["line_num"] = line_num
        log(logger, logging.INFO, "Обработка документа", **context)

    print(f"Документ: '{document}'")
    print(f"Запрос: '{query}'")

    result = model.semantic_search(document, query, threshhold=threshold)

    if result:
        best_candidate, position_str, probability = result
        print(f"Результат: Слово - {best_candidate['text']}, Позиция: {position_str}, Вероятность: {probability:.4f}")

        if logger:
            log(logger, logging.INFO, "Результат поиска",
                found=True,
                match=best_candidate['text'],
                position=position_str,
                probability=probability,
                query=query,
                document=document,
                line_num=line_num)
    else:
        print(f"Для '{query}' совпадений в документе не найдено")

        if logger:
            log(logger, logging.INFO, "Результат поиска",
                found=False,
                query=query,
                document=document,
                line_num=line_num)

    print("-" * 50)

def get_default_log_filename():
    """Получает имя файла лога на основе существующих файлов"""
    log_dir = "semantic_search_log"

    # Создать директорию, если ее нет
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Найти максимальный номер существующего файла лога
    existing_logs = [f for f in os.listdir(log_dir) if f.startswith("search_") and f.endswith(".log")]

    if not existing_logs:
        # Если нет существующих файлов, начинаем с 1
        return os.path.join(log_dir, "search_1.log")

    # Извлечь номера и найти максимальный
    max_num = 0
    for log_file in existing_logs:
        try:
            # Извлекаем номер из имени файла
            num_str = log_file.replace("search_", "").replace(".log", "")
            num = int(num_str)
            max_num = max(max_num, num)
        except ValueError:
            continue

    # Используем следующий номер
    return os.path.join(log_dir, f"search_{max_num + 1}.log")

def main():
    # Разбор аргументов командной строки
    parser = argparse.ArgumentParser(description='Семантический поиск CLI')
    parser.add_argument('-s', '--search', required=True, help='Поисковый запрос')

    # Создание взаимоисключающей группы для способов ввода
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-t', '--text', help='Текст для поиска (в кавычках)')
    input_group.add_argument('-f', '--file', help='Файл для поиска (построчно)')

    # Добавление параметра порога с значением по умолчанию
    parser.add_argument('--threshold', type=float, default=0.6,
                        help='Порог сходства (по умолчанию: 0.6)')

    # Параметр для файла логов (опциональный)
    parser.add_argument('--log-file', help='Путь к файлу логов')

    args = parser.parse_args()

    # Определение пути к файлу логов
    log_file = args.log_file if args.log_file else get_default_log_filename()

    # Настройка логирования
    logger = setup_logging(log_file=log_file)

    # Логирование запуска программы
    log(logger, logging.INFO, "Запуск программы", params=vars(args))

    # Инициализация модели
    model = SemanticModel(logger=logger)

    # Обработка в зависимости от типа ввода
    try:
        if args.text:
            # Поиск в предоставленном тексте
            document = args.text
            query = args.search
            process_document(document, query, model, args.threshold, logger=logger)
        else:
            # Поиск в файле построчно
            log(logger, logging.INFO, "Обработка файла", filename=args.file)
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line:  # Пропуск пустых строк
                            print(f"\nСтрока {line_num}:")
                            process_document(line, args.search, model, args.threshold, line_num=line_num, logger=logger)
            except FileNotFoundError:
                error_msg = f"Файл '{args.file}' не найден"
                print(f"Ошибка: {error_msg}")
                log(logger, logging.ERROR, "Ошибка чтения файла", error=error_msg, filename=args.file)
            except Exception as e:
                error_msg = str(e)
                print(f"Ошибка чтения файла: {error_msg}")
                log(logger, logging.ERROR, "Ошибка чтения файла", error=error_msg, filename=args.file)
    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка выполнения: {error_msg}")
        log(logger, logging.ERROR, "Неожиданная ошибка", error=error_msg)

    log(logger, logging.INFO, "Завершение программы")

if __name__ == "__main__":
    main()