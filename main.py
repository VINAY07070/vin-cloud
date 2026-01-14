from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import AsyncGroq
from starlette.middleware.sessions import SessionMiddleware
import os
import logging
import asyncio

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

# --- 10 SECURE ACCOUNTS ---
USERS = {
    "admin": "admin123", # Simple for you to remember
    "vinay": "vinay_pro",
    "user1": "guest_01", "user2": "guest_02",
    "user3": "guest_03", "user4": "guest_04",
    "user5": "guest_05", "user6": "guest_06",
    "user7": "guest_07", "user8": "guest_08"
}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-gpt-pro-key", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- UTILS ---
def check_auth(request: Request):
    return request.session.get("user") in USERS

async def safe_chat_call(messages, model, temp):
    """Robust API call with retry logic"""
    retries = 3
    for attempt in range(retries):
        try:
            completion = await client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=float(temp),
                max_tokens=4096
            )
            return completion.choices[0].message.content
        except Exception as e:
            if attempt == retries - 1: raise e
            await asyncio.sleep(1) # Wait before retry

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if check_auth(request): return RedirectResponse(url="/chat", status_code=303)
    if request.session.get("user"): request.session.clear()
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = username.strip().lower() # Case insensitive username
    pwd = password.strip()
    
    if user in USERS and USERS[user] == pwd:
        request.session["user"] = user
        return RedirectResponse(url="/chat", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect credentials."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    if not check_auth(request): return RedirectResponse(url="/")
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user")})

@app.post("/api/generate")
async def generate(request: Request):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    
    try:
        data = await request.json()
        model = data.get("model", "llama-3.3-70b-versatile")
        history = data.get("history", [])
        system_prompt = data.get("system", "You are a helpful AI assistant.")
        temp = data.get("temperature", 0.7)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        response_text = await safe_chat_call(messages, model, temp)
        return JSONResponse({"response": response_text})

    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
