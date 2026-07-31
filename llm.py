"""LLM client wrapper supporting Anthropic, OpenAI, and OpenAI-compatible
free providers (e.g. Groq)."""
import json
import re

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o-mini",
    "groq": "llama-3.3-70b-versatile",
}

# OpenAI-compatible providers: same SDK/wire format, different base_url.
OPENAI_COMPATIBLE_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
}


class LLMClient:
    def __init__(self, provider, model, api_key):
        if not api_key:
            raise ValueError(f"Missing API key for provider '{provider}'.")

        self.provider = provider
        self.model = model or DEFAULT_MODELS.get(provider)

        if provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        elif provider == "openai":
            import openai
            self._client = openai.OpenAI(api_key=api_key)
        elif provider in OPENAI_COMPATIBLE_BASE_URLS:
            import openai
            self._client = openai.OpenAI(api_key=api_key, base_url=OPENAI_COMPATIBLE_BASE_URLS[provider])
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def chat(self, system_prompt, user_message):
        """Single-turn or multi-turn call. user_message may be a string or a
        list of alternating user/assistant strings (starting with a user turn).
        Returns the text response."""
        if isinstance(user_message, str):
            history = [user_message]
        else:
            history = list(user_message)

        if self.provider == "anthropic":
            return self._chat_anthropic(system_prompt, history)
        else:
            return self._chat_openai(system_prompt, history)

    def _chat_anthropic(self, system_prompt, history):
        messages = []
        for i, text in enumerate(history):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": text})

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
            )
        except Exception as e:
            raise ValueError(f"Anthropic API call failed: {e}")

        return "".join(block.text for block in response.content if block.type == "text")

    def _chat_openai(self, system_prompt, history):
        messages = [{"role": "system", "content": system_prompt}]
        for i, text in enumerate(history):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": text})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {e}")

        return response.choices[0].message.content

    def chat_json(self, system_prompt, user_message):
        """Same as chat() but parses JSON from the response, stripping
        markdown code fences if present."""
        raw = self.chat(system_prompt, user_message)
        cleaned = _strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response was not valid JSON: {e}\nResponse: {raw}")


def _strip_code_fences(text):
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
