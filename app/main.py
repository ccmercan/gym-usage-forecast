from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text
from app.db import get_db, engine, Base
from app import models
from app.constants import TTU_FACILITIES
import traceback
import os

# Tables are created via Alembic migrations, not here
# Base.metadata.create_all(bind=engine)

def run_migrations_if_needed():
    """Run migrations synchronously at module import time."""
    print("=" * 60)
    print("🚀 Checking database migrations (module import)...")
    print("=" * 60)
    
    try:
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            from app.config import settings
            database_url = settings.database_url or ""
        
        if not database_url:
            print("❌ ERROR: DATABASE_URL environment variable not set!")
            return False
        
        # Check if we can connect to database
        print(f"📡 Connecting to database...")
        
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Check if tables exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            print(f"📊 Found {len(existing_tables)} existing tables: {', '.join(existing_tables) if existing_tables else 'none'}")
            
            user_prefs_exists = 'user_preferences' in existing_tables
            usage_snapshots_exists = 'usage_snapshots' in existing_tables
            
            if user_prefs_exists and usage_snapshots_exists:
                print("✅ All required database tables exist")
                return True
            
            # Tables missing - run migrations
            print("⚠️  Database tables missing!")
            print(f"   - user_preferences: {'✅' if user_prefs_exists else '❌'}")
            print(f"   - usage_snapshots: {'✅' if usage_snapshots_exists else '❌'}")
            print("🔄 Attempting to run migrations...")
            
            from alembic.config import Config
            from alembic import command
            
            # Find alembic.ini
            project_root = os.getcwd()
            alembic_ini_path = os.path.join(project_root, "alembic.ini")
            
            if not os.path.exists(alembic_ini_path):
                alt_paths = [
                    "/app/alembic.ini",
                    os.path.join(os.path.dirname(__file__), "..", "alembic.ini"),
                ]
                for alt_path in alt_paths:
                    abs_path = os.path.abspath(alt_path)
                    if os.path.exists(abs_path):
                        alembic_ini_path = abs_path
                        project_root = os.path.dirname(abs_path)
                        break
            
            if not os.path.exists(alembic_ini_path):
                raise FileNotFoundError(f"alembic.ini not found. Tried: {alembic_ini_path}")
            
            print(f"📝 Configuring Alembic...")
            print(f"   Config file: {alembic_ini_path}")
            print(f"   Working directory: {project_root}")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(project_root)
                
                alembic_cfg = Config(alembic_ini_path)
                alembic_cfg.set_main_option("sqlalchemy.url", database_url)
                
                print("🔄 Running: alembic upgrade head")
                command.upgrade(alembic_cfg, "head")
                
                print("✅ Migrations completed successfully!")
                
            finally:
                os.chdir(original_cwd)
            
            # Verify tables were created
            inspector = inspect(engine)
            new_tables = inspector.get_table_names()
            print(f"📊 Tables after migration: {', '.join(new_tables)}")
            
            # Final check
            if 'user_preferences' in new_tables and 'usage_snapshots' in new_tables:
                return True
            else:
                print("⚠️  Migrations ran but tables still missing!")
                return False
                
    except Exception as e:
        print(f"❌ Migration check failed!")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        traceback.print_exc()
        return False
    finally:
        print("=" * 60)

# Run migrations synchronously at module import time
_migrations_complete = run_migrations_if_needed()

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup_event():
    """Startup event - migrations already run at module import."""
    print(f"🚀 FastAPI startup - Migrations status: {'✅ Complete' if _migrations_complete else '❌ Failed'}")
    if not _migrations_complete:
        print("⚠️  WARNING: Migrations failed during module import. Database operations may fail.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions and return detailed error info."""
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url),
        "traceback": traceback.format_exc()
    }
    print(f"ERROR: {error_detail}")  # Log to console
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    from analytics import get_recommendations, get_heatmap_data
    
    prefs = db.query(models.UserPreferences).first()
    if not prefs:
        # Create default preferences if none exist
        prefs = models.UserPreferences(
            id=1,
            email="",
            timezone="America/Chicago",  # Fixed to Texas time
            preferred_start_time_local="06:00",
            preferred_end_time_local="22:00",
            crowd_tolerance_pct=50,
            areas_of_interest=[],
            workout_duration_minutes=60
        )
        db.add(prefs)
        db.commit()
    
    # Get list of available facilities from database, or use default TTU facilities
    available_facilities = db.query(models.UsageSnapshot.location_name).distinct().all()
    available_facilities = [f[0] for f in available_facilities if f[0]]
    if not available_facilities:
        # Use default TTU facilities if no data yet
        available_facilities = TTU_FACILITIES
    else:
        # Merge with default facilities to ensure all are shown
        available_facilities = sorted(list(set(available_facilities + TTU_FACILITIES)))
    
    try:
        recommendations = get_recommendations(db, prefs)
        heatmap = get_heatmap_data(db, prefs)
    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        import traceback
        traceback.print_exc()
        recommendations = []
        heatmap = {}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prefs": prefs,
        "recommendations": recommendations,
        "heatmap": heatmap,
        "available_facilities": available_facilities
    })

@app.post("/", response_class=HTMLResponse)
async def save_and_show(request: Request, db: Session = Depends(get_db)):
    from analytics import get_recommendations, get_heatmap_data
    
    form = await request.form()
    prefs = db.query(models.UserPreferences).first()
    if not prefs:
        prefs = models.UserPreferences(id=1, timezone="America/Chicago")
        db.add(prefs)
    
    # Save settings (timezone is always America/Chicago for Texas)
    new_email = (form.get("email", "") or "").strip()
    # Privacy: email field renders empty by default; don't erase stored email unless user provides one.
    if new_email:
        prefs.email = new_email
    prefs.timezone = "America/Chicago"  # Fixed to Texas time
    prefs.preferred_start_time_local = form.get("start_time", "06:00")
    prefs.preferred_end_time_local = form.get("end_time", "22:00")
    prefs.digest_send_time_local = form.get("digest_time", "07:00")
    prefs.workout_duration_minutes = int(form.get("workout_duration", 60))
    
    # Parse areas of interest from checkboxes
    areas = form.getlist("areas")  # Get all checked checkboxes
    prefs.areas_of_interest = areas if areas else []  # Empty list = all areas
    
    db.commit()
    
    # Get list of available facilities from database, or use default TTU facilities
    available_facilities = db.query(models.UsageSnapshot.location_name).distinct().all()
    available_facilities = [f[0] for f in available_facilities if f[0]]
    if not available_facilities:
        # Use default TTU facilities if no data yet
        available_facilities = TTU_FACILITIES
    else:
        # Merge with default facilities to ensure all are shown
        available_facilities = sorted(list(set(available_facilities + TTU_FACILITIES)))
    
    try:
        recommendations = get_recommendations(db, prefs)
        heatmap = get_heatmap_data(db, prefs)
    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        recommendations = []
        heatmap = {}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prefs": prefs,
        "recommendations": recommendations,
        "heatmap": heatmap,
        "available_facilities": available_facilities,
        "saved": True
    })
