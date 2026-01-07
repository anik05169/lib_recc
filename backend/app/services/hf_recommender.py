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
                "role": "user",
                "content": f"Recommend 3 real books based on this description:\n{user_description}"
            }
        ],
        "max_tokens": 256,
        "temperature": 0.7
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    # CRITICAL: print HF error if any
    if response.status_code != 200:
        print("HF STATUS:", response.status_code)
        print("HF RESPONSE:", response.text)
        response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]

