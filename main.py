import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Configuración de BD
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="Operador")

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String)
    description = Column(String)
    total = Column(Float)
    status = Column(String, default="Pendiente")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dashboard Backend")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas
@app.get("/")
def read_dashboard(request: Request, db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    orders = db.query(OrderDB).all()
    
    total_revenue = sum(o.total for o in orders)
    pending_orders = sum(1 for o in orders if o.status == "Pendiente")
    
    # Asignación explícita de request, name y context
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "users": users,
            "orders": orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "total_users": len(users)
        }
    )

@app.post("/users/add")
def add_user(name: str = Form(...), email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.email == email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    new_user = UserDB(name=name, email=email, role=role)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/orders/add")
def add_order(client_name: str = Form(...), description: str = Form(...), total: float = Form(...), db: Session = Depends(get_db)):
    new_order = OrderDB(client_name=client_name, description=description, total=total)
    db.add(new_order)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/orders/delete/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return RedirectResponse(url="/", status_code=303)