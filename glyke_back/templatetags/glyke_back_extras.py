from django import template
from urllib.parse import quote_plus

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
def append_url_param_value(param_name, param_value):
    """Concatenate strings param_name & param_value, escaping spaces"""
    param_value = quote_plus(str(param_value), encoding='utf-8')
    return str(param_name) + str(param_value)

@register.filter
def remove_all_occ_url_param(current_params, param_to_remove):
    """Remove all occurences of param from path"""
    current_params = str(current_params)
    param_to_remove = str(param_to_remove)
    if param_to_remove not in current_params:
        return current_params
    param_list = current_params.split('&')
    param_list = ' '.join(param_list). split() # removes all empty strings from the list
    new_params = str()
    for param in param_list:
        if param_to_remove in param: continue
        new_params += param + '&'
    new_params = new_params[:-1] if new_params.endswith('&') else new_params
    return new_params

