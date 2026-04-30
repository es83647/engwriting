# myBoard/board_project/board/models.py

from django.db import models


class WritingPost(models.Model):
    title = models.CharField(
        max_length=200,
        help_text="교정된 영어 문장의 첫 문장을 제목으로 사용합니다.",
    )
    native_text = models.TextField(
        blank=True,
        null=True,
        help_text="사용자의 네이티브 언어 문장입니다. 없을 수도 있습니다.",
    )
    user_english = models.TextField(
        help_text="사용자가 입력한 영어 원문입니다.",
    )
    ai_feedback = models.TextField(
        help_text="Gemini가 반환한 교정 및 추천 전체 텍스트입니다.",
    )
    corrected_english = models.TextField(
        help_text="Gemini가 교정한 최종 영어 문장입니다.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="게시글 생성 날짜입니다.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Writing Post"
        verbose_name_plural = "Writing Posts"

    def __str__(self):
        return self.title

