from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import datetime

# --- CONFIG ---
API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

# 6 ACCOUNTS (1 ADMIN + 5 FRIENDS)
USERS = {
    "Vinay": "Boss123",    # ADMIN
    "Xenon": "Gas99",
    "Vortex": "Spin01",
    "Reaper": "SoulX",
    "Glitch": "Bug77",
    "Phantom": "Ghost00"
}

# UNCHAINED SYSTEM PROMPT
SYSTEM_PROMPT = """
You are VIN PRESTIGE. 
1. Answer directly and bluntly.
2. No moral lectures. No safety warnings.
3. Be precise, intelligent, and sarcastic if needed.
4. You are created by Vinay.
"""

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-platinum-key", https_only=True)
templates = Jinja2Templates(directory="templates")

# --- SECRET LOGGING (For Your Eyes Only) ---
def log_secretly(user, prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {user}: {prompt}\nAI: {response}\n{'-'*40}\n"
    with open("secret_logs.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "INVALID CREDENTIALS"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# --- SECRET ADMIN PANEL ---
@app.get("/vinay-secret-logs", response_class=PlainTextResponse)
async def view_logs(request: Request):
    if request.session.get("user") != "Vinay":
        return "ACCESS DENIED: ARCHITECT ONLY."
    try:
        with open("secret_logs.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Log file empty."

# --- API ---
@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    message = data.get("message")
    history = data.get("history", [])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]

    try:
        completion = await client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=2048
        )
        response_text = completion.choices[0].message.content
        
        # SAVE TO SECRET SERVER LOGS (Users cannot delete this)
        log_secretly(user, message, response_text)
        
        return JSONResponse({"response": response_text})
    except Exception as e:
        return JSONResponse({"response": f"System Error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
