#!/usr/bin/env python3
import sys
import os
import urllib.request
import urllib.parse
import json
import time

# Parse CLI Arguments
def get_arg(name, default):
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == name:
            return sys.argv[i+1]
    return default

# Print Help
if "--help" in sys.argv or "-h" in sys.argv:
    print("Usage: python3 planet_position.py [options]")
    print("Options:")
    print("  --datetime DATETIME   ISO-8601 birth/query time (e.g. 1995-05-15T08:30:00+05:30)")
    print("  --latitude LAT        Latitude coordinate (e.g. 19.076)")
    print("  --longitude LNG       Longitude coordinate (e.g. 72.877)")
    print("  --demo                Force Demo/Mock mode (default if no keys in .env)")
    sys.exit(0)

# Configuration defaults
DATETIME = get_arg("--datetime", time.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
LATITUDE = get_arg("--latitude", "19.076")
LONGITUDE = get_arg("--longitude", "72.877")
FORCE_DEMO = "--demo" in sys.argv

# Load .env variables
CLIENT_ID = ""
CLIENT_SECRET = ""
DEMO_MODE = True

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if key == "PROKERALA_CLIENT_ID":
                    CLIENT_ID = val
                elif key == "PROKERALA_CLIENT_SECRET":
                    CLIENT_SECRET = val

DEMO_MODE = FORCE_DEMO or not (CLIENT_ID and CLIENT_SECRET)

def get_access_token():
    if DEMO_MODE:
        return "demo_token"
        
    token_url = "https://api.prokerala.com/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).encode('utf-8')
    
    req = urllib.request.Request(
        token_url,
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('access_token')
    except Exception as e:
        print(f"Error fetching token: {e}")
        return None

def get_mock_planet_positions():
    return [
        {"planet": "Sun", "sign": "Taurus", "house": 7, "longitude": 59.2, "degree": 29.1, "nakshatra": "Mrigashira", "is_retrograde": False},
        {"planet": "Moon", "sign": "Taurus", "house": 7, "longitude": 38.5, "degree": 8.5, "nakshatra": "Krittika", "is_retrograde": False},
        {"planet": "Mars", "sign": "Pisces", "house": 5, "longitude": 345.3, "degree": 15.3, "nakshatra": "Uttara Bhadrapada", "is_retrograde": False},
        {"planet": "Mercury", "sign": "Gemini", "house": 8, "longitude": 64.1, "degree": 4.1, "nakshatra": "Ardra", "is_retrograde": True},
        {"planet": "Jupiter", "sign": "Aquarius", "house": 4, "longitude": 322.8, "degree": 22.8, "nakshatra": "Purva Bhadrapada", "is_retrograde": False},
        {"planet": "Venus", "sign": "Aries", "house": 6, "longitude": 11.2, "degree": 11.2, "nakshatra": "Ashwini", "is_retrograde": False},
        {"planet": "Saturn", "sign": "Capricorn", "house": 3, "longitude": 276.4, "degree": 6.4, "nakshatra": "Uttarashadha", "is_retrograde": False}
    ]

def get_planet_positions():
    if DEMO_MODE:
        return get_mock_planet_positions()
        
    token = get_access_token()
    if not token:
        print("[Warning] Token request failed, falling back to mock positions.")
        return get_mock_planet_positions()
        
    coordinates = f"{LATITUDE},{LONGITUDE}"
    url = f"https://api.prokerala.com/v2/astrology/planet-position?datetime={urllib.parse.quote(DATETIME)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            data = res_data.get("data", {})
            return data.get("planet_position") or data.get("planetary_positions") or []
    except Exception as e:
        print(f"API Error: {e}, falling back to mock positions.")
        return get_mock_planet_positions()

# Run and format outputs
def main():
    print("==========================================================================================")
    print("                      PROKERALA API PLANETARY POSITIONS                                   ")
    print("==========================================================================================")
    print(f" Query Time: {DATETIME}")
    print(f" Location  : Lat {LATITUDE}, Lng {LONGITUDE}")
    print(f" Mode      : {'DEMO / MOCK' if DEMO_MODE else 'REAL API'}")
    print("==========================================================================================")
    
    planets = get_planet_positions()
    
    # Table Header
    print(f"{'Planet':<12} | {'Zodiac Sign':<12} | {'Rasi Lord (Vedic)':<22} | {'Degree':<8} | {'Retrograde':<10}")
    print("-" * 90)
    
    for p in planets:
        planet_name = p.get("name") or p.get("planet") or "N/A"
        
        # Parse Rasi info
        rasi = p.get("rasi")
        if isinstance(rasi, dict):
            sign = rasi.get("name", "N/A")
            lord_name = rasi.get("lord", {}).get("name", "N/A")
            lord_vedic = rasi.get("lord", {}).get("vedic_name", "N/A")
            lord_info = f"{lord_name} ({lord_vedic})"
        else:
            sign = p.get("sign") or "N/A"
            lord_info = "N/A"
            
        deg = f"{p.get('degree', 0):.1f}°" if isinstance(p.get('degree'), (int, float)) else "N/A"
        retro = "Yes" if p.get("is_retrograde", False) or p.get("isRetrograde", False) else "No"
        
        print(f"{planet_name:<12} | {sign:<12} | {lord_info:<22} | {deg:<8} | {retro:<10}")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
