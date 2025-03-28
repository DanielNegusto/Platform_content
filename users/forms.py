from django import forms

from users.models import User


class SignUpForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=15, required=True, label="Phone Number"
    )
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, required=True, label="Confirm Password"
    )
    consent_personal_data = forms.BooleanField(
        required=True, label="Я даю согласие на обработку персональных данных"
    )

    class Meta:
        model = User
        fields = [
            "phone_number",
            "email",
            "password",
            "confirm_password",
            "consent_personal_data",
        ]  # Убедитесь, что поля соответствуют вашим требованиям

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
            "description",
        ]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "phone_number": "Номер телефона",
            "description": "Описание",
        }
