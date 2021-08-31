from django import template
from django.utils.http import urlencode
# TODO this might help

register = template.Library()

@register.filter
def addstr(str1, str2):
    """Concatenate strings str1 & str2"""
    return str(str1) + str(str2)

@register.filter
def remove_first_occ_substr(str1, str2):
    """Remove the first occurence of str2 from str1"""
    return str(str1).replace(str(str2), '', 1)

@register.filter
def remove_first_occ_url_param(path, param):
    """Remove the first occurence of param from path"""
    new_path = str(path).replace(str(param), '', 1)
    if '&' in new_path:
        new_path = new_path.split('&', 1)[1]
    new_path = new_path.replace('?&', '?')
    # new_path = new_path.replace('&&', '&')
    return new_path[:-1] if new_path.endswith('&') else new_path


@register.filter
def remove_all_occ_url_param(path, param_start):
    """Remove all occurence of param from path"""
    param_start = str(param_start)
    new_path = str(path)
    while True:
        if param_start not in new_path: break
        new_path, new_path_end = new_path.split(param_start, 1)
        if '&' in new_path_end:
            new_path += new_path_end.split('&', 1)[1]
    new_path = new_path.replace('?&', '?')
    # new_path = new_path.replace('&&', '&')
    return new_path[:-1] if new_path.endswith('&') else new_path