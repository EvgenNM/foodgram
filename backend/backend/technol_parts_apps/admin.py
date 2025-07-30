from django.contrib import admin

from .models import (
    Favorite, Follow, Ingredient, Recipe,
    RecipeIngredient, Shopping, Tag, RecipeTag,
)


class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 0


class RecipeTagInline(admin.StackedInline):
    model = RecipeTag
    extra = 0

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        RecipeIngredientInline, RecipeTagInline
    )
    list_display = (
        'id',
        'name',
        'author',
        'image',
        'pub_date',
        'description',
        'cooking_time',
        'get_ingredient'
    )

    def get_ingredient(self, instance):
        return [
            one_ingredient.ingredient
            for one_ingredient in instance.recipes_ingredient.all()
        ]

    get_ingredient.short_description = 'Ингредиенты'


admin.site.register(Favorite)
admin.site.register(Follow)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeTag)
admin.site.register(Shopping)
admin.site.register(Tag)
