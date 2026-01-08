import json
import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://router.huggingface.co/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
}

def recommend_books_hf(user_description: str):
    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a backend API that returns structured JSON.\n"
                    "Return ONLY valid JSON.\n\n"
                    "Return an object with a single key: recommendations.\n"
                    "recommendations must be an array of EXACTLY 3 objects.\n\n"
                    "Each object MUST contain:\n"
                    "- title: book title ONLY\n"
                    "- author: author name\n"
                    "- description: 1–2 factual sentences\n\n"
                    "Rules:\n"
                    "- Only REAL, well-known books\n"
                    "- No fictional books\n"
                    "- No opinions\n"
                    "- No markdown\n"
                    "- No explanations outside JSON\n"
                )
            },
            {
                "role": "user",
                "content": (
                    f'Recommend 3 real books related to "{user_description}".\n'
                    "Respond ONLY with valid JSON."
                )
            }
        ],
        "max_tokens": 350,
        "temperature": 0.2
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code != 200:
        print("HF STATUS:", response.status_code)
        print("HF RESPONSE:", response.text)
        response.raise_for_status()

    data = response.json()
    print("HF RAW RESPONSE:", json.dumps(data, indent=2))
    content = data["choices"][0]["message"]["content"].strip()
    print("HF CONTENT:", repr(content))

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("RAW MODEL OUTPUT:\n", content)
        return {"recommendations": []}
