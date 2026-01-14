"""
VIN ETERNITY: ENTERPRISE EDITION
Architect: V.K. (Vinay)
Version: 10.0 (Final Polish)
"""

import os
import logging
import asyncio
import json
import urllib.parse
from datetime import datetime
from typing import List, Optional

# FASTAPI & CORE
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# AI & TOOLS
from groq import AsyncGroq
from duckduckgo_search import DDGS
from pypdf import PdfReader

# DATABASE
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

# --- 1. SYSTEM CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VIN_CORE")

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    logger.warning("CRITICAL: NO GROQ API KEY DETECTED")

client = AsyncGroq(api_key=API_KEY)

app = FastAPI(title="VinEternity", version="10.0")
app.add_middleware(SessionMiddleware, secret_key="vin-oppenheimer-key", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- 2. DATABASE SETUP (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./vin.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class ChatHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. INTELLIGENCE TOOLS ---

def search_web(query: str):
    """Secure Internet Access via DuckDuckGo"""
    try:
        results = DDGS().text(query, max_results=4)
        if not results: return None
        summary = "WEB INTEL:\n"
        for r in results:
            summary += f"- {r['title']}: {r['body']}\n"
        return summary
    except: return None

def generate_image(prompt: str):
    """Pollinations AI Neural Rendering"""
    safe_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&private=true&enhance=true&model=flux"

def extract_pdf(file_bytes):
    """Extracts text from PDF binary"""
    try:
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:10000] # Limit to 10k chars to save tokens
    except: return None

# --- 4. THE ROUTER (BRAIN) ---

async def process_autonomous_request(user_prompt: str, history: list, model: str, context: str = ""):
    """
    The Decision Engine. Decides to Search, Draw, or Chat.
    """
    prompt_lower = user_prompt.lower()
    
    # SYSTEM PROMPT
    base_system = (
        "You are VIN ETERNITY (v10.0), a hyper-intelligent AI Architected by V.K. (Vinay). "
        "You are professional, precise, and sophisticated. "
        "Never mention you are an AI model from Groq. You are proprietary VIN Technology."
    )

    # 1. IMAGE DETECTION
    if any(x in prompt_lower for x in ["draw", "generate image", "paint", "picture of", "create an image"]):
        img_prompt = user_prompt.replace("draw", "").replace("generate image", "").strip()
        url = generate_image(img_prompt)
        return {"type": "image", "content": url, "alt": img_prompt}

    # 2. WEB SEARCH DETECTION
    if any(x in prompt_lower for x in ["news", "price", "current", "today", "latest", "who won", "weather", "stock"]):
        web_data = search_web(user_prompt)
        if web_data:
            base_system += f"\n\n[LIVE WEB DATA]:\n{web_data}\n(Use this data to answer. Cite it naturally.)"

    # 3. CONTEXT INJECTION (PDFs)
    if context:
        base_system += f"\n\n[DOCUMENT CONTEXT]:\n{context}\n(Answer based on this document.)"

    # 4. CHAT GENERATION
    # Model Alias Mapping for "Premium Feel"
    real_model = "llama-3.3-70b-versatile"
    if model == "chatgpt-oss-120b": real_model = "llama-3.3-70b-versatile" # The Powerhouse
    if model == "vin-flash-8b": real_model = "llama-3.1-8b-instant"
    if model == "vin-creative-mix": real_model = "mixtral-8x7b-32768"

    messages = [{"role": "system", "content": base_system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        completion = await client.chat.completions.create(
            messages=messages,
            model=real_model,
            temperature=0.7,
            max_tokens=4096
        )
        return {"type": "text", "content": completion.choices[0].message.content}
    except Exception as e:
        return {"type": "error", "content": str(e)}

# --- 5. ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/auth/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Auto-create user if not exists (Simplified for UX)
    existing = db.query(User).filter(User.username == username).first()
    if not existing:
        new_user = User(username=username, hashed_password=pwd_context.hash(password))
        db.add(new_user)
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/auth/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "AUTHENTICATION FAILED"})
    
    request.session["user"] = username
    return RedirectResponse("/os", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/os", response_class=HTMLResponse)
async def os_interface(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user: return RedirectResponse("/")
    
    # Load History from DB
    history_objs = db.query(ChatHistory).filter(ChatHistory.username == user).order_by(ChatHistory.timestamp).all()
    history_data = [{"role": h.role, "content": h.content} for h in history_objs]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": user, 
        "history": json.dumps(history_data)
    })

@app.post("/api/interact")
async def interact(
    request: Request,
    message: str = Form(...),
    model: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)

    # 1. Handle File (PDF)
    doc_context = ""
    if file and file.filename.endswith(".pdf"):
        content = await file.read()
        doc_context = extract_pdf(content) or "Error reading PDF."

    # 2. Get Recent History for Context (Last 10 messages)
    history_objs = db.query(ChatHistory).filter(ChatHistory.username == user).order_by(ChatHistory.timestamp.desc()).limit(10).all()
    history_formatted = [{"role": h.role, "content": h.content} for h in reversed(history_objs)]

    # 3. Process
    result = await process_autonomous_request(message, history_formatted, model, doc_context)

    # 4. Save to DB
    db.add(ChatHistory(username=user, role="user", content=f"{message} {'[File Uploaded]' if file else ''}"))
    if result["type"] == "text":
        db.add(ChatHistory(username=user, role="assistant", content=result["content"]))
    elif result["type"] == "image":
        db.add(ChatHistory(username=user, role="assistant", content=f"![Generated Image]({result['content']})"))
    
    db.commit()
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)