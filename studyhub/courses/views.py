from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django import forms
from .models import (
    Course,
    Category,
    Review,
    Enrollment,
    UserProfile,
    Module,
    Lesson,
    Progress,
    Order,
    OrderItem,
    AssistantCategory,
    AssistantQuestion,
    SupportRequest,
)
from .forms import (
    UserRegisterForm,
    ContactForm,
    ReviewForm,
    EnrollmentForm,
    ProfileForm,
    ModuleForm,
    LessonForm,
)

class HomePageView(TemplateView):
    template_name = 'courses/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_published = Course.objects.filter(is_published=True)
        featured = all_published.filter(is_popular=True)[:3]
        if not featured:
            featured = all_published[:3]
        context['featured_courses'] = featured
        context['free_courses'] = all_published.filter(is_free=True)[:3]
        context['total_courses'] = all_published.count()
        return context

class AboutPageView(TemplateView):
    template_name = 'courses/about.html'

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_published=True)
        
        category_id = self.request.GET.get('category')
        if category_id and category_id != 'all':
            queryset = queryset.filter(category_id=category_id)

        level = self.request.GET.get('level')
        if level and level != 'all':
            queryset = queryset.filter(level=level)

        show_free_only = self.request.GET.get('free') == 'on'
        if show_free_only:
            queryset = queryset.filter(is_free=True)

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(author__username__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['current_level'] = self.request.GET.get('level', 'all')
        context['free_only'] = self.request.GET.get('free') == 'on'
        context['levels'] = Course.LEVEL_CHOICES
        
        categories_with_counts = []
        for category in context['categories']:
            count = Course.objects.filter(
                category=category,
                is_published=True
            ).count()
            categories_with_counts.append({
                'category': category,
                'count': count
            })
        context['categories_with_counts'] = categories_with_counts
        
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Получаем все отзывы для курса
        reviews = Review.objects.filter(course=course).select_related('user').order_by('-created_at')
        context['reviews'] = reviews
        
        # Статистика отзывов
        review_count = reviews.count()
        context['review_count'] = review_count
        
        if review_count > 0:
            avg_rating = sum(review.rating for review in reviews) / review_count
            context['average_rating'] = round(avg_rating, 1)
        else:
            context['average_rating'] = None
        
        # Проверяем, оставлял ли текущий пользователь отзыв
        if self.request.user.is_authenticated:
            context['has_reviewed'] = Review.objects.filter(
                course=course,
                user=self.request.user
            ).exists()
        else:
            context['has_reviewed'] = False
        
        # Проверяем, записан ли пользователь на курс
        if self.request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    user=self.request.user,
                    course=course
                )
                context['user_enrolled'] = True
                context['enrollment_date'] = enrollment.enrolled_at
                context['enrollment_completed'] = enrollment.completed
            except Enrollment.DoesNotExist:
                context['user_enrolled'] = False
        else:
            context['user_enrolled'] = False
        
        # Похожие курсы
        similar_courses = Course.objects.filter(
            category=course.category,
            is_published=True
        ).exclude(pk=course.pk)[:3]
        context['similar_courses'] = similar_courses
        
        # Добавляем данные о прогрессе (ОБНОВЛЕННЫЙ КОД)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'enrollment_set'):
            if self.request.user.enrollment_set.filter(course=course).exists():
                # Прогресс курса
                completed_lessons = Progress.objects.filter(
                    user=self.request.user,
                    lesson__module__course=course,
                    completed=True
                ).count()
                total_lessons = Lesson.objects.filter(module__course=course).count()
                progress_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
                
                context['user_progress'] = {
                    'completed_lessons': completed_lessons,
                    'total_lessons': total_lessons,
                    'percentage': progress_percentage,
                    'has_progress': completed_lessons > 0
                }
        
        return context

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'description', 'category', 'duration_hours', 'is_published']
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Курс успешно создан!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.pk})

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'description', 'category', 'duration_hours', 'is_published']
    
    def test_func(self):
        course = self.get_object()
        return self.request.user == course.author
    
    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        if self.request.user.is_authenticated:
            return HttpResponseForbidden("Вы не являетесь автором этого курса")
        else:
            return redirect('login')
    
    def form_valid(self, form):
        messages.success(self.request, 'Курс успешно обновлен!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.pk})

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    
    def test_func(self):
        course = self.get_object()
        return self.request.user == course.author
    
    def get_success_url(self):
        messages.success(self.request, 'Курс успешно удален!')
        return reverse_lazy('course_list')

class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = '/'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request, 
            f'Добро пожаловать, {user.username}! Регистрация прошла успешно.'
        )
        return response

class MyCoursesView(LoginRequiredMixin, ListView):
    template_name = 'courses/my_courses.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(author=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_queryset()
        
        from django.db.models import Sum
        context['total_count'] = courses.count()
        context['published_count'] = courses.filter(is_published=True).count()
        context['draft_count'] = courses.filter(is_published=False).count()
        
        total_hours = courses.aggregate(total=Sum('duration_hours'))['total'] or 0
        context['total_hours'] = total_hours
        
        if context['total_count'] > 0:
            context['avg_hours'] = total_hours / context['total_count']
            context['published_percent'] = int(
                (context['published_count'] / context['total_count']) * 100
            )
        else:
            context['avg_hours'] = 0
            context['published_percent'] = 0
        
        context['latest_course'] = courses.order_by('-created_at').first()
        
        return context

class ContactFormView(FormView):
    template_name = 'courses/contact_form.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact_form')
    
    def form_valid(self, form):
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']
        contact_type = form.cleaned_data['contact_type']
        
        print(f"Новое обращение: {contact_type}")
        print(f"От: {name} ({email})")
        print(f"Сообщение: {message[:50]}...")
        
        messages.success(
            self.request, 
            f'Спасибо за ваше обращение, {name}! Мы ответим вам в течение 24 часов.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Пожалуйста, исправьте ошибки в форме.'
        )
        return super().form_invalid(form)

class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'courses/add_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs['pk']
        context['course'] = get_object_or_404(Course, pk=course_id)
        return context
    
    def form_valid(self, form):
        course_id = self.kwargs['pk']
        course = get_object_or_404(Course, pk=course_id)
        
        if Review.objects.filter(course=course, user=self.request.user).exists():
            messages.error(
                self.request,
                'Вы уже оставляли отзыв на этот курс.'
            )
            return redirect('course_detail', pk=course_id)
        
        form.instance.course = course
        form.instance.user = self.request.user
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            'Спасибо за ваш отзыв! Он поможет другим студентам.'
        )
        
        return response
    
    def get_success_url(self):
        course_id = self.kwargs['pk']
        return reverse_lazy('course_detail', kwargs={'pk': course_id})

class EnrollView(LoginRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'courses/enroll_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        course = form.instance.course
        messages.success(
            self.request,
            f'Вы успешно записались на курс "{course.title}"!'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.course.pk})

@login_required
def quick_enroll(request, pk):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=pk)
        
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            messages.warning(request, 'Вы уже записаны на этот курс!')
        else:
            Enrollment.objects.create(user=request.user, course=course)
            messages.success(request, f'Вы успешно записались на курс "{course.title}"!')
    
    return redirect('course_detail', pk=pk)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileForm
    template_name = 'courses/profile_update.html'
    success_url = reverse_lazy('my_courses')
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'bio': '',
                'phone': '',
                'birth_date': None,
                'avatar': None
            }
        )
        if created:
            messages.info(self.request, 'Создан новый профиль для вас!')
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['age'] = self.object.age
        context['is_adult'] = self.object.is_adult()
        context['role'] = self.object.role
        return context

class CourseSearchView(ListView):
    model = Course
    template_name = 'courses/course_search.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_published=True)
        
        query = self.request.GET.get('q', '').strip()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(author__username__icontains=query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['search_query'] = query
        context['search_count'] = self.get_queryset().count()
        return context

class ModuleListView(ListView):
    template_name = 'courses/module_list.html'
    context_object_name = 'modules'
    
    def get_queryset(self):
        course_pk = self.kwargs['course_pk']
        return Module.objects.filter(course_id=course_pk).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_pk = self.kwargs['course_pk']
        course = get_object_or_404(Course, pk=course_pk)
        context['course'] = course
        
        # Рассчитываем общую статистику
        modules = self.get_queryset()
        total_lessons = sum(module.lessons.count() for module in modules)
        total_duration = sum(module.total_duration() for module in modules)
        
        context['total_lessons'] = total_lessons
        context['total_duration'] = total_duration
        
        return context

class ModuleDetailView(DetailView):
    model = Module
    template_name = 'courses/module_detail.html'
    context_object_name = 'module'
    
    def get_object(self, queryset=None):
        course_pk = self.kwargs['course_pk']
        module_pk = self.kwargs['module_pk']
        
        return get_object_or_404(
            Module, 
            pk=module_pk, 
            course_id=course_pk
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.object
        
        # Получаем уроки модуля
        lessons = module.lessons.all().order_by('order')
        context['lessons'] = lessons
        
        # Рассчитываем общую продолжительность
        total_duration = sum(lesson.duration_minutes for lesson in lessons)
        context['total_duration'] = total_duration
        
        # Добавляем информацию о прогрессе
        if self.request.user.is_authenticated:
            # Проверяем, записан ли пользователь на курс
            is_enrolled = hasattr(self.request.user, 'enrollment_set') and \
                         self.request.user.enrollment_set.filter(course=module.course).exists()
            
            if is_enrolled:
                # Прогресс модуля
                completed_lessons = Progress.objects.filter(
                    user=self.request.user,
                    lesson__module=module,
                    completed=True
                ).count()
                total_lessons = lessons.count()
                progress_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
                
                context['user_progress'] = {
                    'completed_lessons': completed_lessons,
                    'total_lessons': total_lessons,
                    'percentage': progress_percentage
                }
                
                # Информация о прогрессе для каждого урока
                lessons_with_progress = []
                for lesson in lessons:
                    progress = Progress.objects.filter(
                        user=self.request.user,
                        lesson=lesson
                    ).first()
                    lessons_with_progress.append({
                        'lesson': lesson,
                        'completed': progress.completed if progress else False,
                        'completed_at': progress.completed_at if progress else None
                    })
                context['lessons_with_progress'] = lessons_with_progress
        
        return context

class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'
    
    def get_object(self, queryset=None):
        course_pk = self.kwargs['course_pk']
        module_pk = self.kwargs['module_pk']
        lesson_pk = self.kwargs['lesson_pk']
        
        return get_object_or_404(
            Lesson.objects.select_related('module__course'),
            pk=lesson_pk,
            module_id=module_pk,
            module__course_id=course_pk
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        
        # Информация для навигации
        context['course'] = lesson.module.course
        context['module'] = lesson.module
        
        # Находим предыдущий и следующий уроки
        lessons = list(lesson.module.lessons.all().order_by('order'))
        current_index = lessons.index(lesson)
        
        if current_index > 0:
            context['previous_lesson'] = lessons[current_index - 1]
        
        if current_index < len(lessons) - 1:
            context['next_lesson'] = lessons[current_index + 1]
        
        # Добавляем информацию о прогрессе
        if self.request.user.is_authenticated:
            # Проверяем, записан ли пользователь на курс
            is_enrolled = hasattr(self.request.user, 'enrollment_set') and \
                         self.request.user.enrollment_set.filter(course=lesson.module.course).exists()
            
            if is_enrolled:
                # Прогресс текущего урока
                progress = Progress.objects.filter(
                    user=self.request.user,
                    lesson=lesson
                ).first()
                
                context['user_progress'] = {
                    'completed': progress.completed if progress else False,
                    'completed_at': progress.completed_at if progress else None
                }
                
                # Прогресс модуля
                module = lesson.module
                module_completed = Progress.objects.filter(
                    user=self.request.user,
                    lesson__module=module,
                    completed=True
                ).count()
                module_total = module.lessons.count()
                module_progress = int((module_completed / module_total) * 100) if module_total > 0 else 0
                
                context['module_progress'] = {
                    'completed': module_completed,
                    'total': module_total,
                    'percentage': module_progress
                }
                
                # Прогресс курса
                course = lesson.module.course
                course_completed = Progress.objects.filter(
                    user=self.request.user,
                    lesson__module__course=course,
                    completed=True
                ).count()
                course_total = Lesson.objects.filter(module__course=course).count()
                course_progress = int((course_completed / course_total) * 100) if course_total > 0 else 0
                
                context['course_progress'] = {
                    'completed': course_completed,
                    'total': course_total,
                    'percentage': course_progress
                }
        
        return context

class ModuleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    
    def test_func(self):
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        return self.request.user == course.author
    
    def form_valid(self, form):
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        form.instance.course = course
        messages.success(self.request, 'Модуль успешно создан!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('module_list', kwargs={'course_pk': self.kwargs['course_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        context['course'] = course  # <-- ВАЖНО: добавляем курс в контекст
        return context

class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
    
    def test_func(self):
        module = get_object_or_404(Module, pk=self.kwargs['module_pk'])
        return self.request.user == module.course.author
    
    def form_valid(self, form):
        module = get_object_or_404(Module, pk=self.kwargs['module_pk'])
        form.instance.module = module
        messages.success(self.request, 'Урок успешно создан!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy(
            'module_detail',
            kwargs={
                'course_pk': self.kwargs['course_pk'],
                'module_pk': self.kwargs['module_pk']
            }
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = get_object_or_404(Module, pk=self.kwargs['module_pk'])
        context['module'] = module  # <-- ВАЖНО
        context['course'] = module.course  # <-- ВАЖНО
        return context

class ModuleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    
    def get_object(self, queryset=None):
        module_pk = self.kwargs['module_pk']
        course_pk = self.kwargs['course_pk']
        return get_object_or_404(Module, pk=module_pk, course_id=course_pk)
    
    def test_func(self):
        module = self.get_object()
        return self.request.user == module.course.author
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.object
        context['course'] = module.course  # <-- ВАЖНО: добавляем курс в контекст
        return context
    
    def get_success_url(self):
        return reverse_lazy('module_detail', kwargs={
            'course_pk': self.object.course.pk,
            'module_pk': self.object.pk
        })

class ModuleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Module
    template_name = 'courses/module_confirm_delete.html'
    
    def get_object(self, queryset=None):
        module_pk = self.kwargs['module_pk']
        course_pk = self.kwargs['course_pk']
        return get_object_or_404(Module, pk=module_pk, course_id=course_pk)
    
    def test_func(self):
        module = self.get_object()
        return self.request.user == module.course.author
    
    def get_success_url(self):
        messages.success(self.request, 'Модуль успешно удален!')
        return reverse_lazy('module_list', kwargs={'course_pk': self.object.course.pk})

class LessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
    
    def get_object(self, queryset=None):
        lesson_pk = self.kwargs['pk']
        module_pk = self.kwargs['module_pk']
        course_pk = self.kwargs['course_pk']
        
        return get_object_or_404(
            Lesson,
            pk=lesson_pk,
            module_id=module_pk,
            module__course_id=course_pk
        )
    
    def test_func(self):
        lesson = self.get_object()
        return self.request.user == lesson.module.course.author
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        context['course'] = lesson.module.course  # <-- ВАЖНО
        context['module'] = lesson.module  # <-- ВАЖНО
        return context
    
    def get_success_url(self):
        return reverse_lazy('lesson_detail', kwargs={
            'course_pk': self.object.module.course.pk,
            'module_pk': self.object.module.pk,
            'lesson_pk': self.object.pk
        })


class TutorsListView(TemplateView):
    """Список преподавателей (пользователи с ролью 'tutor')"""
    template_name = 'courses/tutors.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutors'] = UserProfile.objects.filter(role='tutor').select_related('user')
        return context


class CartView(TemplateView):
    """Страница корзины с выбранными курсами"""
    template_name = 'courses/cart.html'

    def get_cart_course_ids(self):
        return self.request.session.get('cart', [])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_ids = self.get_cart_course_ids()
        courses = Course.objects.filter(id__in=cart_ids, is_published=True)
        total_amount = sum(course.price for course in courses if not course.is_free)
        context['courses'] = courses
        context['total_amount'] = total_amount
        return context


class AddToCartView(LoginRequiredMixin, View):
    """Добавление курса в корзину"""

    def post(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=kwargs['pk'], is_published=True)
        cart = request.session.get('cart', [])
        if course.id not in cart:
            cart.append(course.id)
            request.session['cart'] = cart
            messages.success(request, f'Курс «{course.title}» добавлен в корзину.')
        else:
            messages.info(request, 'Этот курс уже есть в вашей корзине.')
        return redirect('cart')


class RemoveFromCartView(LoginRequiredMixin, View):
    """Удаление курса из корзины"""

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', [])
        course_id = kwargs['pk']
        if course_id in cart:
            cart.remove(course_id)
            request.session['cart'] = cart
            messages.success(request, 'Курс удалён из корзины.')
        return redirect('cart')


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Оформление заказа из корзины"""
    template_name = 'courses/checkout.html'

    def get_cart_courses(self):
        cart_ids = self.request.session.get('cart', [])
        return Course.objects.filter(id__in=cart_ids, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_cart_courses()
        total_amount = sum(course.price for course in courses if not course.is_free)
        context['courses'] = courses
        context['total_amount'] = total_amount
        return context

    def post(self, request, *args, **kwargs):
        courses = self.get_cart_courses()
        if not courses:
            messages.warning(request, 'Ваша корзина пуста.')
            return redirect('cart')

        # Создаём заказ
        order = Order.objects.create(user=request.user, status='paid')
        for course in courses:
            OrderItem.objects.create(
                order=order,
                course=course,
                price=0 if course.is_free else course.price
            )
            # логически считаем, что доступ выдан: создаём Enrollment
            Enrollment.objects.get_or_create(user=request.user, course=course)

        # Очищаем корзину
        request.session['cart'] = []

        messages.success(request, f'Заказ #{order.pk} успешно оформлен. Доступ к курсам выдан.')
        return redirect('orders_history')


class OrdersHistoryView(LoginRequiredMixin, ListView):
    """История заказов пользователя"""
    model = Order
    template_name = 'courses/orders_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__course')


class AssistantFAQView(TemplateView):
    """Простой онлайн‑ассистент на основе категорий вопросов"""
    template_name = 'courses/assistant_faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = AssistantCategory.objects.prefetch_related('questions').all()
        current_category_id = self.request.GET.get('category')
        current_category = None
        questions = []

        if current_category_id:
            current_category = AssistantCategory.objects.filter(id=current_category_id).first()
        if not current_category and categories:
            current_category = categories[0]

        if current_category:
            questions = current_category.questions.all()

        context['categories'] = categories
        context['current_category'] = current_category
        context['questions'] = questions
        return context


class AssistantContactView(FormView):
    """Форма 'не нашли ответ — оставьте контакт'"""
    template_name = 'courses/assistant_contact.html'
    success_url = reverse_lazy('assistant_contact')

    class SimpleSupportForm(forms.Form):
        name = forms.CharField(label='Ваше имя', max_length=100)
        contact = forms.CharField(
            label='Контакт для связи (email, Telegram и т.п.)',
            max_length=150,
        )
        message = forms.CharField(
            label='Ваш вопрос',
            widget=forms.Textarea(attrs={'rows': 4}),
        )

    form_class = SimpleSupportForm

    def form_valid(self, form):
        SupportRequest.objects.create(
            name=form.cleaned_data['name'],
            contact=form.cleaned_data['contact'],
            message=form.cleaned_data['message'],
        )
        messages.success(
            self.request,
            'Спасибо! Мы получили ваш вопрос и свяжемся с вами по указанному контакту.',
        )
        return super().form_valid(form)


class AdminStatsView(UserPassesTestMixin, TemplateView):
    """Простая страница аналитики (для администратора)"""
    template_name = 'courses/admin_stats.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Топ‑5 самых продаваемых курсов
        top_courses = (
            OrderItem.objects.values('course__title')
            .annotate(total_sold=Sum('id'))
            .order_by('-total_sold')[:5]
        )

        # Выручка за последний месяц по оплаченным заказам
        last_month = timezone.now() - timezone.timedelta(days=30)
        recent_paid_items = OrderItem.objects.filter(
            order__status='paid',
            order__created_at__gte=last_month,
        )
        revenue_last_month = recent_paid_items.aggregate(total=Sum('price'))['total'] or 0
        orders_count_last_month = (
            Order.objects.filter(status='paid', created_at__gte=last_month).count()
        )

        context['top_courses'] = top_courses
        context['revenue_last_month'] = revenue_last_month
        context['orders_count_last_month'] = orders_count_last_month
        return context


class CourseRecommendationView(TemplateView):
    """Простой тест подбора курса"""
    template_name = 'courses/recommendation_test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['result_courses'] = None

        direction = self.request.GET.get('direction')
        level = self.request.GET.get('level')
        free_only = self.request.GET.get('free') == 'on'

        if direction or level or free_only:
            qs = Course.objects.filter(is_published=True)
            if level and level != 'all':
                qs = qs.filter(level=level)
            if free_only:
                qs = qs.filter(is_free=True)
            if direction:
                qs = qs.filter(
                    Q(title__icontains=direction) |
                    Q(category__name__icontains=direction)
                )
            context['result_courses'] = qs[:5]

        return context

# ... предыдущий код остается без изменений ...

class MarkLessonCompletedView(LoginRequiredMixin, View):
    """Представление для отметки урока как пройденного/не пройденного"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        lesson_id = request.POST.get('lesson_id')
        completed = request.POST.get('completed') == 'true'
        
        if not lesson_id:
            return JsonResponse({'success': False, 'error': 'Не указан ID урока'}, status=400)
        
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        
        # Проверяем, имеет ли пользователь доступ к уроку
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Требуется авторизация'}, status=403)
        
        # Проверяем, записан ли пользователь на курс
        if not hasattr(request.user, 'enrollment_set') or \
           not request.user.enrollment_set.filter(course=lesson.module.course).exists():
            return JsonResponse({'success': False, 'error': 'Вы не записаны на этот курс'}, status=403)
        
        # Получаем или создаем запись прогресса
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'completed': completed}
        )
        
        # Если запись уже существует, обновляем ее
        if not created:
            progress.completed = completed
            progress.save()
        
        # Получаем статистику прогресса
        module = lesson.module
        course = module.course
        
        # Прогресс модуля
        module_completed = Progress.objects.filter(
            user=request.user,
            lesson__module=module,
            completed=True
        ).count()
        module_total = module.lessons.count()
        module_progress = int((module_completed / module_total) * 100) if module_total > 0 else 0
        
        # Прогресс курса
        course_completed = Progress.objects.filter(
            user=request.user,
            lesson__module__course=course,
            completed=True
        ).count()
        course_total = Lesson.objects.filter(module__course=course).count()
        course_progress = int((course_completed / course_total) * 100) if course_total > 0 else 0
        
        return JsonResponse({
            'success': True,
            'completed': progress.completed,
            'completed_at': progress.completed_at.strftime('%d.%m.%Y %H:%M') if progress.completed_at else None,
            'module_progress': module_progress,
            'course_progress': course_progress,
            'module_completed': module_completed,
            'module_total': module_total,
            'course_completed': course_completed,
            'course_total': course_total,
            'message': 'Урок отмечен как пройденный' if completed else 'Урок отмечен как непройденный'
        })