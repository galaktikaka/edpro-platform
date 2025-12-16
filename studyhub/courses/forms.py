from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    """
    Кастомная форма регистрации с дополнительным полем email.
    Наследуется от встроенной UserCreationForm.
    """
    email = forms.EmailField(
        required=True,
        label='Электронная почта',
        help_text='На этот email придут уведомления'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_email(self):
        """Проверка уникальности email."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        return email

from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле аватара необязательным
        self.fields['avatar'].required = False

        from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator

class ContactForm(forms.Form):
    """
    Обычная форма для обратной связи.
    Не связана с моделью, используется для отправки сообщений.
    """
    
    # Текстовое поле с валидацией длины
    name = forms.CharField(
        label='Ваше имя',
        max_length=100,
        validators=[
            MinLengthValidator(2, 'Имя должно содержать минимум 2 символа'),
            MaxLengthValidator(100, 'Имя не должно превышать 100 символов')
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван Иванов'
        }),
        help_text='Введите ваше полное имя'
    )
    
    # Поле email с автоматической валидацией
    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        }),
        help_text='На эту почту придет ответ'
    )
    
    # Поле выбора из фиксированного списка
    CONTACT_CHOICES = [
        ('question', 'Вопрос по курсу'),
        ('technical', 'Техническая проблема'),
        ('suggestion', 'Предложение по улучшению'),
        ('other', 'Другое'),
    ]
    contact_type = forms.ChoiceField(
        label='Тип обращения',
        choices=CONTACT_CHOICES,
        initial='question',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Многострочное текстовое поле
    message = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Опишите вашу проблему или вопрос...'
        }),
        help_text='Минимум 10 символов, максимум 1000'
    )
    
    # Флажок (необязательное поле)
    newsletter = forms.BooleanField(
        label='Подписаться на рассылку о новых курсах',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Поле для ввода номера курса (необязательное)
    course_id = forms.IntegerField(
        label='Номер курса (если вопрос связан с курсом)',
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: 5'
        })
    )
    
    def clean_message(self):
        """Кастомная валидация для поля message."""
        message = self.cleaned_data['message']
        
        # Проверка минимальной длины
        if len(message.strip()) < 10:
            raise forms.ValidationError('Сообщение должно содержать не менее 10 символов')
        
        # Проверка максимальной длины
        if len(message) > 1000:
            raise forms.ValidationError('Сообщение не должно превышать 1000 символов')
        
        # Проверка на запрещенные слова
        forbidden_words = ['спам', 'реклама', 'взлом']
        for word in forbidden_words:
            if word in message.lower():
                raise forms.ValidationError(f'Сообщение содержит запрещенное слово: "{word}"')
        
        return message
    
    def clean(self):
        """Валидация, затрагивающая несколько полей."""
        cleaned_data = super().clean()
        contact_type = cleaned_data.get('contact_type')
        course_id = cleaned_data.get('course_id')
        
        # Если выбран тип "Вопрос по курсу", но не указан номер курса
        if contact_type == 'question' and not course_id:
            self.add_error('course_id', 'Для вопроса по курсу укажите номер курса')
        
        return cleaned_data

from .models import Review

class ReviewForm(forms.ModelForm):
    """
    Форма модели для добавления отзыва о курсе.
    Связана с моделью Review, позволяет оставлять оценки и комментарии.
    """
    
    class Meta:
        model = Review
        # Используем только rating и text - course и user устанавливаются автоматически
        fields = ['rating', 'text']
        
        # Кастомизация виджетов
        widgets = {
            # RadioSelect для выбора оценки
            'rating': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            # Textarea для текста отзыва
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь вашим впечатлением о курсе...'
            }),
        }
        
        # Кастомизация меток
        labels = {
            'rating': 'Ваша оценка курса',
            'text': 'Текст отзыва',
        }
        
        # Вспомогательные тексты
        help_texts = {
            'text': 'Опишите, что вам понравилось или не понравилось в курсе',
        }
    
    def clean_text(self):
        """Валидация текста отзыва."""
        text = self.cleaned_data['text']
        
        # Проверка минимальной длины
        if len(text.strip()) < 10:
            raise forms.ValidationError('Отзыв должен содержать минимум 10 символов')
        
        # Проверка максимальной длины
        if len(text) > 1000:
            raise forms.ValidationError('Отзыв не должен превышать 1000 символов')
        
        # Проверка на запрещенные слова
        forbidden_words = ['спам', 'реклама', 'купить', 'продать', 'рекламы']
        for word in forbidden_words:
            if word in text.lower():
                raise forms.ValidationError(f'Текст содержит запрещенное слово: "{word}"')
        
        return text

from django import forms
from django.core.exceptions import ValidationError
from .models import Enrollment, Course

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course']
        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-select',
                'id': 'course-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем только опубликованные курсы, на которые пользователь еще не записан
        if self.user:
            enrolled_courses = Enrollment.objects.filter(
                user=self.user
            ).values_list('course_id', flat=True)
            self.fields['course'].queryset = Course.objects.filter(
                is_published=True
            ).exclude(id__in=enrolled_courses)
    
    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        
        if self.user and course:
            # Проверка, не записан ли уже пользователь на этот курс
            if Enrollment.objects.filter(user=self.user, course=course).exists():
                raise ValidationError('Вы уже записаны на этот курс!')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance
    
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import UserProfile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'bio', 'phone', 'birth_date', 'avatar']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-select',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+79161234567'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Убираем все нецифровые символы кроме плюса в начале
            cleaned_phone = phone.strip()
            if cleaned_phone.startswith('+'):
                cleaned_phone = '+' + ''.join(filter(str.isdigit, cleaned_phone[1:]))
            else:
                cleaned_phone = ''.join(filter(str.isdigit, cleaned_phone))
            
            if len(cleaned_phone) < 10:
                raise ValidationError('Номер телефона слишком короткий')
            
            if len(cleaned_phone) > 15:
                raise ValidationError('Номер телефона слишком длинный')
            
            return cleaned_phone
        
        return phone
    
    def clean_birth_date(self):
        """Валидация даты рождения"""
        birth_date = self.cleaned_data.get('birth_date')
        
        if birth_date:
            # Проверка, что дата не в будущем
            if birth_date > date.today():
                raise ValidationError('Дата рождения не может быть в будущем!')
            
            # Проверка, что возраст не менее 16 лет
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            
            if age < 16:
                raise ValidationError('Вам должно быть не менее 16 лет!')
        
        return birth_date
    
from .models import Module, Lesson

class ModuleForm(forms.ModelForm):
    """
    Форма для создания и редактирования модулей курса.
    Автоматически устанавливает курс из URL-параметра.
    """
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'title': 'Название модуля',
            'description': 'Описание модуля',
            'order': 'Порядковый номер',
        }
        
        help_texts = {
            'order': 'Определяет последовательность модулей в курсе (0, 1, 2, ...)',
        }


class LessonForm(forms.ModelForm):
    """
    Форма для создания и редактирования уроков модуля.
    Автоматически устанавливает модуль из URL-параметра.
    """
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order', 'duration_minutes', 'is_published']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'title': 'Название урока',
            'content': 'Содержание урока',
            'order': 'Порядковый номер',
            'duration_minutes': 'Продолжительность (минут)',
        }
