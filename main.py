"""
VinGPT Ultimate Backend
Architect: Vinay
Version: 5.0 (Autonomous Agent)
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from groq import AsyncGroq
from duckduckgo_search import DDGS
import os
import logging
import asyncio
import json
import urllib.parse

# --- 1. SYSTEM CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VinGPT")

API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

# Secure User Database
USERS = {
    "admin": "admin123",
    "vinay": "vinay_pro",
    "guest": "guest_access"
}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-ultimate-key-v5", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- 2. TOOL: WEB SEARCH ---
def search_web(query: str, max_results=3):
    """Performs a live internet search securely."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No internet results found."
        
        # Format results for the AI to read
        summary = "INTERNET SEARCH RESULTS:\n"
        for r in results:
            summary += f"- {r['title']}: {r['body']} (Source: {r['href']})\n"
        return summary
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return "Search unavailable."

# --- 3. TOOL: IMAGE GENERATION ---
def generate_image_url(prompt: str):
    """Generates a high-quality image URL via Pollinations AI."""
    # Clean prompt for URL
    safe_prompt = urllib.parse.quote(prompt)
    # Return the direct image link
    return f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&private=true&enhance=true"

# --- 4. INTELLIGENCE ROUTER ---
async def process_request(user_prompt: str, history: list, model: str, sys_prompt: str):
    """
    Decides whether to Chat, Search, or Draw.
    """
    prompt_lower = user_prompt.lower()

    # --- MODE A: IMAGE GENERATION ---
    # Trigger words: /image, draw, paint, generate image
    if any(x in prompt_lower for x in ["/image", "generate an image", "create an image", "draw a", "paint a"]):
        # Extract the visual description
        image_prompt = user_prompt.replace("/image", "").replace("generate an image of", "").strip()
        image_url = generate_image_url(image_prompt)
        return {
            "type": "image", 
            "content": image_url, 
            "alt": f"Generated: {image_prompt}"
        }

    # --- MODE B: WEB SEARCH ---
    # Trigger words: price, news, current, today, latest, who won, weather
    search_triggers = ["price", "news", "current", "today", "latest", "who won", "weather", "stock", "live"]
    if any(x in prompt_lower for x in search_triggers):
        logger.info(f"Triggering Web Search for: {user_prompt}")
        search_data = search_web(user_prompt)
        
        # Feed search results into Groq
        system_context = f"{sys_prompt}\n\nCONTEXT FROM WEB:\n{search_data}\n\nINSTRUCTION: Answer the user's question using the web context above. Cite sources if possible."
        
        messages = [{"role": "system", "content": system_context}]
        messages.extend(history)
        
        completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.6,
            max_tokens=4096
        )
        return {"type": "text", "content": completion.choices[0].message.content}

    # --- MODE C: STANDARD CHAT ---
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend(history)
    
    completion = await client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=4096
    )
    return {"type": "text", "content": completion.choices[0].message.content}

# --- 5. ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user") in USERS: 
        return RedirectResponse(url="/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse(url="/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Access Denied"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_page(request: Request):
    if request.session.get("user") not in USERS: return RedirectResponse(url="/")
    return templates.TemplateResponse("index.html", {"request": request, "user": request.session.get("user")})

@app.post("/api/generate")
async def generate(request: Request):
    if request.session.get("user") not in USERS: return JSONResponse({"error": "Unauthorized"}, 401)
    
    try:
        data = await request.json()
        response_data = await process_request(
            user_prompt=data.get("message"),
            history=data.get("history", []),
            model=data.get("model", "llama-3.3-70b-versatile"),
            sys_prompt=data.get("system", "You are VinGPT, a helpful AI.")
        )
        return JSONResponse(response_data)
    except Exception as e:
        return JSONResponse({"type": "error", "content": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)