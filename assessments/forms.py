from django import forms
from .models import Quiz, Question


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit_mins', 'max_allowed_warnings', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'time_limit_mins': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_allowed_warnings': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'correct_text', 'order',
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'option_a': forms.TextInput(attrs={'class': 'form-input'}),
            'option_b': forms.TextInput(attrs={'class': 'form-input'}),
            'option_c': forms.TextInput(attrs={'class': 'form-input'}),
            'option_d': forms.TextInput(attrs={'class': 'form-input'}),
            'correct_option': forms.Select(
                choices=[('', '--'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
                attrs={'class': 'form-select'},
            ),
            'correct_text': forms.TextInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }
