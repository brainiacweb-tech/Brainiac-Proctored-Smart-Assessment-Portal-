from django.contrib import admin
from .models import Quiz, Question, QuizAttempt, Answer, ViolationLog


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'time_limit_mins', 'max_allowed_warnings', 'is_active')
    inlines = [QuestionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'status', 'score', 'integrity_score', 'warning_count')
    list_filter = ('status',)


@admin.register(ViolationLog)
class ViolationLogAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'event_type', 'timestamp', 'duration_ms')
    list_filter = ('event_type',)
