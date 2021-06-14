from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import Category, Product

class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['is_active', 'photos', 'category', 'attributes', 'profit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'tags': forms.TextInput(attrs={'class': 'form-control',}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0,}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0,}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0,}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0,}),
        }
        labels = {
            'name': _('Name'),
            'description': _('Description'),
            'tags': _('Tags'),
            'stock': _('Stock'),
            'cost_price': _('Cost price, $'),
            'selling_price': _('Selling price, $'),
            'discount_percent': _('Discount, %'),
        }

class SelectCategoryProductForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True),
                                      empty_label='..',
                                      widget=forms.Select(attrs={'class': 'custom-select',}))