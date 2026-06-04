from django import forms


class ThreadForm(forms.Form):
    title = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'placeholder': 'Enter a descriptive title...',
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'rows': 8,
            'placeholder': 'Share your thoughts, questions, or insights...',
        })
    )


class ReplyForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-sm py-xs border border-outline-variant rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'rows': 4,
            'placeholder': 'Write your reply...',
        })
    )
