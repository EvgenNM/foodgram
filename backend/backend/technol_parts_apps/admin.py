from django.contrib import admin

from .models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, Shopping, Tag
)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'image',
        'pub_date',
        'description',
        # 'ingredients',
        'cooking_time',
        'tag',
        'get_ingredient'
    )

    def get_ingredient(self, instance):
        return [
            one_ingredient.name for one_ingredient in instance.ingredient.all()
        ]


admin.site.register(Favorite)
admin.site.register(Follow)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(Shopping)
admin.site.register(Tag)
