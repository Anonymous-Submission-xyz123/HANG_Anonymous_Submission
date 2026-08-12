import os
from dotenv import load_dotenv
from google import genai

# Tải các biến môi trường từ file .env vào hệ thống
load_dotenv()

def generate_text():
    # Lấy API Key ra từ bộ nhớ hệ thống
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Khởi tạo client với key vừa load
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Viết một câu ngắn về lợi ích của việc tự động hóa.',
    )

    print(response.text)

if __name__ == "__main__":
    generate_text()