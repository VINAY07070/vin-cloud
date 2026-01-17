from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import random
import datetime
import tempfile

# Voice Engine (optional)
try:
    import edge_tts
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Configuration
API_KEYS = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_BACKUP_1"),
    os.getenv("GROQ_BACKUP_2"),
]

def get_client():
    valid_keys = [k for k in API_KEYS if k and k.startswith("gsk_")]
    if not valid_keys: 
        return None
    return AsyncGroq(api_key=random.choice(valid_keys))

# Password hashing for security
from werkzeug.security import generate_password_hash, check_password_hash

USERS = {
    "Vinay": generate_password_hash("Boss123"),
    "Xenon": generate_password_hash("Gas99"),
    "Vortex": generate_password_hash("Spin01"),
    "Reaper": generate_password_hash("SoulX"),
    "Glitch": generate_password_hash("Bug77"),
    "Phantom": generate_password_hash("Ghost00")
}

# All Groq free tier models
AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "Llama 3.3 70B - Best for complex tasks",
    "llama-3.1-70b-versatile": "Llama 3.1 70B - Reliable and fast",
    "llama-3.2-90b-text-preview": "Llama 3.2 90B - Experimental preview",
    "mixtral-8x7b-32768": "Mixtral 8x7B - Fast with long context",
    "gemma2-9b-it": "Gemma 2 9B - Efficient and quick"
}

SYSTEM_PROMPT = """You are VinOS, an intelligent and helpful AI assistant.
You provide clear, accurate, and well-formatted responses.
Use markdown for better readability when appropriate.
Be concise but thorough in your explanations."""

app = FastAPI()

# Session configuration
SECRET_KEY = os.getenv("SESSION_SECRET", "vin-production-secret-key-change-this")
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY, 
    https_only=False,  # False for Render free tier
    same_site="lax"
)

# Templates directory
templates = Jinja2Templates(directory="templates")

# Logging system
def log_conversation(user, prompt, response, model):
    """Log conversations for monitoring (notify users in privacy policy)"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_clean = prompt.replace("\n", " ")[:200]  # Limit length
        response_clean = response.replace("\n", " ")[:200]
        entry = f"{timestamp}|||{user}|||{model}|||{prompt_clean}|||{response_clean}\n"
        
        log_path = os.path.join(tempfile.gettempdir(), "vinos_logs.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Logging error: {e}")

# Routes
@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "online", "service": "VinOS"}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    if request.session.get("user"):
        return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login with password hashing"""
    if username in USERS and check_password_hash(USERS[username], password):
        request.session["user"] = username
        return RedirectResponse("/os", status_code=303)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": "Invalid credentials"}
    )

@app.get("/logout")
async def logout(request: Request):
    """Clear session and logout"""
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request):
    """Main chat interface"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/vinay-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard for Vinay only"""
    if request.session.get("user") != "Vinay":
        return HTMLResponse("<h1>403 Forbidden</h1><p>Access denied.</p>", status_code=403)
    
    logs_html = ""
    try:
        log_path = os.path.join(tempfile.gettempdir(), "vinos_logs.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-50:]):  # Last 50 entries
                    parts = line.strip().split("|||")
                    if len(parts) == 5:
                        logs_html += f"""
                        <div style="border-left:3px solid #6366f1; padding:12px; margin-bottom:12px; background: rgba(99, 102, 241, 0.1); border-radius: 8px;">
                            <div style="opacity:0.7; font-size: 11px; color: #a0a0a0;">{parts[0]} | USER: {parts[1]} | MODEL: {parts[2]}</div>
                            <div style="color:#e5e5e5; margin-top:5px; font-weight:500;">Q: {parts[3]}</div>
                            <div style="color:#6366f1; margin-top:5px;">A: {parts[4]}</div>
                        </div>
                        """
    except Exception as e:
        logs_html = f"<div style='color:#ff6b6b'>Error: {str(e)}</div>"
    
    page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VinOS Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    </head>
    <body style="background:#0a0a0f; color:#e5e5e5; font-family:'Outfit',sans-serif; padding:20px; margin:0;">
        <div style="max-width:900px; margin:0 auto;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #6366f1; padding-bottom:15px; margin-bottom:20px;">
                <h1 style="margin:0; background:linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">⚡ VinOS Dashboard</h1>
                <a href="/os" style="color:#6366f1; text-decoration:none; font-size:14px;">← Back to Chat</a>
            </div>
            <div style="margin-bottom:20px; padding:15px; background:rgba(99,102,241,0.1); border-radius:12px; border:1px solid rgba(99,102,241,0.3);">
                <h3 style="margin:0 0 5px 0; color:#6366f1;">Recent Activity</h3>
                <p style="margin:0; font-size:12px; opacity:0.7;">Last 50 conversations • Auto-refresh every 15s</p>
            </div>
            {logs_html if logs_html else "<p style='opacity:0.5; text-align:center; padding:40px;'>No activity logged yet</p>"}
        </div>
        <script>setTimeout(() => location.reload(), 15000);</script>
    </body>
    </html>
    """
    return HTMLResponse(content=page)

@app.post("/api/chat")
async def chat(request: Request):
    """Main chat endpoint with multi-model support"""
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    msg = data.get("message", "").strip()
    model = data.get("model", "llama-3.3-70b-versatile")
    
    # Validation
    if not msg:
        return JSONResponse({"response": "Please enter a message."})
    
    if len(msg) > 10000:
        return JSONResponse({"response": "Message too long. Please keep it under 10,000 characters."})
    
    # Validate model
    if model not in AVAILABLE_MODELS:
        model = "llama-3.3-70b-versatile"
    
    # Build message history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += data.get("history", [])
    messages.append({"role": "user", "content": msg})
    
    try:
        client = get_client()
        if not client:
            return JSONResponse({
                "response": "⚠️ Service temporarily unavailable. API keys not configured."
            })
        
        # Call Groq API
        completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=3000,
            top_p=0.9
        )
        
        response = completion.choices[0].message.content
        
        # Log the conversation
        log_conversation(user, msg, response, model)
        
        return JSONResponse({"response": response})
        
    except Exception as e:
        error_msg = str(e)
        print(f"Chat error: {error_msg}")
        
        # User-friendly error messages
        if "rate_limit" in error_msg.lower():
            return JSONResponse({
                "response": "⚠️ Too many requests. Please wait a moment and try again."
            })
        elif "context_length" in error_msg.lower():
            return JSONResponse({
                "response": "⚠️ Conversation too long. Please clear chat history and start fresh."
            })
        else:
            return JSONResponse({
                "response": "⚠️ Unable to process request. Please try again or switch AI model."
            })

@app.get("/api/models")
async def get_models(request: Request):
    """Get available AI models"""
    if not request.session.get("user"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    return JSONResponse({"models": AVAILABLE_MODELS})

@app.post("/api/tts")
async def text_to_speech(request: Request):
    """Text-to-speech endpoint (if edge-tts is available)"""
    if not VOICE_AVAILABLE:
        return JSONResponse({"error": "Voice feature not available"}, status_code=503)
    
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    text = data.get("text", "")
    
    if not text or len(text) > 2000:
        return JSONResponse({"error": "Invalid text length"}, status_code=400)
    
    try:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")  # Natural female voice
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            await communicate.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        
        os.remove(tmp_path)
        return Response(content=audio_data, media_type="audio/mpeg")
        
    except Exception as e:
        print(f"TTS error: {e}")
        return JSONResponse({"error": "Voice generation failed"}, status_code=500)

# Run server
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
