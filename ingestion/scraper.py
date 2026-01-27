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
            # Wait for LIVE FACILITY COUNTS section
            try:
                page.wait_for_selector("h1:has-text('LIVE FACILITY COUNTS'), h1:has-text('LIVE'), text='LIVE FACILITY COUNTS'", timeout=5000)
            except:
                pass  # Continue even if selector doesn't match exactly
            
            # Strategy 1: Look for structured data (tables, divs with facility info)
            facility_elements = page.query_selector_all(
                "table tr, [class*='facility'], [class*='zone'], [class*='area'], "
                "[class*='count'], [class*='usage'], [id*='facility'], [id*='zone']"
            )
            
            for elem in facility_elements:
                text = elem.inner_text()
                # Look for percentage patterns: "XX%" or "XX %"
                percent_match = re.search(r'(\d+)\s*%', text)
                if percent_match:
                    # Extract facility name (text before percentage, clean it up)
                    lines = text.split('\n')
                    for line in lines:
                        if '%' in line:
                            # Try to extract name and percentage from this line
                            parts = re.split(r'(\d+\s*%)', line)
                            if len(parts) >= 2:
                                name = parts[0].strip().rstrip(':-').strip()
                                pct_str = parts[1].replace('%', '').strip()
                                try:
                                    pct = int(pct_str)
                                    if 0 <= pct <= 100 and len(name) > 2:
                                        # Avoid duplicates
                                        if not any(loc["name"] == name for loc in locations):
                                            locations.append({"name": name, "usage": pct})
                                except ValueError:
                                    pass
            
            # Strategy 2: If no structured data found, parse entire page text
            if not locations:
                body_text = page.query_selector("body").inner_text()
                # Look for patterns like "Facility Name: XX%" or "Facility Name XX%"
                # More specific pattern for facility counts
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
