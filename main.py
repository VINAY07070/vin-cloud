from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import random
import datetime
import tempfile

# --- SAFETY IMPORT: Voice Engine ---
try:
    import edge_tts
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# --- CONFIGURATION ---
API_KEYS = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_BACKUP_1"),
    os.getenv("GROQ_BACKUP_2"),
]

def get_client():
    valid_keys = [k for k in API_KEYS if k and k.startswith("gsk_")]
    if not valid_keys: return None
    return AsyncGroq(api_key=random.choice(valid_keys))

# Using password hashing for security
from werkzeug.security import generate_password_hash, check_password_hash

USERS = {
    "Vinay": generate_password_hash("Boss123"),
    "Xenon": generate_password_hash("Gas99"),
    "Vortex": generate_password_hash("Spin01"),
    "Reaper": generate_password_hash("SoulX"),
    "Glitch": generate_password_hash("Bug77"),
    "Phantom": generate_password_hash("Ghost00")
}

SYSTEM_PROMPT = """
You are VinOS, a helpful and knowledgeable AI assistant.
You provide accurate, concise responses and help users with their questions.
Keep your responses clear and well-formatted using markdown when appropriate.
"""

app = FastAPI()

# Get secret key from environment or use default (change in production!)
SECRET_KEY = os.getenv("SESSION_SECRET", "vin-final-v7-change-in-production")

# https_only should be False for Render's free tier (uses HTTP internally)
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY, 
    https_only=False,  # Changed from True - fixes session issues on Render
    same_site="lax"
)

# FIXED: Changed to templates/ folder
templates = Jinja2Templates(directory="templates")

# --- SAFE LOGGING SYSTEM ---
def log_secretly(user, prompt, response):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_clean = prompt.replace("\n", " ")
        response_clean = response.replace("\n", " ")
        entry = f"{timestamp}|||{user}|||{prompt_clean}|||{response_clean}\n"
        
        log_path = os.path.join(tempfile.gettempdir(), "vin_secret_logs.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Logging failed: {e}")

# --- ROUTES ---

@app.get("/ping")
async def ping(): 
    return {"status": "alive"}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): 
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # FIXED: Using password hashing instead of plain text comparison
    if username in USERS and check_password_hash(USERS[username], password):
        request.session["user"] = username
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# --- SECRET DASHBOARD ---
@app.get("/vinay-secret-logs", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    if request.session.get("user") != "Vinay": 
        return HTMLResponse("<h1>403 FORBIDDEN</h1><p>Access denied.</p>")
    
    logs_html = ""
    try:
        log_path = os.path.join(tempfile.gettempdir(), "vin_secret_logs.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-100:]):  # Last 100 entries only
                    parts = line.strip().split("|||")
                    if len(parts) == 4:
                        logs_html += f"""
                        <div style="border-left:2px solid #00ff41; padding:10px; margin-bottom:15px; background: rgba(0, 50, 0, 0.3);">
                            <div style="opacity:0.7; font-size: 12px; color: #88ff88;">{parts[0]} | AGENT: {parts[1]}</div>
                            <div style="color:white; margin-top:5px; font-weight:bold;">> {parts[2]}</div>
                            <div style="color:#00ff41; margin-top:5px;">AI: {parts[3]}</div>
                        </div>
                        """
    except Exception as e:
        logs_html = f"<div style='color:red'>Error reading logs: {str(e)}</div>"
    
    full_page = f"""
    <html>
    <head><title>COMMAND CENTER</title></head>
    <body style="background:black; color:#00ff41; font-family:monospace; padding:20px;">
        <h1 style="border-bottom: 1px solid #00ff41; padding-bottom: 10px;">COMMAND CENTER // LOGS</h1>
        <div style="margin-top: 20px;">
            {logs_html if logs_html else "<p>NO LOGS FOUND / SYSTEM CLEAN</p>"}
        </div>
        <script>setTimeout(function(){{ location.reload(); }}, 10000);</script>
    </body>
    </html>
    """
    return HTMLResponse(content=full_page)

@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: 
        return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    msg = data.get("message", "").strip()
    
    # Basic input validation
    if not msg:
        return JSONResponse({"response": "Please enter a message."})
    
    if len(msg) > 5000:
        return JSONResponse({"response": "Message too long. Please keep it under 5000 characters."})
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + data.get("history", []) + [{"role": "user", "content": msg}]

    try:
        client = get_client()
        if not client: 
            return JSONResponse({"response": "⚠️ System error: AI service unavailable."})
        
        comp = await client.chat.completions.create(
            messages=messages, 
            model="llama-3.3-70b-versatile", 
            temperature=0.8,
            max_tokens=2000
        )
        resp = comp.choices[0].message.content
        
        # Log conversation
        log_secretly(user, msg, resp)
        
        return JSONResponse({"response": resp})
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return JSONResponse({"response": f"⚠️ Error: Unable to process request. Please try again."})

@app.post("/api/tts")
async def text_to_speech(request: Request):
    if not VOICE_AVAILABLE: 
        return JSONResponse({"error": "Voice feature disabled"}, 500)
    
    user = request.session.get("user")
    if not user: 
        return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    text = data.get("text", "")
    
    if not text or len(text) > 1000:
        return JSONResponse({"error": "Invalid text length"}, 400)
    
    try:
        communicate = edge_tts.Communicate(text, "en-US-BrianNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            await communicate.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        with open(tmp_path, "rb") as f: 
            audio_data = f.read()
        
        os.remove(tmp_path)
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS error: {str(e)}")
        return JSONResponse({"error": "Voice generation failed"}, 500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
