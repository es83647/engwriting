document.addEventListener("DOMContentLoaded", function () {
    const writingForm = document.getElementById("writing-form");
    const submitBtn = document.getElementById("submit-btn");

    if (writingForm && submitBtn) {
        writingForm.addEventListener("submit", function () {
            submitBtn.disabled = true;
            submitBtn.textContent = "교정 중...";
        });
    }

    const textarea = document.getElementById("user-text");
    const charCount = document.getElementById("char-count");
    const wordCount = document.getElementById("word-count");

    if (textarea && charCount && wordCount) {
        textarea.addEventListener("input", function () {
            const text = textarea.value;

            charCount.textContent = text.length;

            const words = text.trim().split(/\s+/).filter(Boolean);
            wordCount.textContent = words.length;
        });
    }
});