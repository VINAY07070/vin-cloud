from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import AsyncGroq  # <--- CHANGED TO ASYNC CLIENT
from starlette.middleware.sessions import SessionMiddleware
import os
import base64
import asyncio
import logging

# --- LOGGING SETUP (So we can see errors in Render Console) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
API_KEY = os.getenv("GROQ_API_KEY")
# If no key is found, print a warning
if not API_KEY:
    logger.warning("⚠️ NO GROQ API KEY FOUND! SET IT IN RENDER DASHBOARD.")

# Initialize Async Client
client = AsyncGroq(api_key=API_KEY)

# --- SECURE USER DATABASE ---
# Format: "username": "password"
USERS = {
    "vin_admin": "master_key_99",
    "vin_user1": "nebula_x",
    "vin_user2": "quantum_sol",
    "vin_user3": "aero_flux",
    "vin_user4": "cyber_peak",
    "vin_user5": "orbit_99",
    "vin_user6": "stellar_v",
    "vin_user7": "prism_core",
    "vin_user8": "velocity_7",
    "vin_user9": "echo_base"
}

app = FastAPI()
# Secure Cookies
app.add_middleware(SessionMiddleware, secret_key="vin-cloud-super-secret-v3", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- UTILS ---
def check_auth(request: Request):
    """Checks if user is logged in AND valid."""
    user = request.session.get("user")
    if user and user in USERS:
        return True
    return False

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # If user is already valid, send to OS
    if check_auth(request): 
        return RedirectResponse(url="/os", status_code=303)
    
    # If session exists but invalid (old code), clear it
    if request.session.get("user"):
        request.session.clear()
        
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Clean inputs (Remove accidental spaces from copy-paste)
    user_clean = username.strip()
    pass_clean = password.strip()

    if user_clean in USERS and USERS[user_clean] == pass_clean:
        request.session["user"] = user_clean
        return RedirectResponse(url="/os", status_code=303)
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid Identity or Passkey"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_page(request: Request):
    if not check_auth(request): return RedirectResponse(url="/")
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user")})

# --- AI ENDPOINTS (ASYNC & ROBUST) ---

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    
    try:
        data = await request.json()
        model = data.get("model", "llama-3.3-70b-versatile")
        history = data.get("history", [])

        # System Instruction
        messages = [{"role": "system", "content": "You are VIN OS. An advanced AI System created by VINAY. Be precise, helpful, and professional."}]
        messages.extend(history)

        # ASYNC CALL (Does not freeze server)
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.6,
            max_tokens=4096
        )
        return JSONResponse({"response": chat_completion.choices[0].message.content})

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        return JSONResponse({"response": f"⚠️ Neural Core Error: {str(e)}"})

@app.post("/api/vision")
async def vision_endpoint(request: Request, file: UploadFile = File(...), prompt: str = Form(...)):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)

    try:
        # Read file
        contents = await file.read()
        encoded_image = base64.b64encode(contents).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{encoded_image}"

        # Vision Model Call
        chat_completion = await client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            model="llama-3.2-11b-vision-preview"
        )
        return JSONResponse({"response": chat_completion.choices[0].message.content})

    except Exception as e:
        logger.error(f"Vision Error: {e}")
        return JSONResponse({"response": f"⚠️ Visual Sensor Error: {str(e)}"})

@app.post("/api/audio")
async def audio_endpoint(request: Request, file: UploadFile = File(...)):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)

    temp_filename = f"temp_{file.filename}"
    try:
        # Save temp file
        with open(temp_filename, "wb") as f:
            f.write(await file.read())
        
        # Whisper Call
        with open(temp_filename, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(temp_filename, audio_file.read()),
                model="whisper-large-v3"
            )
        
        os.remove(temp_filename)
        return JSONResponse({"response": transcription.text})

    except Exception as e:
        if os.path.exists(temp_filename): os.remove(temp_filename)
        logger.error(f"Audio Error: {e}")
        return JSONResponse({"response": f"⚠️ Audio Processor Error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)