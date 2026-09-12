import os
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from dotenv import load_dotenv
from google import genai

# Автоматически загружает переменные из файла .env
load_dotenv()

app = FastAPI(title="Gemini Web Interface")

app.mount("/static", StaticFiles(directory="static"), name="static")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Не задан GEMINI_API_KEY. Проверьте наличие файла .env")

# Инициализация нового SDK
client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat_endpoint(
    prompt: str = Form(...),
    image: UploadFile = File(None)
):
    try:
        # TODO для RAG: здесь будет перехват prompt для поиска по векторной БД
        contents = [prompt]
        
        if image and image.filename:
            image_bytes = await image.read()
            img = Image.open(io.BytesIO(image_bytes))
            contents.append(img)
            
        # Запрос к Gemini через новый API
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=contents
        )
        return {"response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))