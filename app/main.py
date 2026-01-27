from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_db, engine, Base
from app import models
from app.constants import TTU_FACILITIES
import traceback

# Tables are created via Alembic migrations, not here
# Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

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
    prefs.email = form.get("email", "")
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
