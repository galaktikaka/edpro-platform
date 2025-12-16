from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Основные маршруты
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    
    # Контакты
    path('contact/', views.ContactFormView.as_view(), name='contact'),
    path('contact-form/', views.ContactFormView.as_view(), name='contact_form'),
    
    # Курсы
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Поиск
    path('search/', views.CourseSearchView.as_view(), name='course_search'),
    
    # Аутентификация
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='/'
    ), name='logout'),

    # Пользовательские маршруты
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),
    path('tutors/', views.TutorsListView.as_view(), name='tutors'),
    
    # Профиль
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    
    # Отзывы
    path('courses/<int:pk>/add-review/', views.AddReviewView.as_view(), name='add_review'),
    
    # Запись на курс
    path('enroll/', views.EnrollView.as_view(), name='enroll'),
    path('course/<int:pk>/enroll/', views.quick_enroll, name='quick_enroll'),

    # Онлайн‑помощник и аналитика
    path('assistant/faq/', views.AssistantFAQView.as_view(), name='assistant_faq'),
    path('assistant/contact/', views.AssistantContactView.as_view(), name='assistant_contact'),
    path('admin-stats/', views.AdminStatsView.as_view(), name='admin_stats'),
    path('assistant/test/', views.CourseRecommendationView.as_view(), name='course_recommendation'),
    path('projects/', TemplateView.as_view(template_name='courses/projects.html'), name='projects'),

    # Корзина и заказы
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrdersHistoryView.as_view(), name='orders_history'),

    # Модули
    path('courses/<int:course_pk>/modules/', views.ModuleListView.as_view(), name='module_list'),
    path('courses/<int:course_pk>/modules/create/', views.ModuleCreateView.as_view(), name='module_create'),
    path('courses/<int:course_pk>/modules/<int:module_pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('courses/<int:course_pk>/modules/<int:module_pk>/edit/', views.ModuleUpdateView.as_view(), name='module_edit'),
    path('courses/<int:course_pk>/modules/<int:module_pk>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),
    
    # Уроки
    path('courses/<int:course_pk>/modules/<int:module_pk>/lessons/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    path('courses/<int:course_pk>/modules/<int:module_pk>/lessons/<int:lesson_pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('courses/<int:course_pk>/modules/<int:module_pk>/lessons/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),

    # Прогресс
    path('progress/mark-lesson-completed/', views.MarkLessonCompletedView.as_view(), name='mark_lesson_completed'),
]