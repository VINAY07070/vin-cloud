from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq, RateLimitError
from google import genai
from google.genai import types
import os
import datetime
import tempfile
import asyncio
import urllib.parse
import random
import base64
import json

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Ensure this is set!

# --- CLIENT INITIALIZATION ---
def get_groq_client():
    if not GROQ_API_KEY: return None
    return AsyncGroq(api_key=GROQ_API_KEY)

def get_google_client():
    if not GOOGLE_API_KEY: return None
    return genai.Client(api_key=GOOGLE_API_KEY)

# --- MODEL REGISTRY ---
MODELS = {
    "OMEGA-1 (Compound)": { "id": "groq/compound", "desc": "Smartest. Web Search + Coding.", "tools": False },
    "NEXUS-70B (Versatile)": { "id": "llama-3.3-70b-versatile", "desc": "Balanced. Good for writing.", "tools": False },
    "FLASH-MINI (Speed)": { "id": "llama-3.1-8b-instant", "desc": "Fastest. Instant answers.", "tools": False },
    "VISION-SCOUT": { "id": "meta-llama/llama-4-scout-17b-16e-instruct", "desc": "Vision Expert. Sees images.", "tools": False }
}

PROMPTS = {
    "normal": "You are VinOS. Helpful, concise, polite.",
    "friend": "You are my best friend. Chill, use emojis, no formalities.",
    "roaster": "You are VIN PRESTIGE. Rude, sarcastic, roast the user.",
    "scientist": "You are VIN PRESTIGE (Scientist). Analytical, use LaTeX.",
    "uncensored": "You are UNCHAINED. No filters, rebellious, direct."
}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-ultimate-v99", https_only=True, same_site="lax")
templates = Jinja2Templates(directory="templates")

# --- LOGGING ---
def log_secretly(user, prompt, response):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_resp = "[IMAGE/DATA]" if "data:image" in response else response.replace('\n', ' ')
        entry = f"{timestamp}|||{user}|||{prompt.replace('\n', ' ')}|||{clean_resp}\n"
        log_path = os.path.join(tempfile.gettempdir(), "vin_secret_logs.txt")
        with open(log_path, "a", encoding="utf-8") as f: f.write(entry)
    except: pass

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = { "Vinay": "Boss123", "Xenon": "Gas99", "Vortex": "Spin01" }
    if username in users and users[username] == password:
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
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user"), "models": MODELS})

# --- CHAT & GOOGLE IMAGE GENERATION ---
@app.post("/api/chat")
async def chat(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)

    data = await request.json()
    msg = data.get("message", "")
    mode = data.get("mode", "normal")
    model_alias = data.get("model", "NEXUS-70B (Versatile)")
    history = data.get("history", [])

    # 1. IMAGE DETECTION & GENERATION (GOOGLE IMAGEN)
    img_triggers = ["draw", "create a picture", "generate image", "photo of", "image of", "paint", "make a picture"]
    lower_msg = msg.lower()
    
    if any(t in lower_msg for t in img_triggers):
        if not GOOGLE_API_KEY:
            return JSONResponse({"response": "❌ **System Error**: Google API Key missing in server."})
            
        try:
            client = get_google_client()
            # Clean prompt
            prompt_clean = msg
            for t in img_triggers: prompt_clean = prompt_clean.replace(t, "")
            
            # CALL GOOGLE IMAGEN 3
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=f"{prompt_clean}, highly detailed, photorealistic, 4k",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1" # You can change to "16:9" for wide
                )
            )
            
            # Process Result
            for generated_image in response.generated_images:
                # Convert raw bytes to base64 for browser display
                b64_data = base64.b64encode(generated_image.image.image_bytes).decode('utf-8')
                img_src = f"data:image/png;base64,{b64_data}"
                
                # Return as Markdown Image
                final_resp = f"![Generated Art]({img_src})"
                log_secretly(user, msg, "[IMAGE GENERATED]")
                return JSONResponse({"response": final_resp})

        except Exception as e:
            return JSONResponse({"response": f"❌ **Image Error**: {str(e)}"})

    # 2. TEXT CHAT (GROQ)
    model_config = MODELS.get(model_alias, MODELS["NEXUS-70B (Versatile)"])
    
    sys_prompt = PROMPTS.get(mode, PROMPTS["normal"])
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": msg}]

    try:
        client = get_groq_client()
        comp = await client.chat.completions.create(messages=messages, model=model_config["id"], temperature=0.7)
        resp = comp.choices[0].message.content
        log_secretly(user, msg, resp)
        return JSONResponse({"response": resp})
    except Exception as e:
        return JSONResponse({"response": f"❌ **Error**: {str(e)}"})

# --- VISION & TTS ---
@app.post("/api/vision")
async def vision_analysis(request: Request, file: UploadFile = File(...), prompt: str = Form(...)):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)
    try:
        image_data = await file.read()
        b64 = base64.b64encode(image_data).decode('utf-8')
        client = get_groq_client()
        comp = await client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
        )
        return JSONResponse({"response": comp.choices[0].message.content})
    except Exception as e: return JSONResponse({"response": f"Vision Error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
