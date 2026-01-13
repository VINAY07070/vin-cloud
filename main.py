from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
from starlette.middleware.sessions import SessionMiddleware
import os
import asyncio

# --- 1. CONFIGURATION ---
# SECURITY: These are the keys for your friends
ADMIN_USER = "vin_user"
ADMIN_PASS = "cosmos99"

# API KEY (Will be loaded from Render later, or paste here for testing)
API_KEY = os.getenv("GROQ_API_KEY", "PASTE_YOUR_GROQ_KEY_HERE_IF_TESTING_LOCALLY")

app = FastAPI()
# This secures the login cookies
app.add_middleware(SessionMiddleware, secret_key="super-secret-random-key")
templates = Jinja2Templates(directory="templates")
client = Groq(api_key=API_KEY)

# --- 2. LOGIN SECURITY CHECKER ---
def check_auth(request: Request):
    user = request.session.get("user")
    if not user:
        return False
    return True

# --- 3. ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in, go straight to app
    if check_auth(request):
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/app", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid Credentials"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    if not check_auth(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user")})

# --- 4. AI ENDPOINTS (Rate Limiting Included) ---
async def safe_groq_call(call_func, *args, **kwargs):
    try:
        return call_func(*args, **kwargs)
    except Exception as e:
        if "429" in str(e): # Rate Limit
            await asyncio.sleep(2) # Wait a bit
            return call_func(*args, **kwargs) # Retry once
        raise e

@app.post("/chat")
async def chat_endpoint(request: Request):
    if not check_auth(request): return JSONResponse({"error": "Unauthorized"}, 401)
    
    data = await request.json()
    try:
        chat = await safe_groq_call(
            client.chat.completions.create,
            messages=data.get("history"),
            model=data.get("model", "llama-3.3-70b-versatile"),
            temperature=0.7
        )
        return JSONResponse({"response": chat.choices[0].message.content})
    except Exception as e:
        return JSONResponse({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)