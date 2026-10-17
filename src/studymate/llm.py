import re
import time
from typing import Any
from groq import Groq
from studymate.config import GROQ_API_KEY, MODEL, check_keys
from studymate.models import Usage

groq_client: Groq | None = None

def get_client() -> Groq:
    """Khởi tạo và trả về Groq client."""
    global groq_client
    if groq_client is None:
        check_keys()
        groq_client = Groq(api_key=GROQ_API_KEY, timeout=30.0, max_retries=0)
    return groq_client

def call_llm(
    messages: list[dict[str, str]],
    model: str | None = None,
    usage: Usage | None = None,
    temperature: float = 0.0,
    max_retries: int = 3,
) -> str:
    """Gọi LLM qua Groq API có retry và theo dõi token usage."""
    client = get_client()
    target_model = model or MODEL

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
            )
            
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0

            if usage:
                usage.add(prompt_tokens, completion_tokens)

            return response.choices[0].message.content or ""

        except Exception as e:
            error_msg = str(e)
            if attempt == max_retries:
                raise RuntimeError(f"Gọi LLM thất bại sau {max_retries} lần thử lại: {error_msg}") from e

            # Nếu gặp RateLimit 429 từ Groq, bóc tách thời gian yêu cầu chờ
            wait_time = 2 ** (attempt + 1)
            retry_match = re.search(r"try again in ([\d\.]+)s", error_msg, flags=re.IGNORECASE)
            if retry_match:
                try:
                    wait_time = float(retry_match.group(1)) + 1.0
                except ValueError:
                    pass

            time.sleep(wait_time)

    return ""
