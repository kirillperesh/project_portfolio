from django.contrib.auth.models import User
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import Tile


class AddEditTileForm(ModelForm):
    class Meta:
        model = Tile
        fields = ['title', 'post', 'background_link']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': _('Enter the title of your post'),
                'size': '100%',
                'style': 'text-align: center;',
                }),
            'post': forms.Textarea(attrs={
                'placeholder': _('Your post goes here'),
                'style': 'width: 53em; height: 15em; text-align: center;',
                }),
            'background_link': forms.URLInput(attrs={
                'placeholder':
                _('Enter a valid URL for background picture or YOUTUBE video'),
                'size': '100%',
                'style': 'text-align: center;',
                }),
        }

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class':'required', 'placeholder': _('Username.. (used for logging in)'),}),
            'first_name': forms.TextInput(attrs={'placeholder': _('First name..'),}),
            'last_name': forms.TextInput(attrs={'placeholder': _('Last name..'),}),
            'email': forms.EmailInput(attrs={'placeholder': _('Email..'),}),
        }
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Password..'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Repeat password..'})

class SignInForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(SignInForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'class':'required', 'placeholder': 'Username'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'class':'required', 'placeholder': 'Password'})
