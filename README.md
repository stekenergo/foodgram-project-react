
![Deploy Foodgram workflow](https://github.com/stekenergo/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# Учебный проект «foodgram-project-react» :monocle_face:

**Описание**: Дипломный проект: который позволяет научиться 
работать с приложением Docker, создавать образы, контейнеры, оркестр контейнеров,
настраивать взаимосвязь между контейнерами и размещать весь проект на сервере автоматически. 
Проект Foodgram:
Можно создавать, редактировать, удалять и делиться рецептами, Можно подписываться на других
авторов рецептов, добавлять рецепты в избранное, скачивать список для покупки ингредиентов.


## Используемые технологии:

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://user-images.githubusercontent.com/25181517/117207330-263ba280-adf4-11eb-9b97-0ac5b40bc3be.png)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CI/CD](https://user-images.githubusercontent.com/25181517/183868728-b2e11072-00a5-47e2-8a4e-4ebbb2b8c554.png)
![Nginx](https://user-images.githubusercontent.com/25181517/183345125-9a7cd2e6-6ad6-436f-8490-44c903bef84c.png)
![CSS](https://img.shields.io/badge/CSS-239120?&style=for-the-badge&logo=css3&logoColor=white)
![HTML](https://img.shields.io/badge/HTML-239120?style=for-the-badge&logo=html5&logoColor=white)


## Как развернуть проект:
### Подключение проекта и установка на сервер:
**Подключитесь к удалённому серверу по SSH-ключу:
```
ssh -i путь_до_SSH_ключа/название_файла_с_SSH_ключом_без_расширения login@ip
```
**Клонируйте проект с GitHub на сервер:
```
git clone git@github.com:ваш_аккаунт/foodgram-project-react.git
```
**Создайте и активируйте виртуальное окружение:
```
source venv/bin/activate
```
**Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
**В папке с файлом manage.py выполните миграции:
```
python manage.py migrate
```
**Создайте суперпользователя:
```
python3 manage.py createsuperuser
```
**Соберите статику бэкенд-приложения:
```
python3 manage.py collectstatic
```
**Загрузите ингредиенты и теги в базу данных:
```
python manage.py db_import_data
```
```
sudo cp -r путь_к_директории_с_бэкендом/static_backend /var/www/название_проекта
```

**Создайте файл .env в той же директории, что и исполняемый файл:
```
touch .env
```
**Добавьте в файл .env переменные:
```
nano .env
```
```
SECRET_KEY = 'ВАШ_ТОКЕН'
```
```
DEBUG = 'False'
```
```
ALLOWED_HOSTS = 'IP сервера' 'ваш_домен'
```
### Настройка фронтенд-приложения:
**Находясь в директории с фронтенд-приложением, установите зависимости для него:
```
npm i
```
**Из директории с фронтенд-приложением выполните команду:
```
npm run build
```
```
sudo cp -r путь_к_директории_с_фронтенд-приложением/build/. /var/www/имя_проекта/
```
### Установка и настройка WSGI-сервера Gunicorn:
**Подключитесь к удалённому серверу, активируйте виртуальное окружение бэкенд-приложения и установите пакет gunicorn:
```
pip install gunicorn==20.1.0
```
```
gunicorn --bind 0.0.0.0:8080 foodgram_backend.wsgi
```
**Создайте файл конфигурации юнита systemd для Gunicorn в директории (скопируйте файл gunicorn_foodgram.service с папки infra) /etc/systemd/system/gunicorn_foodgram.service:
```
sudo nano /etc/systemd/system/gunicorn_foodgram.service
```
**Команда sudo systemctl с параметрами start, stop или restart запустит, остановит или перезапустит Gunicorn:
```
sudo systemctl start gunicorn_foodgram.service
```
### Установка и настройка WSGI-сервера Gunicorn:
**Установите Nginx на удалённый сервер:
```
sudo apt install nginx -y
```
```
sudo systemctl start nginx
```
**Обновите настройки Nginx в файле конфигурации веб-сервера default(скопируйте файл default с папки infra):
```
sudo nano /etc/nginx/sites-enabled/default
```
**Перезагрузите конфигурацию Nginx:
```
sudo systemctl reload nginx
```
### Настройка файрвола ufw:
**Файрвол установит правило, по которому будут закрыты все порты, кроме тех, которые вы явно укажете:
```
sudo ufw allow 'Nginx Full'
```
```
sudo ufw allow OpenSSH
```
```
sudo ufw enable
```
```
sudo ufw status
```
### Автоматизация тестирования и деплой проекта с помощью GitHub Actions:
### Файл .github/workflows/main.yml workflow будет:
**Проверять код бэкенда в репозитории на соответствие PEP8;
**Запускать тесты для фронтенда и бэкенда (тесты уже написаны);
**Собирать образы проекта и отправлять их на Docker Hub (замените username на ваш логин на Docker Hub):
```
username/foodgram_backend,
username/foodgram_frontend,
username/foodgram_gateway.
```
**Обновлять образы на сервере и перезапускать приложение при помощи Docker Compose;
**Выполнять команды для сборки статики в приложении бэкенда, переносить статику в volume; выполнять миграции;
**Извещать вас в Telegram об успешном завершении деплоя.

[Документацию проекта можно посмотреть по этой ссылке](https://foodgramassist.sytes.net/api/docs/)

[Работу проекта можно посмотреть по этой ссылке](https://foodgramassist.sytes.net)

### Автор: 
[Дмитрий](https://github.com/stekenergo)
