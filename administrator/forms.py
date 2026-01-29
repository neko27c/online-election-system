# administrator/forms.py
from django import forms
from django.contrib.auth.hashers import make_password
from .models import Administrator

class AdministratorAdminForm(forms.ModelForm):
    class Meta:
        model = Administrator
        fields = "__all__"

    def clean_password(self):
        pw = self.cleaned_data["password"]
        # すでにハッシュならそのまま
        if pw.startswith("pbkdf2_"):
            return pw
        return make_password(pw)
