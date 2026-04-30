# myBoard/board_project/board/forms.py

from django import forms


class WritingPostForm(forms.Form):
    user_english = forms.CharField(
        label="영어 문장",
        widget=forms.Textarea(
            attrs={
                "id": "user-text",
                "rows": 6,
                "placeholder": "교정받고 싶은 영어 문장을 입력하세요.",
            }
        ),
        error_messages={
            "required": "영어 문장을 입력해주세요.",
        },
    )

    native_text = forms.CharField(
        label="네이티브 문장",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "필요하다면 한국어 등 네이티브 문장이나 표현 의도를 입력하세요.",
            }
        ),
    )