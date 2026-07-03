import json
import urllib.request


BASE_URL = "http://127.0.0.1:8000"


def post_chat(messages):
    data = json.dumps({"messages": messages}).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    print(urllib.request.urlopen(f"{BASE_URL}/health").read().decode("utf-8"))
    body = post_chat(
        [
            {
                "role": "user",
                "content": "Hiring graduate financial analysts. Need numerical reasoning and finance knowledge.",
            }
        ]
    )
    print(json.dumps(body, indent=2))

