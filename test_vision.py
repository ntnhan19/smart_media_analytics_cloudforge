import requests

def test():
    # Provide a dummy base64 1x1 pixel black image
    img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    payload = {
        "model": "qwen3-vl:2b",
        "messages": [{"role": "user", "content": "What color is this image?", "images": [img]}],
        "stream": False,
        "options": {"temperature": 0.1}
    }
    print("Sending request to Ollama /api/chat...")
    try:
        resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=60)
        print("Status Code:", resp.status_code)
        if resp.status_code != 200:
            print("Response:", resp.text)
            return
            
        data = resp.json()
        print("Result:", data.get("message", {}).get("content"))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
