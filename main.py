"""
VIN ETERNITY: FIXED AUTH EDITION
Architect: V.K.
"""

import os
import logging
import json
import urllib.parse
from datetime import datetime

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from groq import AsyncGroq
from duckduckgo_search import DDGS
from pypdf import PdfReader

# DATABASE
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=API_KEY)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="vin-master-key-fixed", https_only=False)
templates = Jinja2Templates(directory="templates")

# --- DATABASE ---
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
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- TOOLS ---
def search_web(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else None
    except: return None

def generate_image(prompt):
    safe_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&private=true&enhance=true&model=flux"

def extract_pdf(file_bytes):
    try:
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() for page in reader.pages])[:5000]
    except: return None

# --- BRAIN ---
async def process_request(prompt, history, model, doc_context=""):
    prompt_lower = prompt.lower()
    
    # 1. IMAGE
    if any(x in prompt_lower for x in ["generate image", "draw", "create a picture"]):
        clean = prompt.replace("generate image", "").replace("draw", "").strip()
        return {"type": "image", "content": generate_image(clean)}

    # 2. WEB
    sys_msg = "You are VinEternity v10. Created by Vinay."
    if any(x in prompt_lower for x in ["news", "price", "latest", "today", "who won"]):
        web = search_web(prompt)
        if web: sys_msg += f"\nLIVE WEB DATA:\n{web}"

    # 3. PDF
    if doc_context: sys_msg += f"\nDOCUMENT DATA:\n{doc_context}"

    # 4. CHAT
    msgs = [{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": prompt}]
    
    try:
        completion = await client.chat.completions.create(
            messages=msgs, model="llama-3.3-70b-versatile", temperature=0.7
        )
        return {"type": "text", "content": completion.choices[0].message.content}
    except Exception as e:
        return {"type": "error", "content": str(e)}

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse("/os", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/auth/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    
    # --- MASTER KEY OVERRIDE (Safety Net) ---
    # This ensures you can ALWAYS login, even if DB is broken
    if username == "Vinay" and password == "Boss123":
        request.session["user"] = "Vinay"
        return RedirectResponse("/os", status_code=303)
    # ----------------------------------------

    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "ACCESS DENIED"})
    
    request.session["user"] = username
    return RedirectResponse("/os", status_code=303)

@app.post("/auth/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("login.html", {"request": request, "error": "IDENTITY ALREADY EXISTS"})
    
    # Create new user
    new_user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(new_user)
    db.commit()
    
    # Auto-login after register
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
    
    # Load history
    history = db.query(ChatHistory).filter(ChatHistory.username == user).limit(20).all()
    history_data = [{"role": h.role, "content": h.content} for h in history]
    
    return templates.TemplateResponse("index.html", {
        "request": request, "user": user, "history": json.dumps(history_data)
    })

@app.post("/api/interact")
async def interact(request: Request, message: str = Form(...), model: str = Form(...), file: UploadFile = File(None), db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user: return JSONResponse({"error": "Unauthorized"}, 401)

    doc_context = ""
    if file and file.filename.endswith(".pdf"):
        doc_context = extract_pdf(await file.read())

    # Get context
    history_objs = db.query(ChatHistory).filter(ChatHistory.username == user).limit(5).all()
    history = [{"role": h.role, "content": h.content} for h in history_objs]

    result = await process_request(message, history, model, doc_context)

    # Save
    db.add(ChatHistory(username=user, role="user", content=message))
    db.add(ChatHistory(username=user, role="assistant", content=result["content"]))
    db.commit()

    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
