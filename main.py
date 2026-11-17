from fastapi import FastAPI, Request, Form, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import SessionLocal, User, Meal, init_db
import os
import shutil
import uvicorn

# Инициализируем базу данных (создает таблицы, если их нет)
init_db()

app = FastAPI()

# Создаем папку для аватарок, если её нет
if not os.path.exists("static/uploads"): 
    os.makedirs("static/uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ГЛАВНАЯ СТРАНИЦА (ВХОД И РЕГИСТРАЦИЯ) ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "user": None})

@app.get("/home/{username}", response_class=HTMLResponse)
async def home_logged(request: Request, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user: 
        return RedirectResponse("/")
    # Здесь обычно открывают отдельную страницу кабинета, но если у тебя всё в index.html, оставляем так:
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "user": user})

# --- АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ---
@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    # Проверяем, существует ли пользователь и правильный ли у него пароль
    if user and user.password == password:
        # Успешный вход -> пускаем на домашнюю страницу пользователя
        return RedirectResponse(url=f"/home/{username}", status_code=303)
    else:
        # Ошибка -> возвращаем index.html с сообщением (как ты и просил)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Неправильный логин или пароль!"
        })

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), grade: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    
    # Добавил проверку: если пользователь уже есть, не даем создать дубликат
    if user:
        db.close()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Пользователь с таким логином уже существует!"
        })
        
    new_user = User(username=username, password=password, first_name=first_name, last_name=last_name, grade=grade, coins=10)
    db.add(new_user)
    db.commit()
    db.close()
    return RedirectResponse(url=f"/home/{username}", status_code=303)

# --- ЕДА ---
@app.get("/meals/{username}")
async def show_meals(request: Request, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return templates.TemplateResponse(request=request, name="meals.html", context={"request": request, "user": user})

@app.get("/get_meal/{username}/{date}")
async def get_meal(username: str, date: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    meals = []
    if user:
        data = db.query(Meal).filter(Meal.user_id == user.id, Meal.date == date).all()
        meals = [m.meal_type for m in data]
    db.close()
    return {"meals": meals}

@app.post("/book_meal")
async def book_meal(data: dict = Body(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == data['username']).first()
    if user:
        db.query(Meal).filter(Meal.user_id == user.id, Meal.date == data['date']).delete()
        for m in data['meals']:
            db.add(Meal(user_id=user.id, date=data['date'], meal_type=m))
        db.commit()
    db.close()
    return {"status": "success"}

# --- ПРОФИЛЬ ---
@app.get("/profile/{username}")
async def show_profile(request: Request, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return templates.TemplateResponse(request=request, name="profile.html", context={"request": request, "user": user})

@app.post("/update_profile")
async def update_profile(username: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), grade: str = Form(...), profile_pic: UploadFile = File(None)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.first_name = first_name
        user.last_name = last_name
        user.grade = grade
        if profile_pic and profile_pic.filename:
            path = f"static/uploads/{username}_{profile_pic.filename}"
            with open(path, "wb") as buffer: 
                shutil.copyfileobj(profile_pic.file, buffer)
            user.profile_image = f"/{path}"
        db.commit()
    db.close()
    return RedirectResponse(url=f"/profile/{username}", status_code=303)

# --- АДМИНКА (ОТЧЕТЫ И УПРАВЛЕНИЕ) ---
@app.get("/admin/{username}")
async def admin_panel(request: Request, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or not getattr(user, 'is_admin', False): # Безопасная проверка на админа
        db.close()
        return RedirectResponse(url="/")
    all_users = db.query(User).all()
    db.close()
    return templates.TemplateResponse(request=request, name="admin.html", context={"request": request, "user": user, "all_users": all_users})

@app.get("/admin/report/{date}")
async def admin_report(date: str):
    db = SessionLocal()
    records = db.query(Meal).filter(Meal.date == date).all()
    res = []
    for r in records:
        res.append({
            "name": f"{r.owner.first_name} {r.owner.last_name}",
            "grade": r.owner.grade,
            "meal": r.meal_type,  
            "avatar": r.owner.profile_image
        })
    db.close()
    return {"records": res}

@app.post("/give_coins")
async def give_coins(data: dict = Body(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == data['target_username']).first()
    if user:
        user.coins += data['amount']
        db.commit()
        new_balance = user.coins
        db.close()
        return {"new_balance": new_balance}
    db.close()
    return {"error": "User not found"}

@app.post("/delete_user")
async def delete_user(data: dict = Body(...)):
    db = SessionLocal()
    db.query(Meal).filter(Meal.user_id == data['target_id']).delete()
    db.query(User).filter(User.id == data['target_id']).delete()
    db.commit()
    db.close()
    return {"status": "deleted"}

@app.get("/about/{username}")
async def about_us(request: Request, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return templates.TemplateResponse(request=request, name="about.html", context={"request": request, "user": user})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)