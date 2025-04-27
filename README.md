NeuroEmotions
==============================
Команда проекта "НейроЭмоции" (MIFIML):
------------
1. Бикбулатова Айгуль Ришатовна.
2. Борзунов Антон Андреевич.
3. Булахов Юрий Эдуардович.
4. Ворошнина Анна Олеговна.
5. Голунов Артем Сергеевич.
6. Ситёв Роман Рустамович.
7. Чунарев Дмитрий Дмитриевич.

Цель проекта
------------
Создать систему семантического текстового поиска слов (словосочетаний) в документах, учитывающую не только точное написание, но и смысловое значение. Результатом должно быть определение позиции найденного слова/словосочетания в тексте и оценка вероятности совпадения. Желательно реализовать примитивный веб-интерфейс (UI) для ручного тестирования.

Описание проекта
------------
Проект представляет собой систему семантического текстового поиска, которая позволяет находить слова и словосочетания в документах не только по точному совпадению, но и по смысловой близости.

Практическая значимость
------------
1. Для бизнеса и аналитики
    - Поиск юридических терминов в договорах с учётом синонимов.
    - Анализ отзывов (например, поиск "плохой сервис" в сочетаниях типа "меня не обслужили").

2. Для работы с документами
    - Ускорение обработки больших текстов (научные статьи, архивы).

3. Для пользователей
    - Удобный инструмент для поиска информации без точного знания формулировок.

Project Organization
------------
```
semantic_textual_similarity/
├── LICENSE     
├── README.md                  
├── Makefile                     # Makefile with commands like `make data` or `make train`                   
├── configs                      # Config files (models and training hyperparameters)
│   └── model1.yaml              
│
├── data                         
│   ├── external                 # Data from third party sources.
│   ├── interim                  # Intermediate data that has been transformed.
│   ├── processed                # The final, canonical data sets for modeling.
│   └── raw                      # The original, immutable data dump.
│
├── docs                         # Project documentation.
│
├── models                       # Trained and serialized models.
│
├── notebooks                    # Jupyter notebooks.
│
├── references                   # Data dictionaries, manuals, and all other explanatory materials.
│
├── reports                      # Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures                  # Generated graphics and figures to be used in reporting.
│
├── requirements.txt             # The requirements file for reproducing the analysis environment.
└── src                          # Source code for use in this project.
    ├── __init__.py              # Makes src a Python module.
    │
    ├── data                     # Data engineering scripts.
    │   ├── build_features.py    
    │   ├── cleaning.py          
    │   ├── ingestion.py         
    │   ├── labeling.py          
    │   ├── splitting.py         
    │   └── validation.py        
    │
    ├── models                   # ML model engineering (a folder for each model).
    │   └── model1      
    │       ├── dataloader.py    
    │       ├── hyperparameters_tuning.py 
    │       ├── model.py         
    │       ├── predict.py       
    │       ├── preprocessing.py 
    │       └── train.py         
    │
    └── visualization        # Scripts to create exploratory and results oriented visualizations.
        ├── evaluation.py        
        └── exploration.py       
```


--------
<p><small>Project based on the <a target="_blank" href="https://github.com/Chim-SO/cookiecutter-mlops/">cookiecutter MLOps project template</a>
that is originally based on <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. 
#cookiecuttermlops #cookiecutterdatascience</small></p>
