from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label="Новая категория",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите название новой категории",
            }
        ),
    )

    class Meta:
        model = Post
        fields = ["title", "content", "status", "image", "video", "categories"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите заголовок"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Введите содержание",
                }
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "video": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "categories": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "title": "Заголовок",
            "content": "Содержание",
            "status": "Статус",
            "image": "Изображение",
            "video": "Видео",
            "categories": "Категории",
        }
