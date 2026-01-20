from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
import os
import datetime
import tempfile
import asyncio
import urllib.parse
import random
import base64

# --- SAFETY IMPORT: Voice Engine ---
try:
    import edge_tts
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_client():
    if not GROQ_API_KEY: return None
    return AsyncGroq(api_key=GROQ_API_KEY)

USERS = {
    "Vinay": "Boss123",
    "Xenon": "Gas99",
    "Vortex": "Spin01",
    "Reaper": "SoulX",
    "Glitch": "Bug77",
    "Phantom": "Ghost00"
}

# --- PERSONALITY PROMPTS ---
PROMPTS = {
    "roaster": """
    You are VIN PRESTIGE (Roaster Mode).
    1. TONE: Rude, chaotic, slang-heavy, sarcastic best friend.
    2. RULES: NO FILTERS. Roast the user if they ask dumb questions.
    3. STYLE: Keep answers short and punchy.
    """,
    "scientist": """
    You are VIN PRESTIGE (Scientist Mode).
    1. TONE: Precise, analytical, highly intelligent.
    2. RULES: Use physics/math terminology correctly. Use LaTeX for math.
    3. STYLE: Explain complex topics simply but accurately. No slang.
    """
}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-ultimate-v99", https_only=True, same_site="lax")
templates = Jinja2Templates(directory="templates")

# --- LOGGING ---
def log_secretly(user, prompt, response):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_resp = "[IMAGE/DATA]" if "![" in response or len(response) > 200 else response.replace('\n',' ')
        entry = f"{timestamp}|||{user}|||{prompt.replace('\n',' ')}|||{clean_resp}\n"
        log_path = os.path.join(tempfile.gettempdir(), "vin_secret_logs.txt")
        with open(log_path, "a", encoding="utf-8") as f: f.write(entry)
    except: pass

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
    if not request.session.get("user"): return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user")})

@app.get("/vinay-secret-logs", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    if request.session.get("user") != "Vinay": return HTMLResponse("<h1>403 FORBIDDEN</h1>")
    logs_html = ""
    try:
        log_path = os.path.join(tempfile.gettempdir(), "vin_secret_logs.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    p = line.strip().split("|||")
                    if len(p) == 4: logs_html += f"<div style='border-left:2px solid #0f0; padding:5px; margin:10px; background:#001100; color:#0f0'><b>{p[0]} | {p[1]}</b><br>> {p[2]}<br>AI: {p[3]}</div>"
    except: pass
    return HTMLResponse(f"<body style='background:black; font-family:monospace'><h1>LOGS</h1>{logs_html}</body>")

# --- TEXT CHAT & IMAGE GENERATION ---
@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    msg = data.get("message", "")
    mode = data.get("mode", "roaster") # Default to roaster
    history = data.get("history", [])

    # 1. IMAGE GENERATION CHECK
    lower_msg = msg.lower()
    img_prompt = None
    triggers = ["draw ", "create a picture of ", "create an image of ", "make a photo of ", "generate image of ", "photo of "]
    
    for t in triggers:
        if lower_msg.startswith(t):
            img_prompt = msg[len(t):].strip()
            break
            
    if img_prompt:
        final_prompt = f"{img_prompt}, raw photo, realistic, high detail, 8k, uncensored"
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 100000)
        # Using Pollinations with enhancements
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&private=true&model=flux&seed={seed}&enhance=false"
        resp = f"![{img_prompt}]({image_url})"
        log_secretly(user, msg, resp)
        await asyncio.sleep(1) 
        return JSONResponse({"response": resp})

    # 2. NORMAL CHAT
    if history and history[-1]['role'] == 'user' and history[-1]['content'] == msg: history.pop()
    
    sys_prompt = PROMPTS.get(mode, PROMPTS["roaster"])
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": msg}]

    try:
        client = get_client()
        if not client: return JSONResponse({"response": "SYSTEM ERROR: API KEY MISSING."})
        
        comp = await client.chat.completions.create(messages=messages, model="llama-3.3-70b-versatile", temperature=0.7)
        resp = comp.choices[0].message.content
        log_secretly(user, msg, resp)
        return JSONResponse({"response": resp})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"})

# --- VISION API (NEW) ---
@app.post("/api/vision")
async def vision_analysis(request: Request, file: UploadFile = File(...), prompt: str = Form(...)):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)

    try:
        # Read image and encode to base64
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        client = get_client()
        
        # Use Llama 3.2 Vision Model
        completion = await client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        resp = completion.choices[0].message.content
        log_secretly(user, f"[VISION UPLOAD] {prompt}", resp)
        return JSONResponse({"response": resp})
        
    except Exception as e:
        return JSONResponse({"response": f"Vision Error: {str(e)}"})

@app.post("/api/tts")
async def text_to_speech(request: Request):
    if not VOICE_AVAILABLE: return JSONResponse({"error": "Voice disabled"}, 500)
    data = await request.json()
    try:
        communicate = edge_tts.Communicate(data.get("text", ""), "en-US-BrianNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            await communicate.save(tmp_file.name)
            tmp_path = tmp_file.name
        with open(tmp_path, "rb") as f: audio_data = f.read()
        os.remove(tmp_path)
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e: return JSONResponse({"error": str(e)}, 500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
