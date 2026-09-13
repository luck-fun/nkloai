import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
 
# Автоматически загружает переменные из файла .env
load_dotenv()
 
app = FastAPI(title="RouterAI Web Interface")
 
app.mount("/static", StaticFiles(directory="static"), name="static")
 
ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")
if not ROUTERAI_API_KEY:
    raise ValueError("Не задан ROUTERAI_API_KEY. Проверьте наличие файла .env")
 
# Модель можно менять через .env, не трогая код.
# Для картинок нужна vision-модель, например:
#   deepseek/deepseek-v4-flash-vision-exp
#   qwen/qwen3-vl-30b-a3b-instruct
ROUTERAI_MODEL = os.getenv("ROUTERAI_MODEL", "deepseek/deepseek-v4-flash-vision-exp")
 
ROUTERAI_URL = "https://routerai.ru/api/v1/chat/completions"
 
 
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
 
        # Собираем content в формате OpenAI-совместимого API.
        # Если картинки нет — можно отправить content как обычную строку,
        # но при её наличии content должен быть массивом блоков.
        content = [{"type": "text", "text": prompt}]
 
        if image and image.filename:
            image_bytes = await image.read()
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
 
            # Определяем mime-type по расширению файла (простая эвристика)
            mime_type = image.content_type or "image/png"
 
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_image}"
                }
            })
 
        payload = {
            "model": ROUTERAI_MODEL,
            "messages": [
                {"role": "user", "content": content}
            ]
        }
 
        headers = {
            "Authorization": f"Bearer {ROUTERAI_API_KEY}",
            "Content-Type": "application/json"
        }
 
        resp = requests.post(ROUTERAI_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
 
        answer = result["choices"][0]["message"]["content"]
        return {"response": answer}
 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка обращения к RouterAI: {e}")
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Неожиданный формат ответа RouterAI: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))