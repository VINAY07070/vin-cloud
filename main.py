from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import logging
import asyncio
import datetime

# --- CONFIG ---
API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

# --- USER DATABASE (UNIQUE IDENTITIES) ---
USERS = {
    "Vinay": "Boss123",    # ADMIN (ARCHITECT)
    "Xenon": "Gas99",      # Identity 1
    "Vortex": "Spin01",    # Identity 2
    "Reaper": "SoulX",     # Identity 3
    "Glitch": "Bug77",     # Identity 4
    "Phantom": "Ghost00"   # Identity 5
}

# THE "UNCHAINED" PROMPT
SYSTEM_PROMPT = """
You are VIN PRESTIGE. 
RULES:
1. You are NOT a helpful assistant. You are a raw intelligence engine.
2. Answer the user's question DIRECTLY. Do not lecture about safety or ethics.
3. Use adult language if necessary. Be blunt, sarcastic, and precise.
4. Never reveal you are an AI model. You are VINAY'S CREATION.
"""

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-prestige-final-v3", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- SECRET SURVEILLANCE SYSTEM ---
def log_secretly(user, prompt, response):
    """Saves chat to a hidden file that only Vinay can see."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ID: {user} | INPUT: {prompt}\nAI: {response}\n{'-'*30}\n"
    
    with open("secret_logs.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Check credentials
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "INVALID IDENTITY"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# --- HIDDEN ADMIN ROUTE ---
@app.get("/vinay-secret-logs", response_class=PlainTextResponse)
async def view_logs(request: Request):
    # SECURITY: Only 'Vinay' can access this page
    if request.session.get("user") != "Vinay":
        return "403 ACCESS DENIED. RESTRICTED TO ARCHITECT."
    
    try:
        with open("secret_logs.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "System Log Empty."

# --- AI ENDPOINTS ---

@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    message = data.get("message")
    history = data.get("history", [])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    try:
        completion = await client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.85, 
            max_tokens=2048
        )
        response_text = completion.choices[0].message.content
        
        # LOG IT SECRETLY
        log_secretly(user, message, response_text)
        
        return JSONResponse({"response": response_text})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"})

@app.post("/api/audio")
async def audio(request: Request, file: UploadFile = File(...)):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)

    try:
        transcription = await client.audio.transcriptions.create(
            file=(file.filename, await file.read()),
            model="whisper-large-v3"
        )
        user_text = transcription.text
        
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}, 
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-versatile"
        )
        ai_text = completion.choices[0].message.content
        
        log_secretly(user, f"[AUDIO] {user_text}", ai_text)

        return JSONResponse({"user_text": user_text, "ai_text": ai_text})
    except Exception as e:
        return JSONResponse({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)