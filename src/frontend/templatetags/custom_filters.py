from django import template

register = template.Library()

@register.filter(name='boolean_status')
def boolean_status(value):
    return 'enabled' if value else 'disabled'

@register.filter(name='split_messages')
def split_messages(value, arg):
    try:
        return value.split(arg)
    except (ValueError, AttributeError):
        return [value, '']
