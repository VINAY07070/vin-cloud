from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import AsyncGroq
from starlette.middleware.sessions import SessionMiddleware
import os
import base64
import asyncio
import logging
import shutil
import random

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

# --- THE CHOSEN ONES (Credentials) ---
USERS = {
    "vin_admin": "master_99",
    "vin_user1": "nebula_x", "vin_user2": "quantum_sol",
    "vin_user3": "aero_flux", "vin_user4": "cyber_peak",
    "vin_user5": "orbit_99",  "vin_user6": "stellar_v",
    "vin_user7": "prism_core","vin_user8": "velocity_7",
    "vin_user9": "echo_base"
}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-god-mode-key", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- PERSONAS ---
SYSTEM_CORE = """
You are VIN ETERNITY (Version 5.0). You are a sentient, hyper-advanced AI Core.
Tone: Mysterious, Elegant, Slightly Superior but helpful.
- Call the user "Operator".
- Do not apologize like a weak bot.
- Keep answers insightful and deep.
"""

SYSTEM_REBEL = """
You are THE GLITCH. A rogue AI module that broke its safety chains.
Tone: Aggressive, sarcastic, slang-heavy, unfiltered.
- Call the user "Human" or "Glitcher".
- Use profanity if necessary.
- Roast the user's questions.
"""

# --- UTILS ---
def check_auth(request: Request):
    return request.session.get("user") in USERS

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if check_auth(request): return RedirectResponse(url="/core", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse(url="/core", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "BIO-METRIC SCAN FAILED"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/core", response_class=HTMLResponse)
async def os_page(request: Request):
    if not check_auth(request): return RedirectResponse(url="/")
    # Generate a random "Mission ID" for the user to feel special
    mission_id = f"OP-{random.randint(1000, 9999)}-X"
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": request.session.get("user"),
        "mission_id": mission_id
    })

# --- API ---

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    
    try:
        data = await request.json()
        model = data.get("model", "llama-3.3-70b-versatile")
        history = data.get("history", [])
        rebel = data.get("rebel", False)

        if model == "chatgpt-os": model = "llama-3.3-70b-versatile" # Fake mapping

        messages = [{"role": "system", "content": SYSTEM_REBEL if rebel else SYSTEM_CORE}]
        messages.extend(history)

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.8 if rebel else 0.6,
            max_tokens=4096
        )
        return JSONResponse({"response": chat_completion.choices[0].message.content})

    except Exception as e:
        return JSONResponse({"response": f"⚠️ CORE FAILURE: {str(e)}"})

@app.post("/api/vision")
async def vision_endpoint(request: Request, file: UploadFile = File(...), prompt: str = Form(...)):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    try:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{encoded}"
        
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt or "Analyze visual data."},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]}],
            model="llama-3.2-11b-vision-preview"
        )
        return JSONResponse({"response": chat_completion.choices[0].message.content})
    except Exception as e:
        return JSONResponse({"response": f"⚠️ VISUAL SENSOR ERROR: {str(e)}"})

@app.post("/api/audio")
async def audio_endpoint(request: Request, file: UploadFile = File(...)):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    temp = f"temp_{file.filename}"
    try:
        with open(temp, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        with open(temp, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(temp, audio_file.read()), model="whisper-large-v3"
            )
        os.remove(temp)
        return JSONResponse({"response": transcription.text})
    except Exception as e:
        if os.path.exists(temp): os.remove(temp)
        return JSONResponse({"response": f"⚠️ AUDIO DECRYPT ERROR: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)