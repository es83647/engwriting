# myBoard/board_project/board/ai_services.py

import json
import re
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from google import genai
from google.genai import types


class GeminiCorrectionError(Exception):
    """Gemini API 호출 또는 응답 처리 중 발생한 오류입니다."""


@dataclass
class CorrectionResult:
    corrected_english: str
    ai_feedback: str


def build_gemini_prompt(user_english: str, native_text: str | None = None) -> str:
    """
    사용자의 영어 문장과 선택적 네이티브 문장을 바탕으로
    Gemini에게 보낼 프롬프트를 생성합니다.
    """

    native_section = ""
    if native_text:
        native_section = f"""
        [사용자의 네이티브 문장 또는 의도 설명]
        {native_text}
        """

    prompt = f"""
        당신은 영어 작문 초보자를 돕는 영어 교정 튜터입니다.
        
        목표:
        - 사용자의 영어 문장을 자연스럽고 명확한 영어로 교정합니다.
        - 다만, 원문이 informal한 경우 informal한 표현을 과하게 formal하게 바꾸지 마세요.
        - 영어 커뮤니티에 복잡한 질문이나 짧은 게시물을 쓸 수 있도록 돕습니다.
        - 사용자의 네이티브 문장 또는 의도 설명이 제공된 경우, 그 의미를 참고해 영어 문장을 자연스럽게 다듬습니다.
        - 설명은 한국어로 작성합니다.
        - 사용자의 네이티브 문장은 원문 그대로 표기합니다.
        
        반드시 아래 JSON 형식만 출력하세요.
        마크다운 코드블록, 인사말, 사과, 서론은 쓰지 마세요.
        JSON 바깥에는 어떤 글자도 쓰지 마세요.
        
        {{
          "corrected_english": "교정된 최종 영어 문장 전체",
          "corrections": [
            {{
              "target": "교정할 대상 표현 또는 문장",
              "corrected": "교정된 표현 또는 문장",
              "reason": "교정한 이유"
            }}
          ],
          "suggestions": {{
            "word_adverb": [
              {{
                "item": "제안 단어 또는 부사",
                "reason": "제안한 이유"
              }}
            ],
            "verb_adjective": [
              {{
                "item": "제안 동사, 구동사 또는 형용사",
                "reason": "제안한 이유"
              }}
            ],
            "expression_idiom": [
              {{
                "item": "제안 표현 또는 숙어",
                "reason": "제안한 이유"
              }}
            ]
          }}
        }}
        
        주의:
        - corrected_english에는 반드시 교정된 최종 영어 문장만 넣으세요.
        - corrections 배열에는 최소 1개 이상 작성하세요.
        - 각 suggestions 배열에는 가능하면 2개 이상 작성하세요.
        - 제안할 내용이 정말 없으면 빈 배열 []을 사용하세요.
        
        {native_section}
        
        [사용자의 영어 문장]
        {user_english}
        """.strip()

    return prompt


def call_gemini_for_correction(user_english: str, native_text: str | None = None) -> CorrectionResult:
    """
    Gemini API를 호출하여 영어 교정 결과를 받습니다.
    """

    if not settings.GEMINI_API_KEY:
        raise GeminiCorrectionError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. myBoard/.env 파일을 확인하세요."
        )

    prompt = build_gemini_prompt(
        user_english=user_english,
        native_text=native_text,
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )

        response_text = response.text or ""

    except Exception as exc:
        raise GeminiCorrectionError(f"Gemini API 호출 실패: {exc}") from exc

    feedback_data = parse_gemini_json(response_text)
    corrected_english = str(feedback_data.get("corrected_english", "")).strip()

    if not corrected_english:
        raise GeminiCorrectionError(
            "Gemini 응답에서 corrected_english 값을 찾지 못했습니다. "
            "Gemini 응답 형식을 다시 확인해야 합니다."
        )

    if corrected_english in {"{", "}", "[", "]"}:
        raise GeminiCorrectionError(
            "Gemini 응답 파싱에 실패했습니다. JSON의 일부만 교정문으로 인식되었습니다."
        )

    feedback_data["corrected_english"] = corrected_english

    return CorrectionResult(
        corrected_english=corrected_english,
        ai_feedback=json.dumps(feedback_data, ensure_ascii=False),
    )


def parse_gemini_json(response_text: str) -> dict[str, Any]:
    """
    Gemini 응답을 JSON으로 파싱합니다.
    코드블록, 앞뒤 설명, 불필요한 공백이 섞인 경우도 최대한 보정합니다.
    """

    cleaned = clean_json_text(response_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        extracted = extract_json_object(cleaned)

        if not extracted:
            raise GeminiCorrectionError(
                "Gemini 응답을 JSON으로 파싱하지 못했습니다.\n\n"
                f"응답 앞부분:\n{response_text[:500]}"
            ) from exc

        try:
            data = json.loads(extracted)
        except json.JSONDecodeError as exc2:
            raise GeminiCorrectionError(
                "Gemini 응답에서 JSON처럼 보이는 부분을 찾았지만, 올바른 JSON이 아닙니다.\n\n"
                f"응답 앞부분:\n{response_text[:500]}"
            ) from exc2

    if not isinstance(data, dict):
        raise GeminiCorrectionError("Gemini 응답 JSON의 최상위 구조가 객체(dict)가 아닙니다.")

    return normalize_feedback_data(data)


def clean_json_text(text: str) -> str:
    """
    Gemini가 ```json 코드블록을 붙여도 제거합니다.
    """

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    return cleaned.strip()


def extract_json_object(text: str) -> str:
    """
    응답 안에서 첫 번째 { 부터 마지막 } 까지를 추출합니다.
    """

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return ""

    return text[start : end + 1].strip()


def normalize_feedback_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    템플릿에서 안전하게 사용할 수 있도록 Gemini 응답 구조를 보정합니다.
    """

    suggestions = data.get("suggestions")

    if not isinstance(suggestions, dict):
        suggestions = {}

    return {
        "corrected_english": str(data.get("corrected_english", "")).strip(),
        "corrections": normalize_corrections(data.get("corrections")),
        "suggestions": {
            "word_adverb": normalize_suggestion_list(suggestions.get("word_adverb")),
            "verb_adjective": normalize_suggestion_list(suggestions.get("verb_adjective")),
            "expression_idiom": normalize_suggestion_list(suggestions.get("expression_idiom")),
        },
        "raw_text": data.get("raw_text", ""),
    }


def normalize_corrections(value: Any) -> list[dict[str, str]]:
    """
    corrections 배열을 템플릿에서 안전하게 출력할 수 있는 형태로 보정합니다.
    """

    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        if not isinstance(item, dict):
            continue

        result.append(
            {
                "target": str(item.get("target", "")).strip(),
                "corrected": str(item.get("corrected", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
            }
        )

    return result


def normalize_suggestion_list(value: Any) -> list[dict[str, str]]:
    """
    suggestions 배열을 템플릿에서 안전하게 출력할 수 있는 형태로 보정합니다.
    """

    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        if not isinstance(item, dict):
            continue

        result.append(
            {
                "item": str(item.get("item", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
            }
        )

    return result


def parse_saved_feedback(ai_feedback: str) -> dict[str, Any]:
    """
    DB에 저장된 ai_feedback을 상세 페이지 표시용 dict로 변환합니다.
    기존에 저장된 일반 텍스트 피드백도 깨지지 않게 처리합니다.
    """

    try:
        data = json.loads(ai_feedback)
        if isinstance(data, dict):
            return normalize_feedback_data(data)
    except json.JSONDecodeError:
        pass

    return {
        "corrected_english": "",
        "corrections": [],
        "suggestions": {
            "word_adverb": [],
            "verb_adjective": [],
            "expression_idiom": [],
        },
        "raw_text": ai_feedback,
    }


def make_title_from_corrected_english(corrected_english: str) -> str:
    """
    교정된 영어 문장의 첫 문장을 게시글 제목으로 만듭니다.
    """

    text = corrected_english.strip().replace("\n", " ")

    if not text:
        return "Untitled"

    match = re.match(r"^(.+?[.!?])(\s|$)", text)

    if match:
        title = match.group(1).strip()
    else:
        title = text[:80].strip()

    if len(title) > 200:
        title = title[:197] + "..."

    return title