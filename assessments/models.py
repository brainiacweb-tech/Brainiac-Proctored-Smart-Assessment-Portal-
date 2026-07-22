from django.db import models
from django.conf import settings
from django.utils import timezone


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_mins = models.PositiveIntegerField(default=30)
    max_allowed_warnings = models.PositiveIntegerField(default=3)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_quizzes',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
        SHORT_ANSWER = 'SA', 'Short Answer'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(
        max_length=2,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
    )
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_option = models.CharField(
        max_length=1,
        blank=True,
        help_text='A, B, C, or D for multiple choice',
    )
    correct_text = models.CharField(
        max_length=500,
        blank=True,
        help_text='Expected answer for short answer questions',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.quiz.title} - Q{self.order + 1}'


class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        DISQUALIFIED = 'DISQUALIFIED', 'Disqualified'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    integrity_score = models.FloatField(default=100.0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    warning_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.student.username} - {self.quiz.title} ({self.status})'

    @property
    def violation_count(self):
        return self.violations.count()

    def calculate_integrity_score(self):
        penalty = getattr(settings, 'PROCTOR_INTEGRITY_PENALTY', 15)
        self.integrity_score = max(0, 100 - (self.violation_count * penalty))
        return self.integrity_score

    def recalculate_score(self):
        """Calculate score from submitted answers."""
        answers = self.answers.select_related('question')
        if not answers.exists():
            return 0.0

        correct = 0
        total = answers.count()
        for ans in answers:
            q = ans.question
            if q.question_type == Question.QuestionType.MULTIPLE_CHOICE:
                if ans.selected_option and ans.selected_option.upper() == q.correct_option.upper():
                    correct += 1
            elif q.question_type == Question.QuestionType.SHORT_ANSWER:
                if ans.text_answer and q.correct_text:
                    if ans.text_answer.strip().lower() == q.correct_text.strip().lower():
                        correct += 1

        self.score = round((correct / total) * 100, 1) if total else 0.0
        return self.score


class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True)
    text_answer = models.TextField(blank=True)

    class Meta:
        unique_together = [['attempt', 'question']]


class ViolationLog(models.Model):
    class EventType(models.TextChoices):
        TAB_SWITCH = 'TAB_SWITCH', 'Tab Switch / Window Blur'
        WINDOW_BLUR = 'WINDOW_BLUR', 'Window Focus Lost'
        NO_FACE = 'NO_FACE', 'No Face Detected'
        MULTIPLE_FACES = 'MULTIPLE_FACES', 'Multiple Faces Detected'
        HEAD_TURNED = 'HEAD_TURNED', 'Head Turned Away'
        NOISE_DETECTED = 'NOISE_DETECTED', 'Excessive Noise Detected'
        MULTIPLE_DISPLAY = 'MULTIPLE_DISPLAY', 'Multiple Displays Detected'

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='violations')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    timestamp = models.DateTimeField(default=timezone.now)
    duration_ms = models.PositiveIntegerField(default=0)
    snapshot_base64 = models.TextField(blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.event_type} @ {self.timestamp}'
