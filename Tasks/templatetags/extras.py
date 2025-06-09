from django import template
register = template.Library()

@register.filter
def get_status_color(value):
    return {
        'pending': '#fef3c7',        # Yellow
        'in_progress': '#e0e7ff',    # Blue
        'completed': '#d1fae5',      # Green
    }.get(value, '#f3f4f6')