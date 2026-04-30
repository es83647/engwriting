# myBoard/board_project/board/views.py

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WritingPostForm
from .models import WritingPost
from .ai_services import (
    GeminiCorrectionError,
    call_gemini_for_correction,
    make_title_from_corrected_english,
    parse_saved_feedback,
)


def post_list(request):
    """
    메인 화면입니다.
    """

    posts = WritingPost.objects.all()

    if request.method == "POST":
        form = WritingPostForm(request.POST)

        if form.is_valid():
            user_english = form.cleaned_data["user_english"]
            native_text = form.cleaned_data.get("native_text") or ""

            try:
                result = call_gemini_for_correction(
                    user_english=user_english,
                    native_text=native_text or None,
                )

            except GeminiCorrectionError as exc:
                form.add_error(None, str(exc))
                return render(
                    request,
                    "post_list.html",
                    {
                        "form": form,
                        "posts": posts,
                    },
                )

            title = make_title_from_corrected_english(result.corrected_english)

            post = WritingPost.objects.create(
                title=title,
                native_text=native_text or None,
                user_english=user_english,
                ai_feedback=result.ai_feedback,
                corrected_english=result.corrected_english,
            )

            messages.success(request, "영어 문장 교정이 완료되었습니다.")
            return redirect("post_detail", pk=post.pk)

    else:
        form = WritingPostForm()

    return render(
        request,
        "post_list.html",
        {
            "form": form,
            "posts": posts,
        },
    )


def post_detail(request, pk):
    """
    교정 기록 상세 페이지입니다.
    """

    post = get_object_or_404(WritingPost, pk=pk)
    feedback = parse_saved_feedback(post.ai_feedback)

    return render(
        request,
        "post_detail.html",
        {
            "post": post,
            "feedback": feedback,
        },
    )


def post_delete(request, pk):
    """
    교정 기록 삭제 기능입니다.

    GET:
    - 삭제 확인 페이지 표시

    POST:
    - 실제 삭제 후 목록으로 이동
    """

    post = get_object_or_404(WritingPost, pk=pk)

    if request.method == "POST":
        post.delete()
        messages.success(request, "게시글이 삭제되었습니다.")
        return redirect("post_list")

    return render(
        request,
        "post_confirm_delete.html",
        {
            "post": post,
        },
    )