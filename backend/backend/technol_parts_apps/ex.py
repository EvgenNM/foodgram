class RecipeViewSet(viewsets.ModelViewSet):
    """Создание манипуляционного инструмента для рецепта"""
    http_method_names = ['post', 'get', 'patch', 'delete']
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', )

    def get_queryset(self):

        if self.request.query_params.get('tags'):
            tags_obj = Tag.objects.filter(
                slug__in=self.request.query_params.getlist('tags')
            )
            recipes_tags = Recipe.objects.filter(tag__in=tags_obj).distinct()
            return recipes_tags
        return Recipe.objects.all()


class Tag(NameFieldModelBase):
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=const.MAX_LENGTH_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name', )


class Recipe(NameFieldModelBase):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True)
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    description = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки',
        validators=[
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
    )
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient', null=True, blank=True
    )
    tags = models.ManyToManyField(
        'Tag', through='RecipeTag', null=True, blank=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'Рецепт {self.name[:const.LENGTH_TEXT]} от {self.author}'
    

class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='tag_recipes'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_tags'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        ordering = ('tag', )