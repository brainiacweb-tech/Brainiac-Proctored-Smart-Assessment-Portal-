import html

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

QUIZ_THEMES = {
    'introduction to python': {
        'icon': 'code-2',
        'icon_class': 'w-6 h-6 text-emerald-600',
        'accent': 'from-emerald-500 to-teal-600',
        'icon_bg': 'bg-emerald-100',
        'tag': 'Programming',
    },
    'mobile app development': {
        'icon': 'smartphone',
        'icon_class': 'w-6 h-6 text-violet-600',
        'accent': 'from-violet-500 to-purple-600',
        'icon_bg': 'bg-violet-100',
        'tag': 'Mobile',
    },
    'networking and security': {
        'icon': 'shield-check',
        'icon_class': 'w-6 h-6 text-sky-600',
        'accent': 'from-sky-500 to-blue-600',
        'icon_bg': 'bg-sky-100',
        'tag': 'Security',
    },
    'database management': {
        'icon': 'database',
        'icon_class': 'w-6 h-6 text-amber-600',
        'accent': 'from-amber-500 to-orange-600',
        'icon_bg': 'bg-amber-100',
        'tag': 'Database',
    },
    'company law': {
        'icon': 'scale',
        'icon_class': 'w-6 h-6 text-rose-600',
        'accent': 'from-rose-500 to-pink-600',
        'icon_bg': 'bg-rose-100',
        'tag': 'Law',
    },
}

DEFAULT_THEME = {
    'icon': 'file-text',
    'icon_class': 'w-6 h-6 text-indigo-600',
    'accent': 'from-indigo-500 to-indigo-700',
    'icon_bg': 'bg-indigo-100',
    'tag': 'Assessment',
}


@register.filter
def quiz_theme(title):
    return QUIZ_THEMES.get(title.lower(), DEFAULT_THEME)


@register.simple_tag
def lucide(name, css_class='w-5 h-5', stroke='2'):
    """Render a Lucide icon without inclusion-tag context copying (Py 3.14 safe)."""
    return mark_safe(
        f'<i data-lucide="{html.escape(str(name))}" '
        f'class="{html.escape(str(css_class))}" '
        f'stroke-width="{html.escape(str(stroke))}"></i>'
    )
