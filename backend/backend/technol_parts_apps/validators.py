from django.core.validators import MaxValueValidator, MinValueValidator

import technol_parts_apps.constants as const


cooking_time_validators = [
    MinValueValidator(
        const.MIN_AMOUNT_COOKING_TIME,
        message=(
            'Длительность готовки не может быть меньше '
            f'{const.MIN_AMOUNT_COOKING_TIME}'
        )
    ),
    MaxValueValidator(
        const.MAX_AMOUNT_COOKING_TIME,
        message=(
            'Длительность готовки не может быть больше '
            f'{const.MAX_AMOUNT_COOKING_TIME}'
        )
    ),
]

amount_validators = [
    MinValueValidator(
        const.MIN_AMOUNT_COOKING_TIME,
        message=(
            'Количество ингредиента не может быть меньше '
            f'{const.MIN_AMOUNT_COOKING_TIME}'
        )
    ),
    MaxValueValidator(
        const.MAX_AMOUNT_COOKING_TIME,
        message=(
            'Количество ингредиента не может быть больше '
            f'{const.MAX_AMOUNT_COOKING_TIME}'
        )
    ),
]
