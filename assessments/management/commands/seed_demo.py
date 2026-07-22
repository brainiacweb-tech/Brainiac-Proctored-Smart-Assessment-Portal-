from django.core.management.base import BaseCommand
from accounts.models import User
from assessments.models import Quiz, Question
from .quiz_question_banks import QUESTION_BANKS

QUIZZES = [
    {
        'title': 'Introduction to Python',
        'description': 'Test your knowledge of Python fundamentals — variables, functions, data types, OOP, and exception handling.',
        'time_limit_mins': 50,
        'max_allowed_warnings': 3,
    },
    {
        'title': 'Mobile App Development',
        'description': 'Cover core concepts in mobile development — platforms, UI patterns, lifecycle, APIs, and cross-platform frameworks.',
        'time_limit_mins': 50,
        'max_allowed_warnings': 3,
    },
    {
        'title': 'Networking and Security',
        'description': 'Assess your understanding of network protocols, encryption, firewalls, and cybersecurity best practices.',
        'time_limit_mins': 50,
        'max_allowed_warnings': 3,
    },
    {
        'title': 'Database Management',
        'description': 'Evaluate your skills in relational databases, SQL queries, normalization, and database design principles.',
        'time_limit_mins': 50,
        'max_allowed_warnings': 3,
    },
    {
        'title': 'Company Law',
        'description': 'Test knowledge of corporate governance, legal structures, directors duties, and business regulations.',
        'time_limit_mins': 50,
        'max_allowed_warnings': 3,
    },
]

QUESTIONS_PER_QUIZ = 25


class Command(BaseCommand):
    help = 'Seed demo instructor, student, and five quizzes with 25 questions each'

    def handle(self, *args, **options):
        instructor, created = User.objects.get_or_create(
            username='instructor',
            defaults={'email': 'instructor@example.com', 'role': User.Role.INSTRUCTOR},
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write('Created instructor (instructor / instructor123)')
        else:
            self.stdout.write('Instructor already exists')

        student, created = User.objects.get_or_create(
            username='student',
            defaults={'email': 'student@example.com', 'role': User.Role.STUDENT},
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write('Created student (student / student123)')
        else:
            self.stdout.write('Student already exists')

        for quiz_def in QUIZZES:
            quiz_data = quiz_def.copy()
            title = quiz_data['title']
            quiz, created = Quiz.objects.get_or_create(
                title=title,
                created_by=instructor,
                defaults=quiz_data,
            )
            if not created:
                for key, val in quiz_data.items():
                    setattr(quiz, key, val)
                quiz.save()

            if quiz.questions.count() != QUESTIONS_PER_QUIZ:
                quiz.questions.all().delete()
                for raw in QUESTION_BANKS[title]:
                    qd = raw.copy()
                    qtype = qd.pop('question_type', Question.QuestionType.MULTIPLE_CHOICE)
                    Question.objects.create(quiz=quiz, question_type=qtype, **qd)
                self.stdout.write(f'Seeded "{title}" with {quiz.questions.count()} questions')
            else:
                self.stdout.write(f'"{title}" already has {QUESTIONS_PER_QUIZ} questions')

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete — {Quiz.objects.count()} quizzes, {QUESTIONS_PER_QUIZ} questions each.'
        ))
