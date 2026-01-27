from app.db import SessionLocal
from app import models
from analytics.recommendations import get_recommendations
from datetime import datetime, timedelta
import httpx
from app.config import settings
import pytz

def send_email(to_email: str, subject: str, html_content: str):
    """Send email using Resend API (or other email service)."""
    if not settings.email_api_key or not settings.email_from:
        print(f"[EMAIL] Would send to {to_email}: {subject}")
        print(f"[EMAIL] Content: {html_content[:200]}...")
        return False
    
    try:
        # Using Resend API (simple and free tier available)
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.email_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            print(f"[EMAIL] Sent successfully to {to_email}")
            return True
        else:
            print(f"[EMAIL] Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[EMAIL] Error: {e}")
        return False

def send_digest():
    """Send daily email digest based on user preferences."""
    db = SessionLocal()
    try:
        prefs = db.query(models.UserPreferences).first()
        if not prefs or not prefs.email:
            print("[DIGEST] No preferences or email configured")
            return
        
        recommendations = get_recommendations(db, prefs)
        
        # Build email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #c41e3a;">🏋️ Raider Power Zone - Daily Digest</h2>
            <p>Here are the best times to visit today based on your preferences:</p>
            
            <h3>🎯 Recommended Times ({prefs.workout_duration_minutes} minutes)</h3>
        """.format(prefs=prefs)
        
        if recommendations:
            html_content += "<ul>"
            for time_range, pct in recommendations:
                html_content += f"<li><strong>{time_range}</strong> - {pct:.1f}% average usage</li>"
            html_content += "</ul>"
        else:
            html_content += "<p>No recommendations available at this time.</p>"
        
        html_content += """
            <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                Visit the dashboard: <a href="http://localhost:8000">Raider Power Zone</a>
            </p>
        </body>
        </html>
        """
        
        subject = "🏋️ Raider Power Zone - Daily Digest"
        send_email(prefs.email, subject, html_content)
        
    except Exception as e:
        print(f"[DIGEST] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_and_send_alert():
    """Check if usage is below 30% during preferred timeframe and send alert (once per day)."""
    db = SessionLocal()
    try:
        prefs = db.query(models.UserPreferences).first()
        if not prefs or not prefs.email:
            print("[ALERT] No preferences or email configured")
            return
        
        # Check if alert was already sent today
        tz = pytz.timezone("America/Chicago")
        today = datetime.now(tz).date()
        
        if prefs.last_alert_sent_date:
            last_alert_date = pytz.UTC.localize(prefs.last_alert_sent_date).astimezone(tz).date()
            if last_alert_date == today:
                print("[ALERT] Alert already sent today, skipping")
                return
        
        # Get preferred time window
        if not prefs.preferred_start_time_local or not prefs.preferred_end_time_local:
            print("[ALERT] No preferred time window configured")
            return
        
        start_hour, start_min = map(int, prefs.preferred_start_time_local.split(":"))
        end_hour, end_min = map(int, prefs.preferred_end_time_local.split(":"))
        
        # Get current time in Texas timezone
        now = datetime.now(tz)
        current_hour = now.hour
        current_min = now.minute
        current_minutes = current_hour * 60 + current_min
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # Check if we're within preferred timeframe
        if not (start_minutes <= current_minutes < end_minutes):
            print(f"[ALERT] Current time {current_hour}:{current_min:02d} not in preferred window {prefs.preferred_start_time_local}-{prefs.preferred_end_time_local}")
            return
        
        # Get latest snapshots for selected areas (last hour)
        one_hour_ago = now - timedelta(hours=1)
        query = db.query(models.UsageSnapshot).filter(
            models.UsageSnapshot.timestamp_utc >= one_hour_ago.astimezone(pytz.UTC).replace(tzinfo=None)
        )
        
        if prefs.areas_of_interest:
            query = query.filter(models.UsageSnapshot.location_name.in_(prefs.areas_of_interest))
        
        recent_snapshots = query.order_by(models.UsageSnapshot.timestamp_utc.desc()).limit(20).all()
        
        if not recent_snapshots:
            print("[ALERT] No recent data available")
            return
        
        # Check if any facility has usage below 30%
        low_usage_facilities = []
        for snap in recent_snapshots:
            if snap.usage_percentage < 30:
                # Avoid duplicates
                if not any(f["name"] == snap.location_name for f in low_usage_facilities):
                    low_usage_facilities.append({
                        "name": snap.location_name,
                        "usage": snap.usage_percentage,
                        "time": pytz.UTC.localize(snap.timestamp_utc).astimezone(tz)
                    })
        
        if not low_usage_facilities:
            print("[ALERT] No facilities with usage below 30%")
            return
        
        # Send alert email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #4caf50;">🚨 Low Usage Alert - Raider Power Zone</h2>
            <p>Great news! The following facilities currently have low usage (< 30%):</p>
            
            <ul>
        """
        
        for facility in low_usage_facilities:
            time_str = facility["time"].strftime("%I:%M %p")
            html_content += f'<li><strong>{facility["name"]}</strong>: {facility["usage"]}% (as of {time_str})</li>'
        
        html_content += f"""
            </ul>
            
            <p style="background: #e8f5e9; padding: 15px; border-radius: 5px;">
                <strong>Perfect time to visit!</strong> These facilities are currently less crowded.
            </p>
            
            <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                Visit the dashboard: <a href="http://localhost:8000">Raider Power Zone</a>
            </p>
        </body>
        </html>
        """
        
        subject = "🚨 Raider Power Zone - Low Usage Alert"
        if send_email(prefs.email, subject, html_content):
            # Update last alert sent date
            prefs.last_alert_sent_date = datetime.utcnow()
            db.commit()
            print(f"[ALERT] Alert sent successfully for {len(low_usage_facilities)} facility(ies)")
        else:
            print("[ALERT] Failed to send alert email")
        
    except Exception as e:
        print(f"[ALERT] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
