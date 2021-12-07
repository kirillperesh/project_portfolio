from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm, UsernameField, PasswordChangeForm
from django.db.models.fields import EmailField
from django.forms import fields
from django.utils.translation import gettext_lazy as _

from .models import Category, Product


class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['is_active', 'photos', 'category', 'attributes', 'profit', 'end_user_price']
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

    def is_valid_check_same_name(self, *, current_name):
        """Calls self.is_valid().
        Returns True if the ['Product with this Name already exists.'] error was caused by not changing the initial name. Removes this error if it's the only one."""
        form_is_valid = self.is_valid()
        if not form_is_valid:
            # the order here is important
            if 'name' in list(self.errors.keys()) and ['Product with this Name already exists.'] == self.errors['name'] and self.data['name'] == current_name:
                self.cleaned_data['name'] = current_name
                if ['name'] == list(self.errors.keys()): form_is_valid = True
                self.errors.pop('name')
        return form_is_valid

class SelectCategoryProductForm(forms.Form):
    category = forms.ModelChoiceField(required=True,
                                      queryset=Category.objects.filter(is_active=True),
                                      empty_label='..',
                                      widget=forms.Select(attrs={'class': 'custom-select',}))

class PhotosForm(forms.Form):
    photos = forms.ImageField(required=False,
                              widget=forms.ClearableFileInput(attrs={'multiple': True,
                                                                     'accept': "image/*",
                                                                     'id': "photosInput",
                                                                     'name': "photos",
                                                                     'type': "file",
                                                                     'style': "display:none;",
                                                                     'onchange': "previewImages(event)"}))

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class':'required', 'placeholder': _('General Kenobi! (username)'),}),
            'first_name': forms.TextInput(attrs={'placeholder': _('First name..'),}),
            'last_name': forms.TextInput(attrs={'placeholder': _('Last name..'),}),
            'email': forms.EmailInput(attrs={'placeholder': _('Email..'),}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Password..'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Repeat password..'})

class SignInForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'class':'required', 'placeholder': 'Username'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Password'})

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Old password'})
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'New password'})
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Repeat new password'})

class UsernameChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username',)
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'required':True, 'placeholder': 'New username'})
        
    def clean(self):
        cleaned_data = super().clean()
        if self.has_changed():
            username = self.cleaned_data['username']
            initial_username = self.initial['username']
            if username == initial_username: self.add_error('username', "That's the same username you've been already using")
        return cleaned_data

class EmailChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget = forms.EmailInput(attrs={'required':True, 'placeholder': 'New email'})

    def clean(self):
        cleaned_data = super().clean()
        if self.has_changed():
            email = self.cleaned_data['email']
            initial_email = self.initial['email']
                    
            if email == initial_email:
                self.add_error('email', "That's the same email you've been already using")
            elif User.objects.filter(email=email).exclude(email=initial_email).exists():
                self.add_error('email', 'That email is already being used by another user')                
        return cleaned_data
