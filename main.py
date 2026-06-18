import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import bcrypt
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configuración de BD
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Seguridad
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False

# Modelos
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True) # nullable for backwards compatibility
    role = Column(String, default="Usuario") # Admin, Operador, Usuario

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String)
    description = Column(String)
    total = Column(Float)
    status = Column(String, default="Pendiente")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dashboard Backend")
# Middleware para sesiones
app.add_middleware(SessionMiddleware, secret_key="super-secret-dashboard-key")

templates = Jinja2Templates(directory="templates")

# Dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(UserDB).filter(UserDB.id == user_id).first()
    return None

def login_required(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user

def admin_required(request: Request, db: Session = Depends(get_db)):
    user = login_required(request, db)
    if user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requiere rol de Admin")
    return user

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 303:
        return RedirectResponse(url=exc.headers.get("Location", "/login"))
    # Render error pages dynamically or redirect
    return templates.TemplateResponse(request=request, name="error.html", context={"detail": str(exc.detail)}, status_code=exc.status_code)

# Migración en el inicio
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        db.execute(text("SELECT password FROM users LIMIT 1"))
    except Exception:
        db.rollback()
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR"))
            db.commit()
            print("Columna 'password' añadida a 'users'")
        except Exception as e:
            print(f"Error en migración: {e}")
            db.rollback()
    finally:
        db.close()

# Rutas de Autenticación
@app.get("/login")
def login_view(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user or not user.password or not verify_password(password, user.password):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Credenciales inválidas"})
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)

@app.get("/register")
def register_view(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.email == email).first():
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El email ya está registrado"})
    
    # First user is Admin, rest are Usuario
    is_first = db.query(UserDB).count() == 0
    role = "Admin" if is_first else "Usuario"
    
    new_user = UserDB(name=name, email=email, password=get_password_hash(password), role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-login
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# Rutas del Dashboard
@app.get("/")
def read_dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    users_count = db.query(UserDB).count()
    orders = db.query(OrderDB).all()
    
    total_revenue = sum(o.total for o in orders)
    pending_orders = sum(1 for o in orders if o.status == "Pendiente")
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "orders": orders[:5], # Only 5 recent for main dashboard
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "total_users": users_count
        }
    )

@app.get("/users")
def users_view(request: Request, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    users = db.query(UserDB).all()
    return templates.TemplateResponse(request=request, name="users.html", context={"user": current_user, "users": users})

@app.post("/users/{user_id}/role")
def update_user_role(user_id: int, role: str = Form(...), db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user and user.id != current_user.id: # Prevent changing own role easily
        user.role = role
        db.commit()
    return RedirectResponse(url="/users", status_code=303)

@app.post("/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(admin_required)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user and user.id != current_user.id:
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/users", status_code=303)

@app.get("/orders")
def orders_view(request: Request, db: Session = Depends(get_db), current_user: UserDB = Depends(login_required)):
    orders = db.query(OrderDB).all()
    return templates.TemplateResponse(request=request, name="orders.html", context={"user": current_user, "orders": orders})

@app.post("/orders/add")
def add_order(client_name: str = Form(...), description: str = Form(...), total: float = Form(...), db: Session = Depends(get_db), current_user: UserDB = Depends(login_required)):
    new_order = OrderDB(client_name=client_name, description=description, total=total)
    db.add(new_order)
    db.commit()
    return RedirectResponse(url="/orders", status_code=303)

@app.post("/orders/delete/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: UserDB = Depends(login_required)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return RedirectResponse(url="/orders", status_code=303)

@app.post("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str = Form(...), db: Session = Depends(get_db), current_user: UserDB = Depends(login_required)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return RedirectResponse(url="/orders", status_code=303)