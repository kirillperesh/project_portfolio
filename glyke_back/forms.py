from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import Category, Product

class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'tags', 'stock', 'photos']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'tags': forms.TextInput(attrs={'class': 'form-control',}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0,}),
            # 'post': forms.Textarea(attrs={
            #     'placeholder': _('Your post goes here'),
            #     'style': 'width: 53em; height: 15em; text-align: center;',
            #     }),
            # 'background_link': forms.URLInput(attrs={
            #     'placeholder':
            #     _('Enter a valid URL for background picture or YOUTUBE video'),
            #     'size': '100%',
            #     'style': 'text-align: center;',
            #     }),
        }

class SelectCategoryProductForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True),
                                      empty_label='..',
                                      widget=forms.Select(attrs={'class': 'custom-select',}))