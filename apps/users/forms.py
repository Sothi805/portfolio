from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
            'placeholder': 'you@example.com',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
            'placeholder': '••••••••',
        })
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
            'placeholder': 'Min. 8 characters',
        }),
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
            'placeholder': 'Repeat password',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
                'placeholder': 'johndoe',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg bg-surface text-on-surface placeholder:text-outline focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors',
                'placeholder': 'you@example.com',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', 'Email already registered.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
