import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Avg

from .models import Quiz, Question, QuizAttempt, Answer, ViolationLog
from .forms import QuizForm, QuestionForm
from .proctor import analyze_frame


def instructor_required(view_func):
    """Decorator ensuring the user is an instructor."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_instructor:
            return HttpResponseForbidden('Instructor access required.')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard(request):
    """Role-based dashboard redirect."""
    if request.user.is_instructor:
        return redirect('assessments:instructor_dashboard')
    return redirect('assessments:student_dashboard')


@login_required
def student_dashboard(request):
    if request.user.is_instructor:
        return redirect('assessments:instructor_dashboard')

    quizzes = Quiz.objects.filter(is_active=True)
    attempts = QuizAttempt.objects.filter(student=request.user).select_related('quiz')
    attempt_map = {a.quiz_id: a for a in attempts}

    quiz_items = [
        {'quiz': quiz, 'attempt': attempt_map.get(quiz.id)}
        for quiz in quizzes
    ]

    context = {'quiz_items': quiz_items}
    return render(request, 'assessments/student_dashboard.html', context)


@login_required
@instructor_required
def instructor_dashboard(request):
    quizzes = Quiz.objects.filter(created_by=request.user).annotate(
        attempt_count=Count('attempts'),
    )
    recent_attempts = QuizAttempt.objects.filter(
        quiz__created_by=request.user,
    ).select_related('student', 'quiz').order_by('-start_time')[:20]

    stats = QuizAttempt.objects.filter(quiz__created_by=request.user).aggregate(
        avg_score=Avg('score'),
        avg_integrity=Avg('integrity_score'),
        total_attempts=Count('id'),
    )

    context = {
        'quizzes': quizzes,
        'recent_attempts': recent_attempts,
        'stats': stats,
    }
    return render(request, 'assessments/instructor_dashboard.html', context)


@login_required
@instructor_required
def quiz_list(request):
    quizzes = Quiz.objects.filter(created_by=request.user)
    return render(request, 'assessments/quiz_list.html', {'quizzes': quizzes})


@login_required
@instructor_required
def quiz_create(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created.')
            return redirect('assessments:quiz_edit', pk=quiz.pk)
    else:
        form = QuizForm()
    return render(request, 'assessments/quiz_form.html', {'form': form, 'is_edit': False})


@login_required
@instructor_required
def quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    questions = quiz.questions.all()

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated.')
            return redirect('assessments:quiz_edit', pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)

    return render(request, 'assessments/quiz_form.html', {
        'form': form,
        'quiz': quiz,
        'questions': questions,
        'is_edit': True,
    })


@login_required
@instructor_required
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    if request.method == 'POST':
        title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{title}" deleted.')
        return redirect('assessments:instructor_dashboard')
    return render(request, 'assessments/quiz_confirm_delete.html', {'quiz': quiz})


@login_required
@instructor_required
def question_add(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, created_by=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question added.')
            return redirect('assessments:quiz_edit', pk=quiz.pk)
    else:
        form = QuestionForm(initial={'order': quiz.questions.count()})
    return render(request, 'assessments/question_form.html', {
        'form': form,
        'quiz': quiz,
        'is_edit': False,
    })


@login_required
@instructor_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated.')
            return redirect('assessments:quiz_edit', pk=question.quiz.pk)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'assessments/question_form.html', {
        'form': form,
        'quiz': question.quiz,
        'is_edit': True,
    })


@login_required
@instructor_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    quiz_pk = question.quiz.pk
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
        return redirect('assessments:quiz_edit', pk=quiz_pk)
    return render(request, 'assessments/question_confirm_delete.html', {'question': question})


@login_required
@instructor_required
def audit_dashboard(request, quiz_pk=None):
    """Instructor audit dashboard with violation snapshots."""
    if quiz_pk:
        quiz = get_object_or_404(Quiz, pk=quiz_pk, created_by=request.user)
        attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student').prefetch_related('violations')
    else:
        quiz = None
        attempts = QuizAttempt.objects.filter(
            quiz__created_by=request.user,
        ).select_related('student', 'quiz').prefetch_related('violations')

    context = {
        'quiz': quiz,
        'attempts': attempts,
        'quizzes': Quiz.objects.filter(created_by=request.user),
    }
    return render(request, 'assessments/audit_dashboard.html', context)


@login_required
def attempt_detail(request, attempt_pk):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_pk)
    if request.user.is_student and attempt.student != request.user:
        return HttpResponseForbidden()
    if request.user.is_instructor and attempt.quiz.created_by != request.user:
        return HttpResponseForbidden()

    violations = attempt.violations.all()
    answers = attempt.answers.select_related('question')

    return render(request, 'assessments/attempt_detail.html', {
        'attempt': attempt,
        'violations': violations,
        'answers': answers,
    })


@login_required
def start_quiz(request, pk):
    """Pre-exam checks page before starting proctored quiz."""
    if request.user.is_instructor:
        return HttpResponseForbidden()

    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)

    existing = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz,
        status=QuizAttempt.Status.IN_PROGRESS,
    ).first()

    if existing:
        return redirect('assessments:take_quiz', attempt_pk=existing.pk)

    if request.method == 'POST':
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            status=QuizAttempt.Status.IN_PROGRESS,
        )
        for q in quiz.questions.all():
            Answer.objects.create(attempt=attempt, question=q)
        return redirect('assessments:take_quiz', attempt_pk=attempt.pk)

    return render(request, 'assessments/start_quiz.html', {'quiz': quiz})


@login_required
def take_quiz(request, attempt_pk):
    """Proctored quiz taking interface."""
    attempt = get_object_or_404(
        QuizAttempt,
        pk=attempt_pk,
        student=request.user,
        status=QuizAttempt.Status.IN_PROGRESS,
    )
    quiz = attempt.quiz
    questions = quiz.questions.all()
    answers = {a.question_id: a for a in attempt.answers.all()}

    question_items = [
        {'question': q, 'answer': answers.get(q.id)}
        for q in questions
    ]

    proctor_config = {
        'attemptId': attempt.pk,
        'frameIntervalMs': getattr(settings, 'PROCTOR_FRAME_INTERVAL_MS', 2000),
        'debounceChecks': getattr(settings, 'PROCTOR_FACE_DEBOUNCE_CHECKS', 2),
        'maxWarnings': quiz.max_allowed_warnings,
        'timeLimitMins': quiz.time_limit_mins,
        'noiseThreshold': getattr(settings, 'PROCTOR_NOISE_THRESHOLD', 0.38),
        'noiseDebounceChecks': getattr(settings, 'PROCTOR_NOISE_DEBOUNCE_CHECKS', 3),
        'noiseSampleMs': getattr(settings, 'PROCTOR_NOISE_SAMPLE_MS', 500),
        'displayCheckMs': getattr(settings, 'PROCTOR_DISPLAY_CHECK_MS', 3000),
        'displayDebounceChecks': getattr(settings, 'PROCTOR_DISPLAY_DEBOUNCE_CHECKS', 2),
        'violationCooldownMs': getattr(settings, 'PROCTOR_VIOLATION_COOLDOWN_MS', 15000),
    }

    return render(request, 'assessments/take_quiz.html', {
        'attempt': attempt,
        'quiz': quiz,
        'question_items': question_items,
        'proctor_config_json': json.dumps(proctor_config),
    })


@login_required
@require_POST
def submit_quiz(request, attempt_pk):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_pk, student=request.user)

    if attempt.status != QuizAttempt.Status.IN_PROGRESS:
        return JsonResponse({'error': 'Attempt already finalized.'}, status=400)

    data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    answers_data = data.get('answers', {})

    for q_id, ans_val in answers_data.items():
        try:
            answer = attempt.answers.get(question_id=int(q_id))
            if isinstance(ans_val, str) and len(ans_val) == 1 and ans_val.upper() in 'ABCD':
                answer.selected_option = ans_val.upper()
            else:
                answer.text_answer = ans_val
            answer.save()
        except Answer.DoesNotExist:
            pass

    attempt.end_time = timezone.now()
    attempt.status = QuizAttempt.Status.SUBMITTED
    attempt.recalculate_score()
    attempt.calculate_integrity_score()
    attempt.save()

    return JsonResponse({
        'status': 'submitted',
        'score': attempt.score,
        'integrity_score': attempt.integrity_score,
        'redirect': f'/assessments/attempt/{attempt.pk}/',
    })


@login_required
@require_POST
def log_violation(request, attempt_pk):
    """Record a frontend or backend-detected violation."""
    attempt = get_object_or_404(
        QuizAttempt,
        pk=attempt_pk,
        student=request.user,
        status=QuizAttempt.Status.IN_PROGRESS,
    )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event_type = data.get('event_type', 'TAB_SWITCH')
    snapshot = data.get('snapshot', '')
    duration_ms = data.get('duration_ms', 0)
    details = data.get('details', '')

    valid_types = [c[0] for c in ViolationLog.EventType.choices]
    if event_type not in valid_types:
        event_type = ViolationLog.EventType.TAB_SWITCH

    violation = ViolationLog.objects.create(
        attempt=attempt,
        event_type=event_type,
        snapshot_base64=snapshot,
        duration_ms=duration_ms,
        details=details,
    )

    attempt.warning_count += 1
    attempt.calculate_integrity_score()
    attempt.save(update_fields=['warning_count', 'integrity_score'])

    disqualified = False
    if attempt.warning_count >= attempt.quiz.max_allowed_warnings:
        attempt.status = QuizAttempt.Status.DISQUALIFIED
        attempt.end_time = timezone.now()
        attempt.save(update_fields=['status', 'end_time'])
        disqualified = True

    return JsonResponse({
        'logged': True,
        'violation_id': violation.pk,
        'warning_count': attempt.warning_count,
        'max_warnings': attempt.quiz.max_allowed_warnings,
        'integrity_score': attempt.integrity_score,
        'disqualified': disqualified,
    })


@login_required
@require_POST
def analyze_frame_api(request, attempt_pk):
    """Receive a camera snapshot, run CV analysis, optionally log violation."""
    attempt = get_object_or_404(
        QuizAttempt,
        pk=attempt_pk,
        student=request.user,
        status=QuizAttempt.Status.IN_PROGRESS,
    )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    frame_b64 = data.get('frame', '')
    confirm_strike = data.get('confirm_strike', False)

    result = analyze_frame(frame_b64)

    response = {
        'status': result['status'],
        'face_count': result['face_count'],
        'processed_frame': result['processed_frame'],
        'details': result['details'],
        'strike_logged': False,
    }

    status_to_event = {
        'FLAG_NO_FACE': ViolationLog.EventType.NO_FACE,
        'FLAG_MULTIPLE_FACES': ViolationLog.EventType.MULTIPLE_FACES,
        'FLAG_HEAD_TURNED': ViolationLog.EventType.HEAD_TURNED,
    }

    if confirm_strike and result['status'] in status_to_event:
        event_type = status_to_event[result['status']]
        ViolationLog.objects.create(
            attempt=attempt,
            event_type=event_type,
            snapshot_base64=result['processed_frame'],
            details=result['details'],
        )
        attempt.warning_count += 1
        attempt.calculate_integrity_score()
        attempt.save(update_fields=['warning_count', 'integrity_score'])

        response['strike_logged'] = True
        response['warning_count'] = attempt.warning_count
        response['max_warnings'] = attempt.quiz.max_allowed_warnings
        response['integrity_score'] = attempt.integrity_score

        if attempt.warning_count >= attempt.quiz.max_allowed_warnings:
            attempt.status = QuizAttempt.Status.DISQUALIFIED
            attempt.end_time = timezone.now()
            attempt.save(update_fields=['status', 'end_time'])
            response['disqualified'] = True

    return JsonResponse(response)


@login_required
@require_GET
def attempt_status(request, attempt_pk):
    """Poll attempt status (for disqualification check)."""
    attempt = get_object_or_404(QuizAttempt, pk=attempt_pk, student=request.user)
    return JsonResponse({
        'status': attempt.status,
        'warning_count': attempt.warning_count,
        'integrity_score': attempt.integrity_score,
    })
