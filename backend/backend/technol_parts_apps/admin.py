import technol_parts_apps.models as md
from django.contrib import admin


class RecipeIngredientInline(admin.StackedInline):
    model = md.RecipeIngredient
    extra = 0


class RecipeTagInline(admin.StackedInline):
    model = md.RecipeTag
    extra = 0


@admin.register(md.Recipe)
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


admin.site.register(md.Favorite)
admin.site.register(md.Follow)
admin.site.register(md.Ingredient)
admin.site.register(md.RecipeIngredient)
admin.site.register(md.RecipeTag)
admin.site.register(md.Shopping)
admin.site.register(md.Tag)
