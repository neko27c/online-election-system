from django import forms
from .models import Voter
class LoginForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ['PersonalInfo', 'Voter', 'VoteStatus']
        labels = {
            'PersonalInfo': '個人情報',
            'Voter': '投票者',
            'VoteStatus': '投票状況',
        }