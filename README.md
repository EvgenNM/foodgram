
# описание проекта

«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


# инструкцию по запуску:
    - Перейти в дирректорию foodgram/, где расположен файл docker-compose.production.yml
    - Проверить фукционирование docker.desktop
    - ввести в терминале команду: `docker compose -f docker-compose.production.yml up -d`

    При первом запуске дополнительно:
        Находясь в указанной дирректории, из нового терминала (при работе на windows рекомендуется использовать "Windows PowerShell"), где расположен файл docker-compose.production.yml выполнить команды (без ковычек):

            - "docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic" (сбор backend-статики);

            - "docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/" (размещение собранной статики);

            - "docker compose -f docker-compose.production.yml exec backend python manage.py migrate" (выполнение миграций);

            - "docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser" (Создание администратора);

            Рекомендуемое (не обязательно):

                - подключить shell командой "docker compose -f docker-compose.production.yml exec backend python manage.py shell";

                - использую представленный ниже скрипт произвести заполнение базы данных информацией из таблицы ингредиентов:
                    """
                        >>> import csv
                        >>> from technol_parts_apps.models import Ingredient
                        >>> with open('ingredients.csv', encoding='utf-8') as file:
                        ...     rows = csv.reader(file)
                        ...     Ingredient.objects.bulk_create([Ingredient(name=name, measurement_unit=amount) for name, amount in rows])
                        ...
                    """
                - остановка shell командой "exit()"

# примеры запросов

    http://yevgeny-zolotko.zapto.org/recipes/

    ИЛИ (при запуске на локально машине)

    http://localhost:7000/api/recipes/

        - Выводят список рецептов

    http://yevgeny-zolotko.zapto.org/download_shopping_cart/

    ИЛИ

    http://localhost:7000/api/recipes/download_shopping_cart/

        - позволяют скачать список покупок

    http://yevgeny-zolotko.zapto.org/users/me/

    ИЛИ

    http://localhost:7000/api/users/me/

        - Вход в профиль пользователя (при условии предварительной аутентификации)


# использованные технологии
    Проект выполнен на басе уже сформированной fronted-составляющей.
    При формировании backend-составляющей использованы:
        Django
        djangorestframework
        djoser
        Pillow
        django-filter
        gunicorn
        psycopg2-binary
        flake8

# информация об авторе
 - Студент 105 кагорты курса Python-разработчик образовательной платформы Яндекс-практикум
 - Евгений Новик (Имя, Фамилия)
 - github.com/EvgenNM (Профиль на github)