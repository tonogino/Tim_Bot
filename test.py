import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def looks_like_chat_model(model_id: str) -> bool:
    text = model_id.lower()
    bad = ["embedding", "rerank", "moderation", "image", "tts", "whisper", "audio"]
    if any(x in text for x in bad):
        return False
    good = ["claude", "gpt", "gemini", "sonnet", "opus", "chat"]
    return any(x in text for x in good)

def main() -> None:
    api_key = os.getenv("THIRD_PARTY_API_KEY")
    base_url = os.getenv("THIRD_PARTY_BASE_URL")

    if not api_key:
        raise RuntimeError("缺少 THIRD_PARTY_API_KEY，请在 .env 文件中填写有效的 API 密钥。")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)

    try:
        models = client.models.list()
        candidates = [m.id for m in models.data if looks_like_chat_model(m.id)]

        print("Found candidates:")
        for model in candidates[:50]:
            print("-", model)

        print("\nTesting candidates...\n")

        for model_name in candidates[:20]:
            try:
                print(f"Trying: {model_name}")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "请只回复：测试成功"}],
                    max_tokens=20,
                    temperature=0
                )
                print("SUCCESS:", model_name)
                print("Reply:", response.choices[0].message.content)
                break
            except Exception as exc:
                print("FAILED:", model_name)
                print(type(exc).__name__, exc)
                print("-" * 40)

    except Exception as exc:
        print("LIST MODELS FAILED:")
        print(type(exc).__name__, exc)


if __name__ == "__main__":
    main()
