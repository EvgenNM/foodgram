>>> from technol_parts_apps.models import Ingredient
>>> import csv
>>> with open('ingredients.csv', encoding='utf-8') as file:
...     rows = csv.reader(file)
...     for name, amount in rows:
...         Ingredient.objects.create(name=name, measurement_unit=amount)
...