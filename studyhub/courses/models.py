from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import os
from datetime import date


class Category(models.Model):
    """
    Модель для категорий курсов.
    Каждый курс принадлежит к одной категории.
    """
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Course(models.Model):
    """
    Основная модель курса.
    Содержит информацию о курсе и ссылку на автора и категорию.
    """
    LEVEL_CHOICES = [
        ('beginner', 'Начальный уровень'),
        ('middle', 'Средний уровень'),
        ('advanced', 'Продвинутый уровень'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Краткое описание")
    full_description = models.TextField(blank=True, verbose_name="Полное описание")

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Цена (₽)"
    )
    is_free = models.BooleanField(
        default=False,
        verbose_name="Бесплатный курс",
        help_text="Если отмечено — курс отображается как бесплатный"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name="Уровень"
    )
    is_popular = models.BooleanField(
        default=False,
        verbose_name="Популярный курс",
        help_text="Отмеченные курсы будут показаны на главной странице"
    )
    
    # Связь с авторам курса
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Автор",
        related_name='courses'
    )
    
    # Связь с категорией
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Категория"
    )
    
    # Даты создания и обновления
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # Статус курса
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")
    
    # Новое поле: продолжительность курса
    duration_hours = models.PositiveIntegerField(
        default=10, 
        verbose_name="Продолжительность (часов)",
        help_text="Сколько часов в среднем занимает прохождение курса"
    )
    
    def __str__(self):
        return self.title
    
    # Метод для получения продолжительности в днях (опционально)
    def get_duration_days(self):
        """Возвращает продолжительность курса в днях (примерно)"""
        return round(self.duration_hours / 8, 1)  # Предполагаем 8 часов в день
    
    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-created_at']  # Сортировка по дате создания (новые первыми)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bio = models.TextField(blank=True, verbose_name="О себе")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    def filename(self):
        if self.avatar:
            return os.path.basename(self.avatar.name)
        return None
    
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class Review(models.Model):
    """
    Модель для хранения отзывов пользователей о курсах.
    Каждый пользователь может оставить только один отзыв на курс.
    """
    # Связь с курсом, к которому относится отзыв
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name='Курс'
    )
    
    # Связь с пользователем, оставившим отзыв
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    
    # Оценка курса от 1 до 5 звезд
    RATING_CHOICES = [
        (1, '★ - Очень плохо'),
        (2, '★★ - Плохо'),
        (3, '★★★ - Удовлетворительно'),
        (4, '★★★★ - Хорошо'),
        (5, '★★★★★ - Отлично'),
    ]
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        default=5,
        verbose_name='Оценка'
    )
    
    # Текст отзыва
    text = models.TextField(
        max_length=1000,
        verbose_name='Текст отзыва',
        help_text='Максимум 1000 символов'
    )
    
    # Даты создания и обновления
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        # Ограничение: один пользователь - один отзыв на курс
        unique_together = ['course', 'user']
        # Сортировка по дате создания (новые первыми)
        ordering = ['-created_at']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
    
    def __str__(self):
        return f'Отзыв {self.user.username} на "{self.course.title}"'
    
    def get_rating_stars(self):
        """Возвращает оценку в виде звездочек."""
        return '★' * self.rating


class Enrollment(models.Model):
    """Модель записи пользователя на курс"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    course = models.ForeignKey('Course', on_delete=models.CASCADE, verbose_name="Курс")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата записи")
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    
    class Meta:
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курсы"
        unique_together = ['user', 'course']  # Одна запись на курс
    
    def __str__(self):
        return f"{self.user.username} → {self.course.title}"
    
    @property
    def progress_percentage(self):
        """Процент выполнения курса (можно расширить)"""
        return 0  # Пока заглушка, можно добавить логику позже


class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('tutor', 'Преподаватель'),
    ]
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_profile',
        verbose_name="Пользователь"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name="Роль на платформе",
        help_text="Выберите, как вы будете использовать платформу: как студент или как преподаватель"
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name="О себе",
        help_text="Расскажите о себе, своих интересах и опыте"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Телефон",
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Введите корректный номер телефона. Формат: +79161234567"
            )
        ]
    )
    birth_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Дата рождения"
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        verbose_name="Аватар",
        help_text="Рекомендуемый размер: 200x200 пикселей"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    @property
    def age(self):
        """Возраст пользователя"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    def is_adult(self):
        """Проверка, является ли пользователь совершеннолетним"""
        return self.age is not None and self.age >= 18
    
    def clean(self):
        """Валидация данных"""
        from django.core.exceptions import ValidationError
        
        if self.birth_date:
            # Проверка, что дата рождения не в будущем
            if self.birth_date > date.today():
                raise ValidationError({'birth_date': 'Дата рождения не может быть в будущем!'})
            
            # Проверка, что пользователь старше 16 лет
            if self.age < 16:
                raise ValidationError({'birth_date': 'Вам должно быть не менее 16 лет!'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Module(models.Model):
    """
    Модель модуля курса. Каждый курс состоит из нескольких модулей.
    Модуль содержит уроки и имеет порядковый номер.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Курс'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Название модуля'
    )
    
    description = models.TextField(
        verbose_name='Описание модуля',
        help_text='Краткое описание того, что студенты изучат в этом модуле'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядковый номер',
        help_text='Определяет последовательность модулей в курсе'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'
        unique_together = ['course', 'order']  # В рамках одного курса порядок уникален
    
    def __str__(self):
        return f'{self.title} (Курс: {self.course.title})'
    
    def lesson_count(self):
        """Возвращает количество уроков в модуле."""
        return self.lessons.count()
    
    def total_duration(self):
        """Возвращает общую продолжительность всех уроков модуля."""
        return sum(lesson.duration_minutes for lesson in self.lessons.all())


class Lesson(models.Model):
    """
    Модель урока в модуле. Каждый модуль состоит из нескольких уроков.
    Урок содержит учебный материал и имеет продолжительность.
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Модуль'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Название урока'
    )
    
    content = models.TextField(
        verbose_name='Содержание урока',
        help_text='Подробный учебный материал урока'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядковый номер',
        help_text='Определяет последовательность уроков в модуле'
    )
    
    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='Продолжительность (минут)',
        help_text='Примерное время на изучение урока'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_published = models.BooleanField(
        default=True, 
        verbose_name='Опубликован',
        help_text='Если не отмечено, урок будет виден только преподавателю'
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        unique_together = ['module', 'order'] # В рамках одного модуля порядок уникален
    
    def __str__(self):
        return f'{self.title} (Модуль: {self.module.title})'
    
    def course(self):
        """Возвращает курс, к которому принадлежит урок."""
        return self.module.course

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Добавьте эту модель в существующий models.py

class Progress(models.Model):
    """Модель для отслеживания прогресса прохождения уроков"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, verbose_name='Урок')
    completed = models.BooleanField(default=False, verbose_name='Пройден')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата прохождения')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'lesson']
        verbose_name = 'Прогресс'
        verbose_name_plural = 'Прогрессы'
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['lesson', 'completed']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({'Пройден' if self.completed else 'Не пройден'})"
    
    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)
    
    @classmethod
    def get_user_progress_for_course(cls, user, course):
        """Получить прогресс пользователя по курсу"""
        return cls.objects.filter(
            user=user,
            lesson__module__course=course
        )
    
    @classmethod
    def get_user_progress_for_module(cls, user, module):
        """Получить прогресс пользователя по модулю"""
        return cls.objects.filter(
            user=user,
            lesson__module=module
        )


class Order(models.Model):
    """Заказ на покупку курсов"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('delivering', 'Доступ выдан'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус заказа'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} от {self.user.username}'

    @property
    def total_amount(self):
        """Общая сумма заказа"""
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    """Конкретный курс в составе заказа"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        verbose_name='Курс'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Цена на момент покупки'
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.course.title} ({self.price} ₽)'

    @property
    def total_price(self):
        return self.price


class AssistantCategory(models.Model):
    """Категория вопросов для онлайн‑ассистента (FAQ)"""
    name = models.CharField(max_length=100, verbose_name='Название категории')

    class Meta:
        verbose_name = 'Категория ассистента'
        verbose_name_plural = 'Категории ассистента'

    def __str__(self):
        return self.name


class AssistantQuestion(models.Model):
    """Вопрос и ответ внутри категории ассистента"""
    category = models.ForeignKey(
        AssistantCategory,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Категория'
    )
    question = models.CharField(max_length=255, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')

    class Meta:
        verbose_name = 'Вопрос ассистента'
        verbose_name_plural = 'Вопросы ассистента'

    def __str__(self):
        return self.question


class SupportRequest(models.Model):
    """Обращение пользователя в поддержку / ассистенту"""
    name = models.CharField(max_length=100, verbose_name='Имя')
    contact = models.CharField(
        max_length=150,
        verbose_name='Контакт для связи (email, Telegram и т.п.)'
    )
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    processed = models.BooleanField(default=False, verbose_name='Обработано')

    class Meta:
        verbose_name = 'Обращение в поддержку'
        verbose_name_plural = 'Обращения в поддержку'
        ordering = ['-created_at']

    def __str__(self):
        return f'Обращение от {self.name} ({self.contact})'