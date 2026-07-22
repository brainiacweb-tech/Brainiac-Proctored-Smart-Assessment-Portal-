from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),

    # Quiz CRUD (instructor)
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quizzes/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),

    # Questions
    path('quizzes/<int:quiz_pk>/questions/add/', views.question_add, name='question_add'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),

    # Audit
    path('audit/', views.audit_dashboard, name='audit_dashboard'),
    path('audit/<int:quiz_pk>/', views.audit_dashboard, name='audit_dashboard_quiz'),

    # Student quiz flow
    path('quiz/<int:pk>/start/', views.start_quiz, name='start_quiz'),
    path('attempt/<int:attempt_pk>/take/', views.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_pk>/', views.attempt_detail, name='attempt_detail'),

    # API endpoints
    path('api/attempt/<int:attempt_pk>/submit/', views.submit_quiz, name='submit_quiz'),
    path('api/attempt/<int:attempt_pk>/violation/', views.log_violation, name='log_violation'),
    path('api/attempt/<int:attempt_pk>/analyze/', views.analyze_frame_api, name='analyze_frame'),
    path('api/attempt/<int:attempt_pk>/status/', views.attempt_status, name='attempt_status'),
]
