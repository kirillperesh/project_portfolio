from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import Category, Product

class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'tags']

class SelectCategoryProductForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True),
                                      empty_label=_('select category'))