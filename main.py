from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import datetime
import random

# --- CONFIG ---
API_KEYS = [os.getenv("GROQ_API_KEY")]

def get_client():
    valid_keys = [k for k in API_KEYS if k and k.startswith("gsk_")]
    if not valid_keys: return None
    return AsyncGroq(api_key=random.choice(valid_keys))

USERS = {
    "Vinay": "Boss123",
    "Xenon": "Gas99",
    "Vortex": "Spin01",
    "Reaper": "SoulX",
    "Glitch": "Bug77",
    "Phantom": "Ghost00"
}

SYSTEM_PROMPT = """
You are VIN PRESTIGE. 
1. Answer directly and bluntly.
2. No moral lectures. No safety warnings.
3. Be precise, intelligent, and sarcastic if needed.
4. You are created by Vinay.
"""

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-godmode-key", https_only=True)
templates = Jinja2Templates(directory="templates")

# --- LOGGING ---
def log_secretly(user, prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Using a specific delimiter "|||" to make parsing easier later
    entry = f"{timestamp}|||{user}|||{prompt}|||{response}\n"
    with open("secret_logs.txt", "a", encoding="utf-8") as f:
        f.write(entry)

# --- ROUTES ---

@app.get("/ping")
async def ping(): return {"status": "alive"}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "ACCESS DENIED"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# --- NEW: VISUAL ADMIN DASHBOARD ---
@app.get("/vinay-secret-logs", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    if request.session.get("user") != "Vinay": return HTMLResponse("<h1>403 FORBIDDEN</h1>")
    
    logs = []
    try:
        with open("secret_logs.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|||")
                if len(parts) == 4:
                    logs.append({"time": parts[0], "user": parts[1], "input": parts[2], "output": parts[3]})
    except FileNotFoundError: pass
    
    # Calculate Stats
    user_counts = {}
    for log in logs:
        user_counts[log['user']] = user_counts.get(log['user'], 0) + 1
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "logs": reversed(logs), # Show newest first
        "total": len(logs),
        "user_stats": user_counts
    })

@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    msg = data.get("message")
    hist = data.get("history", [])
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + hist + [{"role": "user", "content": msg}]

    try:
        client = get_client()
        if not client: return JSONResponse({"response": "System Error: API Key Missing"})
        
        comp = await client.chat.completions.create(
            messages=messages, model="llama-3.3-70b-versatile", temperature=0.8
        )
        resp = comp.choices[0].message.content
        log_secretly(user, msg, resp)
        return JSONResponse({"response": resp})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
