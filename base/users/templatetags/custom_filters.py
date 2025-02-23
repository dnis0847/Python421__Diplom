from django import template

register = template.Library()

@register.filter
def ru_pluralize(value, arg):
    """
    Склоняет слово в зависимости от числа.
    :param value: число
    :param arg: строка вида "час,часа,часов"
    :return: правильное склонение
    """
    arg = arg.split(',')
    value = abs(int(value))

    if value % 100 in (11, 12, 13, 14):
        return f"{value} {arg[2]}"
    elif value % 10 == 1:
        return f"{value} {arg[0]}"
    elif value % 10 in (2, 3, 4):
        return f"{value} {arg[1]}"
    else:
        return f"{value} {arg[2]}"
