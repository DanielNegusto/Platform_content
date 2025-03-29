# Platform_content
Проект для публикации платного контента с шаблонами bootstrap и RestAPI
# Содержание

- [Установка](#установка)
- [Использование](#использование)

# Установка

1. Клонируйте репозиторий:

```bash
   git clone https://github.com/DanielNegusto/Platform_content.git
   cd Platform_content/
```

2. Создайте и активируйте виртуальное окружение:

```bash
python -m venv myenv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```
3. Создайте .env файл по примеру .env_example
4. Установите зависимости
```bash
pip install -r req.txt
```
## Запуск сервера локально
- Выполните миграции
```bash
    python manage.py makemigrations
    python manage.py migrate
```
- Запустите сервер
```bash
    python manage.py runserver
```
## Docker-compose
для запуска контейнеров локально, запустите docker на своём пк и выполните команду
```bash
    docker-compose up --build -d
```
# Использование:
После успешного запуска сервера перейдите по адресу http://localhost:8000 если запустили локально,
либо на ip вашего сервера который указан в .env
### Шаблоны
- Главной страницы с постами
- Регистрация 
- Вход
- Профиль
и др.
### Stripe
в проекте реализована подписка на пользователей для просмотра их платного контента 
для этого нужно перейти в профиль и нажать на кнопку подписаться 
### Тестирование
для запуска тестов пропишите 
```bash
    python manage.py test
```
## Сервер сейчас работает по ip http://82.202.140.179/
можно протестировать, но ещё в разработке
## Документация API
все эндпоинты к API можно посмотреть в Swagger
http://82.202.140.179/swagger/