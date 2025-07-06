from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='replace')
@stringfilter
def replace(value, arg):
    """Replace characters in the string.
    Usage: {{ value|replace:"old,new" }}
    """
    if not value:
        return ''
    try:
        old, new = arg.split(',')
        return value.replace(old, new)
    except (ValueError, AttributeError):
        return value

@register.filter(name='format_decimal')
def format_decimal(value, default='0,00'):
    """Format decimal numbers with comma as decimal separator."""
    if value is None or value == '':
        return default
    try:
        # Convert to float first to handle both string and number inputs
        num = float(value)
        # Format with 2 decimal places and replace . with ,
        return f"{num:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")
    except (ValueError, TypeError):
        return default
