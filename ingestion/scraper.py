from playwright.sync_api import sync_playwright
from datetime import datetime
from app.db import SessionLocal
from app import models
import re

PARSER_VERSION = "1.0"

def scrape():
    """
    Scrape TTU Live Facility Counts from hours.php and store in DB.
    
    Note: Data is manually updated by the university on the page.
    This scraper is read-only and does not modify any TTU systems.
    URL: https://www.depts.ttu.edu/recreation/facilities/hours.php
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.depts.ttu.edu/recreation/facilities/hours.php", wait_until="networkidle")
        
        # Wait for page to fully load
        page.wait_for_load_state("networkidle")
        
        locations = []
        try:
            # Wait for LIVE FACILITY COUNTS section (best-effort)
            try:
                page.wait_for_selector("div#charts h1:has-text('LIVE FACILITY COUNTS')", timeout=5000)
            except:
                pass  # Continue even if selector doesn't match exactly
            
            # Strategy 1 (primary): SVG charts inside #charts
            # Structure example:
            # <div id="charts">
            #   <svg class="chart">
            #     <text x="20" y="20">Raider Power Zone</text>
            #     <text x="20" y="35">Last Updated: 4:34 PM</text>
            #     <text x="200" y="45">83%</text>
            #   ...
            chart_svgs = page.query_selector_all("#charts svg.chart")
            for svg in chart_svgs:
                texts = svg.query_selector_all("text")
                if len(texts) < 3:
                    continue
                
                name_text = (texts[0].inner_text() or "").strip()
                pct_text = (texts[2].inner_text() or "").strip()
                
                percent_match = re.search(r'(\d+)\s*%', pct_text)
                if not percent_match:
                    continue
                
                try:
                    pct = int(percent_match.group(1))
                except ValueError:
                    continue
                
                if 0 <= pct <= 100 and len(name_text) > 2:
                    if not any(loc["name"] == name_text for loc in locations):
                        locations.append({"name": name_text, "usage": pct})
            
            # Strategy 2 (fallback): parse entire page text if SVG parsing fails
            if not locations:
                body = page.query_selector("body")
                if body:
                    body_text = body.inner_text()
                    # Look for patterns like "Facility Name: XX%" or "Facility Name XX%"
                    pattern = re.compile(
                        r'([A-Z][A-Za-z\s&]+?)\s*[:]?\s*(\d+)\s*%|'
                        r'(\d+)\s*%\s*([A-Z][A-Za-z\s&]+)',
                        re.IGNORECASE | re.MULTILINE
                    )
                    matches = pattern.findall(body_text)
                    
                    for match in matches:
                        # Handle both pattern directions
                        if match[0] and match[1]:  # "Name: XX%"
                            name = match[0].strip()
                            pct = int(match[1])
                        elif match[2] and match[3]:  # "XX% Name"
                            name = match[3].strip()
                            pct = int(match[2])
                        else:
                            continue
                        
                        # Filter out false positives
                        if (0 <= pct <= 100 and 
                            len(name) > 2 and 
                            name.lower() not in ['the', 'and', 'for', 'university', 'recreation'] and
                            not any(loc["name"] == name for loc in locations)):
                            locations.append({"name": name, "usage": pct})
            
            # Debug: Print what we found
            if locations:
                print(f"Found {len(locations)} facilities:")
                for loc in locations:
                    print(f"  - {loc['name']}: {loc['usage']}%")
            else:
                # Save page HTML for debugging
                html = page.content()
                print("No locations found. Page structure:")
                print(html[:1000])  # First 1000 chars for debugging
                
        except Exception as e:
            print(f"Scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        browser.close()
    
    if not locations:
        print("No locations found - check selectors or page structure")
        return
    
    db = SessionLocal()
    try:
        stored_count = 0
        for loc in locations:
            # Check for duplicates (timestamp + location) - within same minute
            cutoff = datetime.utcnow().replace(second=0, microsecond=0)
            existing = db.query(models.UsageSnapshot).filter(
                models.UsageSnapshot.location_name == loc["name"],
                models.UsageSnapshot.timestamp_utc >= cutoff
            ).first()
            
            if not existing:
                snapshot = models.UsageSnapshot(
                    timestamp_utc=datetime.utcnow(),
                    location_name=loc["name"],
                    usage_percentage=loc["usage"],
                    parser_version=PARSER_VERSION
                )
                db.add(snapshot)
                stored_count += 1
        db.commit()
        print(f"Stored {stored_count} new snapshots")
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        db.close()
