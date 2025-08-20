from django import template
register = template.Library()

def zip_lists(a, b):
    return zip(a, b)
register.filter('zip', zip_lists) 