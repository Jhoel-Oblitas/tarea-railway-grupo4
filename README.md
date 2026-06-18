# Panel de Control NEXUS - Tarea Railway Grupo 4

Este es un panel de control administrativo y de gestión de órdenes y cotizaciones moderno, interactivo y responsivo, desarrollado con **FastAPI** para el backend y **Tailwind CSS** para la interfaz visual.

La aplicación utiliza persistencia de datos (por defecto SQLite de forma local y PostgreSQL para entornos de producción) y está lista para ser desplegada en **Railway**.

## Enlaces del Proyecto

* **Repositorio de GitHub:** [https://github.com/Jhoel-Oblitas/tarea-railway-grupo4](https://github.com/Jhoel-Oblitas/tarea-railway-grupo4)
* **Aplicación Desplegada (Railway):** [https://tarea-railway-grupo4-production.up.railway.app](https://tarea-railway-grupo4-production.up.railway.app)

---

## Características Principales

* **Autenticación Completa:** Registro e inicio de sesión de usuarios con contraseñas encriptadas con `bcrypt`.
* **Control de Acceso basado en Roles:**
  * **Admin:** Acceso completo al panel, visualización y administración de usuarios (cambio de roles y eliminación).
  * **Operador / Usuario:** Acceso a la sección de órdenes y cotizaciones.
* **Gestión de Órdenes:** Creación y eliminación de órdenes con cálculo automático de ingresos estimados en tiempo real.
* **Dashboard Moderno:** Interfaz intuitiva con gráficos interactivos dinámicos de ingresos (Chart.js) y diseño premium de tipo Glassmorphism.
* **Arquitectura Robusta:** Manejo estructurado de errores y redirecciones automáticas para sesiones expiradas o no autenticadas.

---

## Tecnologías Utilizadas

* **Backend:** FastAPI (Python 3.9+)
* **Base de Datos:** SQLAlchemy (compatible con SQLite y PostgreSQL)
* **Frontend:** Jinja2 (Plantillas HTML5), Tailwind CSS (Estilos interactivos), Font Awesome 6 (Iconografía) y Chart.js (Visualización de datos)
* **Seguridad:** Passlib (Bcrypt) y Starlette Session Middleware

---

## Configuración y Ejecución Local

Sigue estos pasos para ejecutar el proyecto en tu entorno local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/Jhoel-Oblitas/tarea-railway-grupo4.git
cd tarea-railway-grupo4
```

### 2. Crear y activar un entorno virtual
En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
En macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (Opcional)
Por defecto, de forma local la aplicación utilizará una base de datos SQLite (`local.db`) autocreada. Si deseas usar otra base de datos, define la variable `DATABASE_URL`:
```bash
set DATABASE_URL=postgresql://usuario:contraseña@localhost/nombre_bd
```

### 5. Iniciar la aplicación
```bash
uvicorn main:app --reload
```
La aplicación estará disponible en: `http://127.0.0.1:8000`

---

## Instrucciones de Despliegue en Railway

Para desplegar esta aplicación en **Railway**, sigue estos sencillos pasos:

1. **Crear una cuenta o iniciar sesión** en [Railway.app](https://railway.app/).
2. **Crear un nuevo proyecto:** Selecciona "Deploy from GitHub repo" y elige este repositorio (`tarea-railway-grupo4`).
3. **Agregar una Base de Datos PostgreSQL:**
   * En el canvas de tu proyecto en Railway, haz clic en **+ New** -> **Database** -> **Add PostgreSQL**.
4. **Vincular Base de Datos:**
   * Railway inyectará automáticamente la variable de entorno `DATABASE_URL` a la aplicación de FastAPI si ambos servicios están en el mismo proyecto.
5. **Configurar el Comando de Inicio (Start Command):**
   * En la configuración del servicio de la aplicación web en Railway (pestaña *Settings*), asegúrate de que el comando de inicio sea:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
6. **Desplegar:** Railway construirá y desplegará la aplicación automáticamente con cada commit en la rama principal (`main`).
