# myBoard/board_project/board/admin.py

from django.contrib import admin

from .models import WritingPost


@admin.register(WritingPost)
class WritingPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "created_at",
    )
    search_fields = (
        "title",
        "user_english",
        "corrected_english",
        "native_text",
    )
    list_filter = (
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )
