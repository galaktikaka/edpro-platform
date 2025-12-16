from django.contrib import admin
from .models import Category, Course

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Category.
    """
    list_display = ['name', 'description']  # Поля для отображения в списке
    search_fields = ['name']  # Поля для поиска
    list_filter = []  # Пока без фильтров

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Course.
    """
    list_display = ['title', 'author', 'category', 'price', 'level', 'is_free', 'is_popular', 'is_published', 'created_at']
    list_filter = ['is_published', 'is_free', 'is_popular', 'level', 'category', 'created_at']
    search_fields = ['title', 'description', 'full_description']
    date_hierarchy = 'created_at'
    
    # Поля, отображаемые при редактировании
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'full_description', 'author', 'category')
        }),
        ('Цена и уровень', {
            'fields': ('price', 'is_free', 'level', 'duration_hours')
        }),
        ('Статус', {
            'fields': ('is_published', 'is_popular')
        }),
    )

from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'user', 'rating', 'created_at', 'get_rating_stars']
    list_filter = ['rating', 'created_at', 'course']
    search_fields = ['text', 'user__username', 'course__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_rating_stars(self, obj):
        return obj.get_rating_stars()
    get_rating_stars.short_description = 'Оценка'

from .models import Module, Lesson

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'created_at', 'lesson_count']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['course', 'order']
    
    def lesson_count(self, obj):
        return obj.lesson_count()
    lesson_count.short_description = 'Кол-во уроков'

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'order', 'duration_minutes', 'is_published', 'created_at']
    list_filter = ['module__course', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['module', 'order']

from .models import Order, OrderItem, AssistantCategory, AssistantQuestion, SupportRequest, UserProfile

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'course', 'price']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['course__title', 'order__user__username']

@admin.register(AssistantCategory)
class AssistantCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'question_count']
    search_fields = ['name']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Количество вопросов'

@admin.register(AssistantQuestion)
class AssistantQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'answer_preview']
    list_filter = ['category']
    search_fields = ['question', 'answer']
    
    def answer_preview(self, obj):
        return obj.answer[:100] + '...' if len(obj.answer) > 100 else obj.answer
    answer_preview.short_description = 'Ответ (превью)'

@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'processed', 'created_at']
    list_filter = ['processed', 'created_at']
    search_fields = ['name', 'contact', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(processed=True)
        self.message_user(request, f'{queryset.count()} обращений отмечено как обработанные')
    mark_as_processed.short_description = 'Отметить как обработанные'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'bio']
    readonly_fields = ['created_at', 'updated_at']