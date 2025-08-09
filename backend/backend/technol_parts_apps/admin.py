from django.contrib import admin

import technol_parts_apps.models as md


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
        'get_ingredient',
        'all_favorite'
    )
    search_fields = (
        'name',
        'author__username'
    )
    list_filter = ('tags',)

    def get_ingredient(self, instance):
        return [
            one_ingredient.ingredient
            for one_ingredient in instance.recipes_ingredient.all()
        ]

    def all_favorite(self, obj):
        return obj.recipes.count()

    get_ingredient.short_description = 'Ингредиенты'
    all_favorite.short_description = 'Избрано пользователями'


@admin.register(md.Ingredient)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(md.Favorite)
admin.site.register(md.Follow)
admin.site.register(md.RecipeIngredient)
admin.site.register(md.RecipeTag)
admin.site.register(md.Shopping)
admin.site.register(md.Tag)
