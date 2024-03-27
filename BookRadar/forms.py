from django import forms
from django.contrib.auth.models import User

from BookRadar.models import Review, Book


class LoginForm(forms.Form):
    username = forms.CharField(max_length=64, label='', widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=64, label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(max_length=64, label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(max_length=64, label='',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'})
        }
        labels = {
            'username': '',
        }
        help_texts = {
            'username': '',
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Hasła nie pasują do siebie.')

        return password2


# class TitleChoiceField(forms.ModelChoiceField):
#     def to_python(self, value):
#         if value == '0':
#             return None
#         return super().to_python(value)
#
# class AuthorChoiceField(forms.ModelChoiceField):
#     def to_python(self, value):
#         if value == '0':
#             return None
#         return super().to_python(value)

class OpinionAddForm(forms.ModelForm):
    author = forms.ModelChoiceField(queryset=Book.objects.values_list('author', flat=True).distinct(), empty_label='---',  widget=forms.Select(attrs={'class': 'form-control'}))
    title = forms.ModelChoiceField(queryset=Book.objects.none(), empty_label='---', widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(OpinionAddForm, self).__init__(*args, **kwargs)
        if 'author' in self.data:
            try:
                author_id = int(self.data.get('author'))
                self.fields['title'].queryset = Book.objects.filter(author=author_id).values('id', 'title')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.author:
            self.fields['title'].queryset = Book.objects.filter(author=self.instance.author).values('id', 'title')

    class Meta:
        model = Review
        fields = ['author', 'title', 'comment', 'rating']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows':5}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'})
        }
