# Personal_diary_service

## Описание
Проект Personal_diary_service представляет собой сервис для ведения общедоступных дневников или постов пользователя. Зарегистрированный пользователь может подписываться на других пользователей и
оставлять комментарии к постам.

## Стек
Python 3.7, 
Django 2.2.19,
Html 5,
Sqlite3,
css,
bootsrap,
Pillow 8.3.1, 
sorl-thumbnail 12.7.0,
Unittest

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Pavel-Leo/Personal_diary_service.git
```

```
cd Personal_diary_service
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv (для mac и linux)
python -m venv venv (для windows)
```

```
source venv/bin/activate (для mac и linux)
source venv/Scripts/activate (для windows)
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip (для mac и linux)
python -m pip install --upgrade pip (для windows)
```

```
перейти в дирректорию где хранится файл requirements.txt и оттуда выполнить команду:

pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate (для mac и linux)
python manage.py migrate (для windows)
```

Запустить проект:

```
перейти в дирректорию где хранится файл manage.py и оттуда выполнить команду:

python3 manage.py runserver (для mac и linux)
python manage.py runserver (для windows)
```

