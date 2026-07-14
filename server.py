#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import time
import sys

# Default Configuration
PORT = 8081
HOST = "127.0.0.1"
CLIENT_ID = "7c8aab4e-0ae2-4b0a-80d8-bec99bce62e3"
CLIENT_SECRET = "IzHT9zLCDZUbHFvCml3AEY2l6TF6VK1VEyF5A2tS"
DEMO_MODE = False
ASTRONOMY_APP_ID = "a8a51d7a-ed3e-466d-b471-5dbc7e720585"
ASTRONOMY_APP_SECRET = "a8e0cfe6322276cf7c5180f883e54fd620d56424c2d5cabc099a5a63d2dccfaaed24474ff7409ec178ff232809e478cbc4fef0e4e80438fb35b446edf7cce7f3950716308a87fc89bd2c10cb76d739c911f11bab191812d7561ca2de70d8c563e5d14fdedfb545c33785c6a7b8d2bdbb"
DIVINE_API_KEY = "77e886281509a6f7374c206bbc3cbb77"
DIVINE_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2RpdmluZWFwaS5jb20vc2lnbnVwIiwiaWF0IjoxNzgzODQwNDYwLCJuYmYiOjE3ODM4NDA0NjAsImp0aSI6Ijh0eWJnTkVGekNRWEpRNUYiLCJzdWIiOiI1NDMxIiwicHJ2IjoiZTZlNjRiYjBiNjEyNmQ3M2M2Yjk3YWZjM2I0NjRkOTg1ZjQ2YzlkNyJ9.WSCRA_VwPPvy0i0dFLK1TUOhaSSLkZ81o7MiJVPBxr4"

# Load .env file manually and check system environment
def load_env():
    global HOST, PORT, CLIENT_ID, CLIENT_SECRET, DEMO_MODE, ASTRONOMY_APP_ID, ASTRONOMY_APP_SECRET, DIVINE_API_KEY, DIVINE_ACCESS_TOKEN
    
    # 1. Read from system environment first (critical for Vercel!)
    CLIENT_ID = os.environ.get("PROKERALA_CLIENT_ID", "")
    CLIENT_SECRET = os.environ.get("PROKERALA_CLIENT_SECRET", "")
    ASTRONOMY_APP_ID = os.environ.get("ASTRONOMY_APP_ID", "")
    ASTRONOMY_APP_SECRET = os.environ.get("ASTRONOMY_APP_SECRET", "")
    DIVINE_API_KEY = os.environ.get("DIVINE_API_KEY", "")
    DIVINE_ACCESS_TOKEN = os.environ.get("DIVINE_ACCESS_TOKEN", "")
    
    # 2. Try to load local .env file overrides
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
                    
                    if key == "PROKERALA_CLIENT_ID" and val:
                        CLIENT_ID = val
                    elif key == "PROKERALA_CLIENT_SECRET" and val:
                        CLIENT_SECRET = val
                    elif key == "ASTRONOMY_APP_ID" and val:
                        ASTRONOMY_APP_ID = val
                    elif key == "ASTRONOMY_APP_SECRET" and val:
                        ASTRONOMY_APP_SECRET = val
                    elif key == "DIVINE_API_KEY" and val:
                        DIVINE_API_KEY = val
                    elif key == "DIVINE_ACCESS_TOKEN" and val:
                        DIVINE_ACCESS_TOKEN = val
                    elif key == "PORT":
                        try:
                            PORT = int(val)
                        except ValueError:
                            pass
                    elif key == "HOST":
                        HOST = val

    if CLIENT_ID and CLIENT_SECRET:
        DEMO_MODE = False
    else:
        DEMO_MODE = True

# Run load_env() immediately at the module level
load_env()

# AstronomyAPI Helper Functions
def parse_datetime_helper(dt_str):
    import datetime
    try:
        parts = dt_str.split('T')
        date_parts = parts[0].split('-')
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        
        time_part = parts[1]
        tz_char = '+'
        if '-' in time_part:
            tz_char = '-'
        elif 'Z' in time_part:
            tz_char = 'Z'
            
        if tz_char == 'Z':
            time_only = time_part.replace('Z', '')
            tzone = 0.0
        else:
            time_only, offset = time_part.split(tz_char, 1)
            offset_parts = offset.split(':')
            offset_hours = int(offset_parts[0])
            offset_mins = int(offset_parts[1]) if len(offset_parts) > 1 else 0
            tzone = offset_hours + offset_mins / 60.0
            if tz_char == '-':
                tzone = -tzone
                
        time_subparts = time_only.split(':')
        hour = int(time_subparts[0])
        minute = int(time_subparts[1])
        second = int(time_subparts[2]) if len(time_subparts) > 2 else 0
    except Exception as e:
        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
        hour, minute, second = now.hour, now.minute, now.second
        tzone = 5.5
    
    return {
        "year": year, "month": month, "day": day,
        "hour": hour, "min": minute, "sec": second,
        "tzone": tzone
    }

def get_nakshatra_details(lon):
    import math
    # 27 Nakshatras
    nakshatras_list = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", 
        "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", 
        "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", 
        "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    
    # 9 Vimshottari Lords in order
    lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    dasha_years = [7, 20, 6, 10, 7, 18, 16, 19, 17] # total 120
    
    nak_idx = int(lon * 27 / 360) % 27
    nak_name = nakshatras_list[nak_idx]
    
    # Pada (1 to 4)
    nak_start_lon = nak_idx * (360.0 / 27.0)
    relative_lon = (lon - nak_start_lon) % (360.0 / 27.0)
    pada = int(relative_lon / (360.0 / 108.0)) + 1
    
    # Nakshatra Lord
    nak_lord_idx = nak_idx % 9
    nak_lord = lords[nak_lord_idx]
    
    # KP Sub Lord
    # Sub-lords in a nakshatra start from the nakshatra lord
    # Let's map the cumulative arc minutes relative to nakshatra start (total 800 minutes)
    relative_minutes = relative_lon * 60.0
    sub_lords_order = lords[nak_lord_idx:] + lords[:nak_lord_idx]
    sub_spans_minutes = [y / 120.0 * 800.0 for y in [dasha_years[lords.index(l)] for l in sub_lords_order]]
    
    cumulative = 0.0
    sub_lord = sub_lords_order[0]
    for idx, span in enumerate(sub_spans_minutes):
        cumulative += span
        if relative_minutes <= cumulative:
            sub_lord = sub_lords_order[idx]
            break
            
    return nak_name, pada, nak_lord, sub_lord

def get_planet_speed(planet_name, is_retrograde=False):
    speeds = {
        "Sun": 0.9856, "Moon": 13.176, "Mercury": 1.2, "Venus": 1.2,
        "Mars": 0.524, "Jupiter": 0.083, "Saturn": 0.033, "Uranus": 0.0117,
        "Neptune": 0.006, "Pluto": 0.004, "True North Node": -0.053, "True South Node": -0.053
    }
    base_speed = speeds.get(planet_name, 0.0)
    if is_retrograde:
        return -abs(base_speed)
    return base_speed

def calculate_true_ascendant(dt_str, lat, lng):
    import math
    from datetime import datetime
    
    # Parse datetime
    dt_info = parse_datetime_helper(dt_str)
    
    # Calculate Julian Date (JD)
    y, m, d = dt_info["year"], dt_info["month"], dt_info["day"]
    h, mn, s = dt_info["hour"], dt_info["min"], dt_info["sec"]
    tz = dt_info["tzone"]
    
    # Convert local time to UTC decimal hours
    utc_hours = h + mn/60.0 + s/3600.0 - tz
    
    # Julian Date calculation
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5 + (utc_hours / 24.0)
    
    # Greenwich Sidereal Time (GST) in degrees
    d_jd = jd - 2451545.0
    mst = (280.46061837 + 360.98564736629 * d_jd) % 360
    
    # Local Sidereal Time (LST) in degrees
    lst = (mst + float(lng)) % 360
    
    # Obliquity eps = 23.44 degrees
    eps = math.radians(23.44)
    lst_rad = math.radians(lst)
    lat_rad = math.radians(float(lat))
    
    # Ascendant formula
    # tan(asc) = -cos(lst) / (sin(lst)*cos(eps) + tan(lat)*sin(eps))
    num = -math.cos(lst_rad)
    den = math.sin(lst_rad) * math.cos(eps) + math.tan(lat_rad) * math.sin(eps)
    
    asc_rad = math.atan2(num, den)
    asc_deg = math.degrees(asc_rad) % 360
    return asc_deg

def calculate_horizontal_coords(ecl_lon, ecl_lat, dt_str, obs_lat, obs_lng):
    import math
    
    # Parse datetime
    dt_info = parse_datetime_helper(dt_str)
    
    # Julian Date (JD)
    y, m, d = dt_info["year"], dt_info["month"], dt_info["day"]
    h, mn, s = dt_info["hour"], dt_info["min"], dt_info["sec"]
    tz = dt_info["tzone"]
    
    utc_hours = h + mn/60.0 + s/3600.0 - tz
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5 + (utc_hours / 24.0)
    
    # LST in degrees
    d_jd = jd - 2451545.0
    mst = (280.46061837 + 360.98564736629 * d_jd) % 360
    lst = (mst + float(obs_lng)) % 360
    
    # Ecliptic to Equatorial conversion
    # Obliquity eps = 23.44 degrees
    eps = math.radians(23.44)
    lam = math.radians(ecl_lon)
    beta = math.radians(ecl_lat)
    
    sin_delta = math.sin(beta)*math.cos(eps) + math.cos(beta)*math.sin(eps)*math.sin(lam)
    delta = math.asin(sin_delta)
    
    y_eq = -math.sin(beta)*math.sin(eps) + math.cos(beta)*math.cos(eps)*math.sin(lam)
    x_eq = math.cos(beta)*math.cos(lam)
    alpha = math.atan2(y_eq, x_eq) # in radians
    
    # Hour angle H = LST - alpha
    lst_rad = math.radians(lst)
    H = lst_rad - alpha
    
    # Equatorial to Horizontal conversion
    obs_lat_rad = math.radians(float(obs_lat))
    
    sin_alt = math.sin(delta)*math.sin(obs_lat_rad) + math.cos(delta)*math.cos(obs_lat_rad)*math.cos(H)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt_rad = math.asin(sin_alt)
    alt_deg = math.degrees(alt_rad)
    
    y_az = -math.sin(H)*math.cos(delta)
    x_az = math.sin(delta)*math.cos(obs_lat_rad) - math.sin(alt_rad)*math.sin(obs_lat_rad)
    az_rad = math.atan2(y_az, x_az)
    az_deg = math.degrees(az_rad) % 360
    
    # Format Altitude and Azimuth
    alt_sign = "+" if alt_deg >= 0 else "-"
    alt_abs = abs(alt_deg)
    alt_d = int(alt_abs)
    alt_m = int((alt_abs - alt_d) * 60)
    alt_s = int(((alt_abs - alt_d) * 60 - alt_m) * 60)
    alt_str = f"{alt_sign}{alt_d:02d}° {alt_m:02d}' {alt_s:02d}\""
    
    az_d = int(az_deg)
    az_m = int((az_deg - az_d) * 60)
    az_s = int(((az_deg - az_d) * 60 - az_m) * 60)
    az_str = f"{az_d:02d}° {az_m:02d}' {az_s:02d}\""
    
    return alt_str, az_str

def equatorial_to_longitude(ra_deg, dec_deg):
    import math
    eps = math.radians(23.44)
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)
    
    # sin(beta) = sin(delta)*cos(eps) - cos(delta)*sin(eps)*sin(alpha)
    # cos(lambda)*cos(beta) = cos(delta)*cos(alpha)
    # sin(lambda)*cos(beta) = sin(delta)*sin(eps) + cos(delta)*cos(eps)*sin(alpha)
    y = math.sin(delta) * math.sin(eps) + math.cos(delta) * math.cos(eps) * math.sin(alpha)
    x = math.cos(delta) * math.cos(alpha)
    
    lam_rad = math.atan2(y, x)
    lam_deg = math.degrees(lam_rad) % 360
    return lam_deg

def longitude_to_equatorial(lon_deg):
    import math
    # Convert ecliptic longitude to Right Ascension and Declination
    # obliquity epsilon = 23.44 degrees
    eps = math.radians(23.44)
    lam = math.radians(lon_deg)
    
    # sin(delta) = sin(lam) * sin(eps)
    sin_dec = math.sin(lam) * math.sin(eps)
    dec_rad = math.asin(sin_dec)
    dec_deg = math.degrees(dec_rad)
    
    # tan(alpha) = cos(eps) * tan(lam)
    y = math.sin(lam) * math.cos(eps)
    x = math.cos(lam)
    ra_rad = math.atan2(y, x)
    ra_deg = math.degrees(ra_rad) % 360
    
    # Format RA as degrees/points (e.g. 111.23°)
    ra_str = f"{round(ra_deg, 2)}°"
    
    # Format Declination as degrees, minutes, seconds
    dec_sign = "+" if dec_deg >= 0 else "-"
    dec_abs = abs(dec_deg)
    dec_d = int(dec_abs)
    dec_m = int((dec_abs - dec_d) * 60)
    dec_s = int(((dec_abs - dec_d) * 60 - dec_m) * 60)
    dec_str = f"{dec_sign}{dec_d:02d}° {dec_m:02d}' {dec_s:02d}\""
    
    return ra_str, dec_str

def get_astronomy_planet_position(dt, lat, lng):
    import base64
    import urllib.request
    import json
    import math
    
    if not ASTRONOMY_APP_ID or not ASTRONOMY_APP_SECRET:
        return None
        
    dt_info = parse_datetime_helper(dt)
    from_date = f"{dt_info['year']:04d}-{dt_info['month']:02d}-{dt_info['day']:02d}"
    time_str = f"{dt_info['hour']:02d}:{dt_info['min']:02d}:{dt_info['sec']:02d}"
    
    auth_str = f"{ASTRONOMY_APP_ID}:{ASTRONOMY_APP_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    
    url = f"https://api.astronomyapi.com/api/v2/bodies/positions?latitude={lat}&longitude={lng}&elevation=0&from_date={from_date}&to_date={from_date}&time={time_str}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Basic {auth_b64}')
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res = json.loads(response.read().decode('utf-8'))
            rows = res.get("data", {}).get("table", {}).get("rows", [])
            mapped = []
            
            name_map = {
                "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
                "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus",
                "neptune": "Neptune", "pluto": "Pluto"
            }
            lord_map = {
                "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
                "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
                "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
            }
            signs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            
            def fmt_dms(deg_str, signed=True):
                try:
                    d = float(deg_str)
                    s = "-" if d < 0 else ("+" if signed else "")
                    d_abs = abs(d)
                    d_int = int(d_abs)
                    m_int = int((d_abs - d_int) * 60)
                    s_int = round(((d_abs - d_int) * 60 - m_int) * 60)
                    if s_int == 60: m_int += 1; s_int = 0
                    return f"{s}{d_int:02d}° {m_int:02d}' {s_int:02d}\""
                except:
                    return deg_str or "N/A"

            for row in rows:
                entry = row.get("entry", {})
                p_id = entry.get("id", "")
                if p_id in name_map:
                    cells = row.get("cells", [])
                    if cells:
                        cell = cells[0]
                        pos = cell.get("position", {})
                        
                        # ── Use ecliptic longitude directly (matches AstronomyAPI website) ──
                        ecl = pos.get("ecliptic", {})
                        ecl_lon = ecl.get("longitude", {})
                        ecl_lat_obj = ecl.get("latitude", {})
                        
                        lon_deg_str = ecl_lon.get("degrees", None)
                        ecl_lat_str = ecl_lat_obj.get("degrees", "0")
                        
                        if lon_deg_str is not None:
                            longitude = float(lon_deg_str) % 360
                        else:
                            # Fallback: convert from RA/Dec
                            eq = pos.get("equatorial", {})
                            ra = eq.get("rightAscension", {})
                            ra_deg = float(ra.get("hours", 0.0)) * 15.0
                            dec = eq.get("declination", {})
                            dec_d = float(dec.get("degrees", 0.0))
                            longitude = equatorial_to_longitude(ra_deg, dec_d)
                        
                        deg = longitude % 30
                        sign_idx = int(longitude / 30) % 12
                        sign = signs_list[sign_idx]
                        lord = lord_map.get(sign, "N/A")
                        
                        # ── Equatorial coords for display ──
                        eq = pos.get("equatorial", {})
                        ra = eq.get("rightAscension", {})
                        ra_hours = float(ra.get("hours", 0.0))
                        ra_deg_val = (ra_hours * 15.0) % 360
                        dec_obj = eq.get("declination", {})
                        dec_str_raw = dec_obj.get("string", "N/A")
                        
                        # ── Horizontal coords ──
                        horiz = pos.get("horizontal", {})
                        alt_raw = horiz.get("altitude", {})
                        az_raw = horiz.get("azimuth", {})
                        alt_str = fmt_dms(alt_raw.get("degrees", ""), signed=True)
                        az_str  = fmt_dms(az_raw.get("degrees", ""),  signed=False)
                        
                        mapped.append({
                            "name": name_map[p_id],
                            "planet": name_map[p_id],
                            "longitude": longitude,
                            "degree": deg,
                            "is_retrograde": False,
                            "rasi": {"name": sign, "lord": {"name": lord}},
                            "right_ascension": f"{round(ra_deg_val, 2)}°",
                            "declination": dec_str_raw,
                            "latitude": ecl_lat_obj.get("string", "0.0°"),
                            "raw_longitude_str": f"{round(longitude, 2)}°",
                            "altitude": alt_str,
                            "azimuth": az_str,
                            "house": 1
                        })
            
            # ── True Lunar Nodes (standard formula from Julian Date) ──
            dt_i = parse_datetime_helper(dt)
            y0, m0, d0 = dt_i["year"], dt_i["month"], dt_i["day"]
            h0, mn0, s0 = dt_i["hour"], dt_i["min"], dt_i["sec"]
            tz0 = dt_i["tzone"]
            utc_h = h0 + mn0/60.0 + s0/3600.0 - tz0
            if m0 <= 2: y0 -= 1; m0 += 12
            A0 = int(y0/100); B0 = 2 - A0 + int(A0/4)
            jd = int(365.25*(y0+4716)) + int(30.6001*(m0+1)) + d0 + B0 - 1524.5 + utc_h/24.0
            T = (jd - 2451545.0) / 36525.0
            # True North Node (Rahu) tropical longitude
            rahu_trop = (125.04452 - 1934.136261*T + 0.0020708*T*T) % 360
            if rahu_trop < 0: rahu_trop += 360
            ketu_trop  = (rahu_trop + 180.0) % 360
            # Mean Node (Spashth) — slightly smoother motion
            spashth_rahu_trop = (125.04455 - 1934.13626197*T) % 360
            if spashth_rahu_trop < 0: spashth_rahu_trop += 360
            spashth_ketu_trop = (spashth_rahu_trop + 180.0) % 360
            
            # Sun position (tropical) for Earth computation
            sun_trop = 0.0
            for p in mapped:
                if p["planet"] == "Sun":
                    sun_trop = p.get("longitude", 0.0)
                    break
            earth_trop = (sun_trop + 180.0) % 360
            
            def make_node_entry(name, lon_trop):
                lon_trop = float(lon_trop) % 360
                si = int(lon_trop / 30) % 12
                sg = signs_list[si]
                ra_s, dec_s = longitude_to_equatorial(lon_trop)
                return {
                    "name": name, "planet": name,
                    "longitude": lon_trop,
                    "degree": lon_trop % 30,
                    "is_retrograde": True,
                    "rasi": {"name": sg, "lord": {"name": lord_map.get(sg, "N/A")}},
                    "right_ascension": ra_s, "declination": dec_s,
                    "latitude": "0° 00' 00\"",
                    "raw_longitude_str": f"{round(lon_trop, 2)}°",
                    "altitude": "N/A", "azimuth": "N/A", "house": 1
                }

            for name, lon in [
                ("True North Node", rahu_trop), ("True South Node", ketu_trop),
                ("Rahu", rahu_trop), ("Ketu", ketu_trop),
                ("Spashth Rahu", spashth_rahu_trop), ("Spashth Ketu", spashth_ketu_trop),
            ]:
                mapped.append(make_node_entry(name, lon))
            
            # Earth entry
            mapped.append(make_node_entry("Earth", earth_trop))
            mapped[-1]["is_retrograde"] = False

            # ── Accurate Ascendant (Lagna) using sidereal time ──
            asc_longitude = calculate_true_ascendant(dt, lat, lng)
            asc_deg_val = asc_longitude % 30
            asc_si = int(asc_longitude / 30) % 12
            asc_sign = signs_list[asc_si]
            asc_lord = lord_map.get(asc_sign, "N/A")
            asc_ra, asc_dec = longitude_to_equatorial(asc_longitude)
            
            mapped.append({
                "name": "Ascendant", "planet": "Ascendant",
                "longitude": asc_longitude, "degree": asc_deg_val,
                "is_retrograde": False,
                "rasi": {"name": asc_sign, "lord": {"name": asc_lord}},
                "right_ascension": asc_ra, "declination": asc_dec,
                "latitude": "0° 00' 00\"",
                "raw_longitude_str": f"{round(asc_longitude, 2)}°",
                "altitude": "N/A", "azimuth": "N/A", "house": 1
            })
            
            if mapped:
                return {
                    "status": "success",
                    "data": {"planetary_positions": mapped}
                }
    except Exception as e:
        print(f"[Backend] Error calling AstronomyAPI: {e}")
    return None



# Divine API Helper Functions
def fetch_divine_api(url, api_key, payload):
    import urllib.request
    import json
    
    token = DIVINE_ACCESS_TOKEN if DIVINE_ACCESS_TOKEN else api_key
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[Backend] Error calling Divine API {url}: {e}")
        if hasattr(e, 'read'):
            try:
                print(f"[Backend] Details: {e.read().decode('utf-8')}")
            except Exception:
                pass
        return None

def get_divine_planet_position(dt, lat, lng, ayanamsa='0'):
    dt_info = parse_datetime_helper(dt)
    payload = {
        "api_key": DIVINE_API_KEY,
        "day": dt_info["day"],
        "month": dt_info["month"],
        "year": dt_info["year"],
        "hour": dt_info["hour"],
        "min": dt_info["min"],
        "sec": dt_info["sec"],
        "gender": "male",
        "full_name": "User",
        "place": "City",
        "lat": float(lat),
        "lon": float(lng),
        "tzone": float(dt_info["tzone"]),
        "lan": "en",
        "house_system": "P"
    }
    
    url = "https://astroapi-4.divineapi.com/western-api/v1/planetary-positions"
    res = fetch_divine_api(url, DIVINE_API_KEY, payload)
    
    if res and res.get("success") == 1:
        raw_planets = res.get("data", {}).get("planets", {})
        mapped = []
        for key, p_data in raw_planets.items():
            name = p_data.get("name") or key.capitalize()
            lon = p_data.get("position", 0.0)
            deg = lon % 30
            is_retro = p_data.get("is_retrograde", False)
            sign = p_data.get("sign", "Aries")
            lord = p_data.get("signLord", "Mars")
            house = p_data.get("house", 1)
            
            mapped.append({
                "name": name,
                "planet": name,
                "longitude": lon,
                "degree": deg,
                "is_retrograde": is_retro,
                "rasi": {
                    "name": sign,
                    "lord": {
                        "name": lord
                    }
                },
                "house": house
            })
        return {
            "status": "success",
            "data": {
                "planetary_positions": mapped
            }
        }
    return None

def get_divine_horoscope(sign, dt):
    dt_info = parse_datetime_helper(dt)
    payload = {
        "api_key": DIVINE_API_KEY,
        "sign": sign.lower(),
        "h_day": "today",
        "tzone": float(dt_info["tzone"]),
        "lan": "en"
    }
    url = "https://astroapi-5.divineapi.com/api/v5/daily-horoscope"
    res = fetch_divine_api(url, DIVINE_API_KEY, payload)
    
    if res and res.get("success") == 1:
        pred = res.get("data", {}).get("prediction", {})
        personal = pred.get("personal", "Focus on self-reflection and balance today.")
        health = pred.get("health", "Take care of your health and stay active.")
        profession = pred.get("profession", "A good day to prioritize work.")
        emotions = pred.get("emotions", "Express yourself clearly in relationships.")
        
        full_pred = f"{personal} {health} {profession} {emotions}"
        
        return {
            "status": "success",
            "data": {
                "sign": sign.capitalize(),
                "date": time.strftime("%Y-%m-%d"),
                "prediction": full_pred,
                "areas": {
                    "personal": personal,
                    "health": health,
                    "profession": profession,
                    "relationship": emotions
                }
            }
        }
    return None

# Token cache variables
_access_token = None
_token_expiry = 0 # Unix timestamp of expiry

def get_access_token():
    global _access_token, _token_expiry
    
    if DEMO_MODE:
        return "demo_token"
        
    current_time = time.time()
    if _access_token and current_time < _token_expiry - 60:
        return _access_token
        
    print("[Backend] Fetching fresh OAuth2 access token from Prokerala API...")
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
            _access_token = res_data.get('access_token')
            expires_in = res_data.get('expires_in', 3600)
            _token_expiry = time.time() + expires_in
            print(f"[Backend] Token fetched successfully. Valid for {expires_in} seconds.")
            return _access_token
    except Exception as e:
        print(f"[Backend] Error fetching OAuth2 token: {e}")
        print("[Backend] Falling back to Demo Mode for this request.")
        return None

# Mock data generators for Demo Mode
def get_mock_horoscope(sign):
    sign_clean = sign.lower()
    horoscopes = {
        "aries": "Energy is high. Perfect for starting new initiatives. Channel your ambition.",
        "taurus": "Patience will be rewarded. Focus on long-term grounding and financial stability.",
        "gemini": "Communication channels are wide open. Share your ideas and collaborate.",
        "cancer": "A good day to nest, rest, and reflect. Prioritize self-care.",
        "leo": "You are in the spotlight. Radiate confidence, and support your team.",
        "virgo": "Organize your schedules and workspace. Clarity will follow order.",
        "libra": "Focus on balance. Nurture relationships and resolve outstanding disputes.",
        "scorpio": "Deep focus allows you to uncover hidden opportunities. Trust your gut.",
        "sagittarius": "Optimism abounds. Spread positivity and explore new educational goals.",
        "capricorn": "Professional accomplishments are highlighted. Stay disciplined and focused.",
        "aquarius": "Innovation is your strength today. Break out of standard routines.",
        "pisces": "Intuition is sharp. Listen to your inner voice and practice mindfulness."
    }
    
    prediction = horoscopes.get(sign_clean, "Stay centered and adapt to the flow of daily events.")
    
    return {
        "status": "success",
        "data": {
            "sign": sign.capitalize(),
            "date": time.strftime("%Y-%m-%d"),
            "prediction": prediction,
            "areas": {
                "personal": "Cosmic forces encourage self-reflection and establishing routines.",
                "health": "Incorporate dynamic stretching or outdoor walks into your schedule.",
                "profession": "Review tasks carefully. Precision is favored over speed.",
                "relationship": "Clear, gentle listening will strengthen your connections."
            }
        }
    }

def get_mock_panchang(datetime_str, lat, lng):
    return {
        "status": "success",
        "data": {
            "datetime": datetime_str,
            "coordinates": f"{lat},{lng}",
            "sunrise": "06:04:12 AM",
            "sunset": "07:11:45 PM",
            "moonrise": "04:32:10 PM",
            "moonset": "03:15:20 AM",
            "tithi": {
                "name": "Ekadashi (Shukla Paksha)",
                "end_time": "08:45 PM"
            },
            "nakshatra": {
                "name": "Chitra",
                "end_time": "11:20 PM"
            },
            "yoga": {
                "name": "Siddha",
                "end_time": "05:10 PM"
            },
            "karana": {
                "name": "Vanija",
                "end_time": "09:30 AM"
            },
            "auspicious_timings": [
                {"name": "Abhijit Muhurta", "start": "11:54 AM", "end": "12:46 PM"},
                {"name": "Amrit Kaal", "start": "06:20 PM", "end": "07:55 PM"}
            ],
            "inauspicious_timings": [
                {"name": "Rahu Kaal", "start": "01:30 PM", "end": "03:00 PM"},
                {"name": "Yamaganda Kaal", "start": "09:00 AM", "end": "10:30 AM"},
                {"name": "Gulika Kaal", "start": "12:00 PM", "end": "01:30 PM"}
            ]
        }
    }

def get_mock_kundli(datetime_str, lat, lng):
    return {
        "status": "success",
        "data": {
            "birth_details": {
                "datetime": datetime_str,
                "latitude": lat,
                "longitude": lng
            },
            "ascendant": {
                "name": "Scorpio",
                "lord": "Mars",
                "degree": 12.4,
                "description": "Intense, deep, magnetic, secretive, powerful, and highly analytical."
            },
            "moon_sign": {
                "name": "Taurus",
                "lord": "Venus",
                "degree": 8.5,
                "description": "Patient, artistic, emotionally stable, likes comfort, and values consistency."
            },
            "nakshatra": {
                "name": "Krittika",
                "lord": "Sun",
                "pada": 4,
                "description": "Connected to purifiers, strong energy, determination, and sharp intellect."
            },
            "planetary_positions": [
                {"planet": "Sun", "sign": "Taurus", "house": 7, "degree": 29.1},
                {"planet": "Moon", "sign": "Taurus", "house": 7, "degree": 8.5},
                {"planet": "Mars", "sign": "Pisces", "house": 5, "degree": 15.3},
                {"planet": "Mercury", "sign": "Gemini", "house": 8, "degree": 4.1},
                {"planet": "Jupiter", "sign": "Aquarius", "house": 4, "degree": 22.8},
                {"planet": "Venus", "sign": "Aries", "house": 6, "degree": 11.2},
                {"planet": "Saturn", "sign": "Capricorn", "house": 3, "degree": 6.4}
            ]
        }
    }

def get_mock_planet_position(datetime_str, lat, lng, ayanamsa='0'):
    import math
    from datetime import date
    
    dt_info = parse_datetime_helper(datetime_str)
    
    # Calculate days since Vernal Equinox (approx March 20, 2000) for position simulation
    try:
        d = date(dt_info["year"], dt_info["month"], dt_info["day"])
        vernal = date(dt_info["year"], 3, 20)
        diff_days = (d - vernal).days
    except:
        diff_days = 114 # fallback default
        
    # Sun's tropical longitude is highly accurate using (days * 360/365.25)
    sun_lon = (diff_days * 0.9856) % 360
    
    # Simulate planetary longitudes using real solar period approximations
    planets_raw = [
        ("Sun", sun_lon, False),
        ("Moon", (sun_lon + diff_days * 13.176) % 360, False),
        ("Mars", (diff_days * 0.524) % 360, (diff_days % 730 > 700)),
        ("Mercury", (sun_lon + 15.0 * math.sin(diff_days * 0.071)) % 360, (diff_days % 116 > 100)),
        ("Jupiter", (54.0 + diff_days * 0.083) % 360, False),
        ("Venus", (sun_lon + 40.0 * math.cos(diff_days * 0.011)) % 360, (diff_days % 584 > 570)),
        ("Saturn", (10.0 + diff_days * 0.033) % 360, False),
        ("Uranus", (45.0 + diff_days * 0.0117) % 360, False),
        ("Neptune", (3.0 + diff_days * 0.006) % 360, False),
        ("Pluto", (298.0 + diff_days * 0.004) % 360, False),
        ("True North Node", (335.0 - diff_days * 0.053) % 360, True),
        ("True South Node", (155.0 - diff_days * 0.053) % 360, True),
        # Rahu = True North Node (Vedic name), Ketu = True South Node (Vedic name)
        ("Rahu", (335.0 - diff_days * 0.053) % 360, True),
        ("Ketu", (155.0 - diff_days * 0.053) % 360, True),
        # Spashth Rahu = Mean North Node (approx 0.9° behind True), Spashth Ketu opposite
        ("Spashth Rahu", (335.9 - diff_days * 0.0529) % 360, True),
        ("Spashth Ketu", (155.9 - diff_days * 0.0529) % 360, True),
        # Earth = geocentric view (Sun + 180°, always on ecliptic)
        ("Earth", (sun_lon + 180.0) % 360, False)
    ]
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    
    positions = []
    for name, lon, is_retro in planets_raw:
        if ayanamsa == '1':
            lon = (lon - 24.0) % 360
        sign_idx = int(lon // 30)
        sign_name = signs[sign_idx]
        deg = lon % 30
        nak_idx = int(lon * 27 / 360)
        nak_name = nakshatras[nak_idx]
        house = int((lon // 30) + 1)
        positions.append({
            "planet": name,
            "sign": sign_name,
            "house": house,
            "longitude": round(lon, 2),
            "degree": round(deg, 2),
            "nakshatra": {"name": nak_name},
            "is_retrograde": is_retro
        })
        
    return {
        "status": "success",
        "data": {
            "planetary_positions": positions
        }
    }

def calculate_aspects(planetary_positions):
    aspects = []
    aspect_defs = [
        {"name": "Conjunction", "angle": 0, "orb_limit": 8, "type": "major"},
        {"name": "Semi-Sextile", "angle": 30, "orb_limit": 2, "type": "minor"},
        {"name": "Semi-Square", "angle": 45, "orb_limit": 2, "type": "minor"},
        {"name": "Sextile", "angle": 60, "orb_limit": 6, "type": "major"},
        {"name": "Quintile", "angle": 72, "orb_limit": 2, "type": "minor"},
        {"name": "Square", "angle": 90, "orb_limit": 8, "type": "major"},
        {"name": "Trine", "angle": 120, "orb_limit": 8, "type": "major"},
        {"name": "Sesquiquadrate", "angle": 135, "orb_limit": 2, "type": "minor"},
        {"name": "Quincunx", "angle": 150, "orb_limit": 2, "type": "minor"},
        {"name": "Opposition", "angle": 180, "orb_limit": 8, "type": "major"}
    ]
    
    for i in range(len(planetary_positions)):
        for j in range(i + 1, len(planetary_positions)):
            p1 = planetary_positions[i]
            p2 = planetary_positions[j]
            
            lon1 = p1.get("longitude")
            lon2 = p2.get("longitude")
            
            if lon1 is None or lon2 is None:
                continue
                
            diff = abs(lon1 - lon2) % 360
            if diff > 180:
                diff = 360 - diff
                
            for asp in aspect_defs:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb_limit"]:
                    aspects.append({
                        "planet_one": p1["planet"],
                        "planet_two": p2["planet"],
                        "aspect_name": asp["name"],
                        "type": asp["type"],
                        "angle": asp["angle"],
                        "exact_diff": round(diff, 2),
                        "orb": round(orb, 2)
                    })
    return aspects

def normalize_positions_helper(planets, provider, ayanamsa, dt, lat, lng):
    signs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    lord_map = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
        "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
        "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    
    # Let's ensure Ascendant / Lagna exists in planets
    has_asc = False
    sun_lon = 0.0
    for p in planets:
        p_name = p.get("name") or p.get("planet") or ""
        if p_name.lower() in ["ascendant", "lagna"]:
            has_asc = True
        if p_name.lower() == "sun" and p.get("longitude") is not None:
            sun_lon = float(p["longitude"])
            
    if not has_asc:
        asc_lon = calculate_true_ascendant(dt, lat, lng)
        asc_deg = asc_lon % 30
        
        asc_sign_idx = int(asc_lon / 30) % 12
        asc_sign = signs_list[asc_sign_idx]
        asc_lord = lord_map.get(asc_sign, "N/A")
        
        planets.append({
            "name": "Ascendant",
            "planet": "Ascendant",
            "longitude": asc_lon,
            "degree": asc_deg,
            "is_retrograde": False,
            "rasi": {
                "name": asc_sign,
                "lord": {
                    "name": asc_lord
                }
            },
            "house": 1
        })
        
    for p in planets:
        lon = p.get("longitude")
        p_name = p.get("name") or p.get("planet") or "Sun"
        if lon is not None:
            lon = float(lon)
            
            # 1. Normalize Display Ecliptic Longitude based on Ayanamsa setting
            # 1. Normalize Display Ecliptic Longitude based on Ayanamsa setting
            # Always store the raw tropical ecliptic longitude for chart plotting
            p["tropical_longitude"] = lon
            if provider in ['astronomyapi', 'divineapi', 'mock'] and ayanamsa == '1':
                display_lon = (lon - 24.23) % 360
                sign_idx = int(display_lon / 30) % 12
                p["rasi"] = {
                    "name": signs_list[sign_idx],
                    "lord": {
                        "name": lord_map[signs_list[sign_idx]],
                        "vedic_name": {"Sun": "Surya", "Moon": "Chandra", "Mars": "Mangala", "Mercury": "Budha", "Jupiter": "Guru", "Venus": "Shukra", "Saturn": "Shani"}.get(lord_map[signs_list[sign_idx]], "N/A")
                    }
                }
                p["degree"] = display_lon % 30
            else:
                display_lon = lon
                if p.get("rasi") and p["rasi"].get("lord") and not p["rasi"]["lord"].get("vedic_name"):
                    l_name = p["rasi"]["lord"].get("name")
                    p["rasi"]["lord"]["vedic_name"] = {"Sun": "Surya", "Moon": "Chandra", "Mars": "Mangala", "Mercury": "Budha", "Jupiter": "Guru", "Venus": "Shukra", "Saturn": "Shani"}.get(l_name, "N/A")
                
            p["longitude"] = display_lon
            p["raw_longitude_str"] = f"{round(display_lon, 2)}°"
            
            # 2. Calculate Nakshatra details (pada, lord, sub lord) from Sidereal longitude
            if ayanamsa == '1':
                sidereal_lon = display_lon
            else:
                sidereal_lon = (display_lon - 24.23) % 360
            nak_name, pada, nak_lord, sub_lord = get_nakshatra_details(sidereal_lon)
            p["nakshatra"] = nak_name
            p["padam"] = pada
            p["nakshatra_lord"] = nak_lord
            p["sub_lord"] = sub_lord
            
            # 3. Calculate Speed deg/day
            is_retro = p.get("is_retrograde", False) or p.get("isRetrograde", False)
            speed_val = get_planet_speed(p_name, is_retro)
            p["speed_deg_day"] = f"{speed_val:+.4f}°/day"
            
            # 4. Latitude / Shara
            lat_val = p.get("latitude")
            if lat_val is None:
                import math
                try:
                    dt_info = parse_datetime_helper(dt)
                    from datetime import date
                    d_obj = date(dt_info["year"], dt_info["month"], dt_info["day"])
                    vernal_obj = date(dt_info["year"], 3, 20)
                    diff_days = (d_obj - vernal_obj).days
                except:
                    diff_days = 114
                    
                if p_name == "Sun":
                    lat_deg = 0.0
                elif p_name == "Moon":
                    lat_deg = 5.15 * math.sin(diff_days * 0.23)
                else:
                    lat_deg = 1.5 * math.sin(diff_days * 0.05)
                    
                lat_sign = "+" if lat_deg >= 0 else "-"
                lat_abs = abs(lat_deg)
                lat_d = int(lat_abs)
                lat_m = int((lat_abs - lat_d) * 60)
                lat_s = int(((lat_abs - lat_d) * 60 - lat_m) * 60)
                p["latitude"] = f"{lat_sign}{lat_d:02d}° {lat_m:02d}' {lat_s:02d}\""
            
            # 5. Reconstruct/Ensure correct equatorial RA and Dec (always tropical)
            if not p.get("right_ascension") or not p.get("declination"):
                if provider in ['prokerala', 'divineapi'] and ayanamsa == '1':
                    tropical_lon = (lon + 24.23) % 360
                else:
                    tropical_lon = lon
                    
                ra_str, dec_str = longitude_to_equatorial(tropical_lon)
                p["right_ascension"] = ra_str
                p["declination"] = dec_str
                
            # 6. Calculate Horizontal Coordinates (Altitude / Azimuth)
            lat_val = p.get("latitude")
            ecl_lat_val = 0.0
            if lat_val:
                if isinstance(lat_val, (int, float)):
                    ecl_lat_val = float(lat_val)
                elif isinstance(lat_val, str):
                    try:
                        clean_lat = lat_val.replace('"', '').replace("'", '').replace('°', '')
                        parts = clean_lat.split()
                        sign = -1.0 if '-' in parts[0] else 1.0
                        d_val = abs(float(parts[0]))
                        m_val = float(parts[1]) if len(parts) > 1 else 0.0
                        s_val = float(parts[2]) if len(parts) > 2 else 0.0
                        ecl_lat_val = sign * (d_val + m_val/60.0 + s_val/3600.0)
                    except:
                        ecl_lat_val = 0.0
                        
            if provider in ['prokerala', 'divineapi'] and ayanamsa == '1':
                tropical_lon = (lon + 24.23) % 360
            else:
                tropical_lon = lon
                
            alt_str, az_str = calculate_horizontal_coords(tropical_lon, ecl_lat_val, dt, lat, lng)
            # Only overwrite altitude/azimuth if they haven't already been set by the API
            if not p.get("altitude"):
                p["altitude"] = alt_str
            if not p.get("azimuth"):
                p["azimuth"] = az_str
                
    # Reorder so Ascendant (Lagna) is always first
    planets_sorted = []
    asc_planet = None
    for p in planets:
        p_name = p.get("name") or p.get("planet") or ""
        if p_name.lower() in ["ascendant", "lagna"]:
            asc_planet = p
            break
    if asc_planet:
        planets_sorted.append(asc_planet)
    for p in planets:
        p_name = p.get("name") or p.get("planet") or ""
        if p_name.lower() not in ["ascendant", "lagna"]:
            planets_sorted.append(p)
            
    return planets_sorted

def get_mock_chart(dt, lat, lng, ayanamsa='0', custom_positions=None, style='default'):
    import math
    import hashlib
    
    data_res = get_mock_planet_position(dt, lat, lng, ayanamsa)
    if custom_positions:
        positions = custom_positions
    else:
        positions = data_res["data"]["planetary_positions"]
        
    symbols = {
        "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿",
        "Jupiter": "♃", "Venus": "♀", "Saturn": "♄", "Uranus": "♅",
        "Neptune": "♆", "Pluto": "♇",
        "True North Node": "☊", "True South Node": "☋",
        "Rahu": "☊", "Ketu": "☋",
        "Spashth Rahu": "☊", "Spashth Ketu": "☋",
        "Earth": "⊕"
    }
    colors = {
        "Sun": "#ffe600", "Moon": "#ffffff", "Mars": "#ff3333", "Mercury": "#33ff57",
        "Jupiter": "#ffb333", "Venus": "#ff33b3", "Saturn": "#e033ff", "Uranus": "#33e0ff",
        "Neptune": "#3357ff", "Pluto": "#999999",
        "True North Node": "#ff9944", "True South Node": "#ff9944",
        "Rahu": "#ff7700", "Ketu": "#ff7700",
        "Spashth Rahu": "#ffaa44", "Spashth Ketu": "#ffaa44",
        "Earth": "#44aaff"
    }
    
    asc_deg = 0.0
    for p_item in positions:
        p_name = p_item.get("planet") or p_item.get("name") or ""
        if p_name.lower() in ["ascendant", "lagna"]:
            # For chart rotation, use the longitude that matches the plotting mode
            if ayanamsa == '1':
                asc_deg = float(p_item.get("longitude", 0.0))
            else:
                asc_deg = float(p_item.get("tropical_longitude") or p_item.get("longitude", 0.0))
            break
            
    if asc_deg == 0.0:
        sun_lon = 0.0
        for p_item in positions:
            p_name = p_item.get("planet") or p_item.get("name") or ""
            if p_name.lower() == "sun" and p_item.get("longitude") is not None:
                sun_lon = float(p_item["longitude"])
                break
        dt_info = parse_datetime_helper(dt)
        time_hours = dt_info["hour"] + dt_info["min"]/60.0 + dt_info["sec"]/3600.0
        asc_deg = (sun_lon + (time_hours - 6.0) * 15.0) % 360
        
    if style == 'sky':
        rotation_offset = 0.0
    else:
        rotation_offset = 180.0 - asc_deg
    
    def get_rotated_rad(angle_deg):
        if style == 'sky':
            # East is 0, North is 90 (Top), West is 180 (Left), South is 270 (Bottom)
            # This is standard cartesian coordinate mapping (anticlockwise rotation)
            return math.radians((360 - angle_deg) % 360)
        else:
            return math.radians((angle_deg + rotation_offset) % 360)
        
    planets = []
    for p in positions:
        name = p.get("planet") or p.get("name", "")
        # Use sidereal longitude (matches table) for Vedic mode;
        # use tropical longitude for tropical mode
        if ayanamsa == '1':
            plot_lon = float(p.get("longitude", 0.0))
        else:
            plot_lon = float(p.get("tropical_longitude") or p.get("longitude", 0.0))
        planets.append((name, symbols.get(name, "?"), plot_lon, colors.get(name, "#ffffff")))
        
    seed_str = f"{dt or '2026-07-09T22:00:00+05:30'}_{lat or '19.076'}_{lng or '72.877'}"
    h = hashlib.sha256(seed_str.encode('utf-8')).digest()
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    planets.sort(key=lambda x: x[2])
    
    svg = f"""<svg viewBox="0 0 1000 1000" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Premium cosmic glow filters -->
    <filter id="glow-light" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    
    <!-- Gradients -->
    <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1b124a"/>
      <stop offset="60%" stop-color="#0a0521"/>
      <stop offset="100%" stop-color="#04020f"/>
    </radialGradient>
    <radialGradient id="centerGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0d0826" stop-opacity="1"/>
      <stop offset="70%" stop-color="#140d3b" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="#1e1354" stop-opacity="0.1"/>
    </radialGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffe600"/>
      <stop offset="50%" stop-color="#d4af37"/>
      <stop offset="100%" stop-color="#aa7c11"/>
    </linearGradient>
  </defs>
  
  <!-- Outer bounds and dark background -->
  <rect width="100%" height="100%" fill="url(#bgGrad)" rx="24"/>
  
  <!-- Star background dots -->
  <g fill="#ffffff" opacity="0.35">
    <circle cx="120" cy="150" r="1.5"/>
    <circle cx="840" cy="180" r="2"/>
    <circle cx="210" cy="780" r="1.2"/>
    <circle cx="780" cy="840" r="1.5"/>
    <circle cx="100" cy="540" r="2.2" opacity="0.5"/>
    <circle cx="900" cy="420" r="1.2"/>
    <circle cx="380" cy="110" r="1.5"/>
    <circle cx="620" cy="890" r="1.8"/>
  </g>
  
  <!-- Main outer wheel borders -->
  <circle cx="500" cy="500" r="460" stroke="url(#goldGrad)" stroke-width="4.5" fill="none" filter="url(#glow-light)"/>
  <circle cx="500" cy="500" r="420" stroke="#d4af37" stroke-width="2.5" fill="none" opacity="0.75"/>
  <circle cx="500" cy="500" r="380" stroke="#d4af37" stroke-width="1.8" fill="none" opacity="0.5"/>
  <circle cx="500" cy="500" r="300" stroke="#d4af37" stroke-width="1.5" fill="url(#centerGrad)" opacity="0.65"/>
"""
    if style == 'sky':
        svg += """
  <!-- Stylized Earth Globe at center -->
  <g filter="url(#glow-light)">
    <circle cx="500" cy="500" r="85" fill="#0d184a" stroke="#007aff" stroke-width="2" opacity="0.95"/>
    <ellipse cx="500" cy="500" rx="85" ry="30" fill="none" stroke="#007aff" stroke-width="1.0" opacity="0.4"/>
    <ellipse cx="500" cy="500" rx="85" ry="60" fill="none" stroke="#007aff" stroke-width="1.0" opacity="0.4"/>
    <ellipse cx="500" cy="500" rx="30" ry="85" fill="none" stroke="#007aff" stroke-width="1.0" opacity="0.4"/>
    <ellipse cx="500" cy="500" rx="60" ry="85" fill="none" stroke="#007aff" stroke-width="1.0" opacity="0.4"/>
    <line x1="415" y1="500" x2="585" y2="500" stroke="#007aff" stroke-width="1.5" opacity="0.6"/>
    <line x1="500" y1="415" x2="500" y2="585" stroke="#007aff" stroke-width="1.5" opacity="0.6"/>
    <!-- Asia/Europe -->
    <path d="M 470 435 Q 490 425 510 445 Q 520 435 530 455 Q 520 475 500 465 Z" fill="#ffe600" opacity="0.25"/>
    <!-- Africa -->
    <path d="M 490 480 Q 510 465 525 475 Q 520 515 505 525 Q 480 505 490 480 Z" fill="#ffe600" opacity="0.25"/>
    <!-- Americas -->
    <path d="M 435 455 Q 455 475 445 505 Q 435 535 450 555 Q 435 545 425 495 Z" fill="#ffe600" opacity="0.25"/>
    <circle cx="500" cy="500" r="85" fill="none" stroke="url(#goldGrad)" stroke-width="2" opacity="0.8"/>
  </g>
"""
    else:
        svg += '  <circle cx="500" cy="500" r="130" stroke="#d4af37" stroke-width="1.2" fill="none" opacity="0.3" stroke-dasharray="6,6"/>\n'
    
    svg += """
  
  <!-- Detailed 360 Degree Tick Marks -->
  <g stroke="#d4af37" opacity="0.65">
"""
    for d in range(360):
        theta = get_rotated_rad(d)
        if d % 10 == 0:
            r1 = 380
            r2 = 420
            stroke_w = 1.2
        elif d % 5 == 0:
            r1 = 388
            r2 = 415
            stroke_w = 0.8
        else:
            r1 = 394
            r2 = 410
            stroke_w = 0.4
            
        x1 = 500 + r1 * math.cos(theta)
        y1 = 500 + r1 * math.sin(theta)
        x2 = 500 + r2 * math.cos(theta)
        y2 = 500 + r2 * math.sin(theta)
        svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="{stroke_w}"/>\n'
        
        # Add labels for 10 and 20 degrees within each sign segment
        rel_deg = d % 30
        if rel_deg in [10, 20] and d % 10 == 0:
            lx = 500 + 363 * math.cos(theta)
            ly = 500 + 363 * math.sin(theta) + 3.5
            if style == 'sky':
                screen_d = (360 - d) % 360
                rot_deg = (screen_d + 90) % 360
            else:
                rot_deg = (d + rotation_offset + 90) % 360
            svg += f'    <text x="{lx:.1f}" y="{ly:.1f}" fill="#ffffff" font-size="9" font-family="Outfit" font-weight="600" opacity="0.75" text-anchor="middle" transform="rotate({rot_deg:.1f}, {lx:.1f}, {ly:.1f})">{rel_deg}</text>\n'

    svg += """  </g>
  
  <!-- Outer Zodiac Sign Sectors & Division Borders -->
  <g stroke="#d4af37" opacity="0.5">
"""
    for i in range(12):
        angle = get_rotated_rad(i * 30)
        x1 = 500 + 300 * math.cos(angle)
        y1 = 500 + 300 * math.sin(angle)
        x2 = 500 + 460 * math.cos(angle)
        y2 = 500 + 460 * math.sin(angle)
        svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="1.8"/>\n'
        
        lbl_angle = get_rotated_rad(i * 30 + 15)
        lx = 500 + 440 * math.cos(lbl_angle)
        ly = 500 + 440 * math.sin(lbl_angle) + 5
        if style == 'sky':
            screen_deg = (360 - (i * 30 + 15)) % 360
            rot_deg = (screen_deg + 90) % 360
        else:
            rot_deg = (i * 30 + 15 + rotation_offset + 90) % 360
        svg += f'    <text x="{lx:.1f}" y="{ly:.1f}" fill="#ffe600" font-size="13.5" font-family="Outfit" font-weight="900" letter-spacing="0.5" text-anchor="middle" transform="rotate({rot_deg:.1f}, {lx:.1f}, {ly:.1f})">{signs[i].upper()}</text>\n'

        # Clickable sector path button for magnifying
        a1 = get_rotated_rad(i * 30)
        a2 = get_rotated_rad((i + 1) * 30)
        x1_in = 500 + 300 * math.cos(a1)
        y1_in = 500 + 300 * math.sin(a1)
        x2_in = 500 + 300 * math.cos(a2)
        y2_in = 500 + 300 * math.sin(a2)
        x1_out = 500 + 460 * math.cos(a1)
        y1_out = 500 + 460 * math.sin(a1)
        x2_out = 500 + 460 * math.cos(a2)
        y2_out = 500 + 460 * math.sin(a2)
        if style == 'sky':
            path_d = f"M {x1_in:.1f} {y1_in:.1f} L {x1_out:.1f} {y1_out:.1f} A 460 460 0 0 0 {x2_out:.1f} {y2_out:.1f} L {x2_in:.1f} {y2_in:.1f} A 300 300 0 0 1 {x1_in:.1f} {y1_in:.1f} Z"
        else:
            path_d = f"M {x1_in:.1f} {y1_in:.1f} L {x1_out:.1f} {y1_out:.1f} A 460 460 0 0 1 {x2_out:.1f} {y2_out:.1f} L {x2_in:.1f} {y2_in:.1f} A 300 300 0 0 0 {x1_in:.1f} {y1_in:.1f} Z"
        svg += f'    <path class="zodiac-sector-btn" data-sign="{signs[i]}" d="{path_d}" fill="transparent" stroke="none" style="cursor: pointer; transition: fill 0.2s;" onmouseover="this.setAttribute(\'fill\', \'rgba(255,215,0,0.06)\')" onmouseout="this.setAttribute(\'fill\', \'transparent\')"/>\n'

    svg += "  </g>\n"
    
    # House boundaries (12 sectors) - skipped if style == 'sky'
    if style != 'sky':
        svg += '  <!-- House boundaries (12 sectors) -->\n  <g stroke="#ffffff" stroke-width="1.0" opacity="0.25" stroke-dasharray="3,4">\n'
        for i in range(12):
            angle_deg = 180 + i * 30
            angle = math.radians(angle_deg)
            x1 = 500 + 130 * math.cos(angle)
            y1 = 500 + 130 * math.sin(angle)
            x2 = 500 + 300 * math.cos(angle)
            y2 = 500 + 300 * math.sin(angle)
            svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" />\n'
            
            num_angle = math.radians(angle_deg + 15)
            nx = 500 + 220 * math.cos(num_angle)
            ny = 500 + 220 * math.sin(num_angle) + 5.5
            svg += f'    <text x="{nx:.1f}" y="{ny:.1f}" fill="#ffffff" font-size="12" font-family="Outfit" opacity="0.45" text-anchor="middle">{i+1}</text>\n'
        svg += '  </g>\n'

    # Dynamic Aspect Lines inside the inner house circle - skipped if style == 'sky'
    if style != 'sky':
        svg += '  <!-- Dynamic Aspect Lines inside the inner house circle -->\n  <g stroke-width="1.5" filter="url(#glow-light)">\n'
        mc_deg = (asc_deg - 90.0) % 360
        aspect_planets = planets.copy()
        aspect_planets.append(("Ascendant", "ASC", asc_deg, "#ffe600"))
        aspect_planets.append(("Midheaven", "MC", mc_deg, "#ffffff"))

        for i in range(len(aspect_planets)):
            for j in range(i + 1, len(aspect_planets)):
                p1_name, _, a1, _ = aspect_planets[i]
                p2_name, _, a2, _ = aspect_planets[j]
                diff = abs(a1 - a2) % 360
                if diff > 180:
                    diff = 360 - diff
                    
                color = None
                if abs(diff - 120) <= 10:
                    color = "#007aff"  # Trine (Blue)
                elif abs(diff - 180) <= 10:
                    color = "#ff3b30"  # Opposition (Red)
                elif abs(diff - 90) <= 10:
                    color = "#ff3b30"  # Square (Red)
                elif abs(diff - 60) <= 8:
                    color = "#007aff"  # Sextile (Blue)
                elif abs(diff - 150) <= 6:
                    color = "#34c759"  # Quincunx (Green)
                elif abs(diff - 30) <= 5:
                    color = "#a0aec0"  # Semisextile (Charcoal / Black equivalent)
                elif abs(diff - 135) <= 5:
                    color = "#a0aec0"  # Sesquiquadrate (Charcoal / Black equivalent)
                elif abs(diff - 45) <= 5:
                    color = "#a0aec0"  # Semisquare (Charcoal / Black equivalent)
                    
                if color:
                    r1 = get_rotated_rad(a1)
                    r2 = get_rotated_rad(a2)
                    x1 = 500 + 300 * math.cos(r1)
                    y1 = 500 + 300 * math.sin(r1)
                    x2 = 500 + 300 * math.cos(r2)
                    y2 = 500 + 300 * math.sin(r2)
                    signs_list = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
                    sign1 = signs_list[int(a1 // 30) % 12]
                    sign2 = signs_list[int(a2 // 30) % 12]
                    svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" opacity="0.65" class="pk-planet-aspect pk-zodiac-{sign1} pk-zodiac-{sign2}"/>\n'
        svg += '  </g>\n'

    svg += """  <!-- Planet placements & glyph indicators -->
  <g font-family="Outfit" text-anchor="middle">
"""
    for name, symbol, angle, color in planets:
        rad = get_rotated_rad(angle)
        ix1 = 500 + 300 * math.cos(rad)
        iy1 = 500 + 300 * math.sin(rad)
        ix2 = 500 + 355 * math.cos(rad)
        iy2 = 500 + 355 * math.sin(rad)
        svg += f'    <line x1="{ix1:.1f}" y1="{iy1:.1f}" x2="{ix2:.1f}" y2="{iy2:.1f}" stroke="#d4af37" stroke-width="0.8" stroke-dasharray="2,2" opacity="0.5"/>\n'
        
        px = 500 + 336 * math.cos(rad)
        py = 500 + 336 * math.sin(rad) + 6.5
        
        # Circle backing
        svg += f'    <circle cx="{px:.1f}" cy="{py-6.5:.1f}" r="16.5" fill="#06020c" stroke="{color}" stroke-width="1.5" opacity="0.95" filter="url(#glow-light)"/>\n'
        # Symbol
        svg += f'    <text class="svg-planet-marker" data-name="{name}" data-symbol="{symbol}" data-longitude="{angle}" data-color="{color}" x="{px:.1f}" y="{py:.1f}" fill="{color}" font-size="20" font-weight="bold">{symbol}</text>\n'
        
        # Text degree label - Full Degree for sky style, Sign-relative for others
        dx = 500 + 312 * math.cos(rad)
        dy = 500 + 312 * math.sin(rad) + 3.5
        if style == 'sky':
            # Show full 0-360 degree with minutes
            deg_total = angle % 360
            deg_num = int(deg_total)
            minutes_num = int((deg_total - deg_num) * 60)
        else:
            deg_within_sign = angle % 30
            deg_num = int(deg_within_sign)
            minutes_num = int((deg_within_sign - deg_num) * 60)
        svg += f'    <text x="{dx:.1f}" y="{dy:.1f}" fill="#ffffff" font-size="9.5" font-family="Outfit" font-weight="700" text-anchor="middle">{deg_num}°{minutes_num:02d}\'</text>\n'

    # Fixed ASC, DSC, MC, IC Marker Axes
    asc_rad_val = math.pi
    dsc_rad_val = 0.0
    mc_rad_val = -math.pi/2
    ic_rad_val = math.pi/2
    
    svg += "  </g>\n"
    
    # ASC, DSC, MC, IC Marker Axes - skipped if style == 'sky'
    if style != 'sky':
        svg += '  <!-- ASC, DSC, MC, IC Marker Axes -->\n  <g stroke="#ffffff" stroke-width="1.2" opacity="0.75">\n'
        # ASC line (300 to 380 radius)
        asc_x1 = 500 + 300 * math.cos(asc_rad_val)
        asc_y1 = 500 + 300 * math.sin(asc_rad_val)
        asc_x2 = 500 + 380 * math.cos(asc_rad_val)
        asc_y2 = 500 + 380 * math.sin(asc_rad_val)
        svg += f'    <line x1="{asc_x1:.1f}" y1="{asc_y1:.1f}" x2="{asc_x2:.1f}" y2="{asc_y2:.1f}" stroke-width="2.5" stroke="#ffe600" />\n'

        # DSC line (300 to 380 radius)
        dsc_x1 = 500 + 300 * math.cos(dsc_rad_val)
        dsc_y1 = 500 + 300 * math.sin(dsc_rad_val)
        dsc_x2 = 500 + 380 * math.cos(dsc_rad_val)
        dsc_y2 = 500 + 380 * math.sin(dsc_rad_val)
        svg += f'    <line x1="{dsc_x1:.1f}" y1="{dsc_y1:.1f}" x2="{dsc_x2:.1f}" y2="{dsc_y2:.1f}" stroke-width="2.5" stroke="#ffe600" />\n'

        # MC line (300 to 380 radius)
        mc_x1 = 500 + 300 * math.cos(mc_rad_val)
        mc_y1 = 500 + 300 * math.sin(mc_rad_val)
        mc_x2 = 500 + 380 * math.cos(mc_rad_val)
        mc_y2 = 500 + 380 * math.sin(mc_rad_val)
        svg += f'    <line x1="{mc_x1:.1f}" y1="{mc_y1:.1f}" x2="{mc_x2:.1f}" y2="{mc_y2:.1f}" stroke-width="2.0" stroke="#ffffff" />\n'

        # IC line (300 to 380 radius)
        ic_x1 = 500 + 300 * math.cos(ic_rad_val)
        ic_y1 = 500 + 300 * math.sin(ic_rad_val)
        ic_x2 = 500 + 380 * math.cos(ic_rad_val)
        ic_y2 = 500 + 380 * math.sin(ic_rad_val)
        svg += f'    <line x1="{ic_x1:.1f}" y1="{ic_y1:.1f}" x2="{ic_x2:.1f}" y2="{ic_y2:.1f}" stroke-width="2.0" stroke="#ffffff" />\n'
        svg += '  </g>\n'

    # Direction Labels or Axis Labels depending on style
    svg += '  <g>'
    if style == 'sky':
        def draw_direction_label(rad, eng_text, vedic_text, offset_dist):
            tx = 500 + offset_dist * math.cos(rad)
            ty = 500 + offset_dist * math.sin(rad)
            return f"""
    <circle cx="{tx:.1f}" cy="{ty:.1f}" r="22" fill="#04020f" stroke="#ffe600" stroke-width="1.8" filter="url(#glow-light)" />
    <text x="{tx:.1f}" y="{ty-3.5:.1f}" fill="#ffe600" font-family="Outfit" font-size="9" font-weight="900" text-anchor="middle">{eng_text}</text>
    <text x="{tx:.1f}" y="{ty+9:.1f}" fill="#ffffff" font-family="Outfit" font-size="9" font-weight="600" opacity="0.85" text-anchor="middle">{vedic_text}</text>
"""
        svg += draw_direction_label(asc_rad_val, "WEST", "पश्चिम", 478)
        svg += draw_direction_label(dsc_rad_val, "EAST", "पूर्व", 478)
        svg += draw_direction_label(mc_rad_val, "NORTH", "उत्तर", 478)
        svg += draw_direction_label(ic_rad_val, "SOUTH", "दक्षिण", 478)
    else:
        def draw_axis_label(rad, text, offset_dist):
            tx = 500 + offset_dist * math.cos(rad)
            ty = 500 + offset_dist * math.sin(rad)
            return f"""
    <rect x="{tx-16:.1f}" y="{ty-16:.1f}" width="32" height="32" rx="6" fill="#04020f" stroke="#ffe600" stroke-width="1.8" filter="url(#glow-light)" />
    <text x="{tx:.1f}" y="{ty+5.5:.1f}" fill="#ffe600" font-family="Outfit" font-size="12" font-weight="900" text-anchor="middle">{text}</text>
"""
        svg += draw_axis_label(asc_rad_val, "ASC", 302)
        svg += draw_axis_label(dsc_rad_val, "DSC", 302)
        svg += draw_axis_label(mc_rad_val, "MC", 302)
        svg += draw_axis_label(ic_rad_val, "IC", 302)

    display_date = "July 10, 2026"
    display_time = "12:01 AM"
    try:
        parts = dt.split('T')
        display_date = parts[0]
        if len(parts) > 1:
            display_time = format_time_short(dt)
    except:
        pass
        
    svg += f"""  </g>
  
  <g fill="#ffffff" font-family="Outfit" font-size="11" text-anchor="middle" opacity="0.9">
    <text x="500" y="492" fill="#ffe600" font-size="13" font-weight="900" letter-spacing="1">COSMIC ALIGNMENT</text>
    <text x="500" y="512" font-weight="600">{display_date}  {display_time}</text>
    <text x="500" y="527" font-size="9.5" opacity="0.6">LAT: {lat}  LNG: {lng}</text>
  </g>
</svg>"""
    return {
        "status": "success",
        "data": {
            "svg": svg
        }
    }

def get_mock_mangal_dosha(datetime_str, lat, lng):
    has_dosha = False
    try:
        minutes = int(datetime_str.split(":")[1][:2])
        has_dosha = (minutes % 2 == 0)
    except:
        pass
        
    if has_dosha:
        description = "Partial Mangal Dosha (Anshik) is present. Mars lies in your 12th house, signifying high passion, but potential emotional flares if unchanneled. Use routine fitness and deep breathing as remediations."
    else:
        description = "No Mangal Dosha is present in your chart. Your Mars alignment is balanced, facilitating steady actions, persistence, and logical temperament."
        
    return {
        "status": "success",
        "data": {
            "has_mangal_dosha": has_dosha,
            "type": "Anshik" if has_dosha else "None",
            "description": description,
            "remedy": "Engage in charitable activities, perform physical sport regularly, and start your morning with a 5-minute breathing layout." if has_dosha else "Your energy is well-integrated. No remedies needed."
        }
    }

def get_mock_kundli_matching(girl_dob, boy_dob):
    try:
        sum_chars = sum(ord(c) for c in (girl_dob + boy_dob))
        score = 16 + (sum_chars % 19)
    except:
        score = 25
        
    verdict = "Excellent Match" if score >= 25 else "Average Match" if score >= 18 else "Low Compatibility"
    
    return {
        "status": "success",
        "data": {
            "score": score,
            "max_score": 36,
            "verdict": verdict,
            "guna_details": {
                "Varna (Ego / Work)": f"{1 if score % 2 == 0 else 0}/1",
                "Vashya (Control)": f"{2 if score % 3 == 0 else 1}/2",
                "Tara (Destiny)": f"{1.5 if score % 4 == 0 else 3}/3",
                "Yoni (Physical Attraction)": f"{3 if score % 5 == 0 else 4}/4",
                 "Graha Maitri (Friendship)": f"{4 if score % 2 == 0 else 5}/5",
                "Gana (Temperament)": f"{5 if score % 3 == 0 else 6}/6",
                "Bhakoot (Emotional Harmony)": f"{7 if score % 5 != 0 else 0}/7",
                "Nadi (Physical Health compatibility)": f"{8 if score % 4 != 0 else 0}/8"
            },
            "alignment_advice": "This combination holds constructive potential. Active collaboration and alignment exercises will ensure long-term stability and mutual prosperity."
        }
    }

# --- Prokerala Astrology API Adapters ---

RASHI_MAP = {
    "Mesha": "Aries",
    "Vrishabha": "Taurus",
    "Mithuna": "Gemini",
    "Karka": "Cancer",
    "Simha": "Leo",
    "Kanya": "Virgo",
    "Tula": "Libra",
    "Vrischika": "Scorpio",
    "Dhanu": "Sagittarius",
    "Makara": "Capricorn",
    "Kumbha": "Aquarius",
    "Meena": "Pisces"
}

SIGN_DESCRIPTIONS = {
    "Aries": "Energetic, pioneering, emotionally active, and enjoys taking challenges head-on.",
    "Taurus": "Grounded, reliable, patient, aesthetic, and values stability and comfort.",
    "Gemini": "Curious, versatile, expressive, intellectual, and loves to communicate ideas.",
    "Cancer": "Nurturing, intuitive, protective, emotionally sensitive, and highly family-oriented.",
    "Leo": "Natural leader, expressive, proud, courageous, creative, and seeking acknowledgment.",
    "Virgo": "Analytical, meticulous, organized, helpful, and dedicated to continuous improvement.",
    "Libra": "Harmonious, diplomatic, aesthetic, relationship-focused, and seeks balance and fairness.",
    "Scorpio": "Intense, passionate, intuitive, transformative, and possesses powerful willpower.",
    "Sagittarius": "Optimistic, adventurous, philosophical, freedom-loving, and seeks broad truth.",
    "Capricorn": "Disciplined, ambitious, practical, organized, and focused on long-term achievement.",
    "Aquarius": "Innovative, humanitarian, independent, progressive, and values community/friendship.",
    "Pisces": "Compassionate, intuitive, artistic, spiritual, and highly empathetic to others."
}

def format_time_ampm(iso_str):
    if not iso_str:
        return "N/A"
    try:
        parts = iso_str.split('T')
        if len(parts) < 2:
            return iso_str
        time_part = parts[1]
        for char in ['+', '-']:
            if char in time_part:
                time_part = time_part.split(char)[0]
        hms = time_part.split(':')
        h = int(hms[0])
        m = int(hms[1])
        s = int(hms[2].split('.')[0]) if len(hms) > 2 else 0
        ampm = "AM" if h < 12 else "PM"
        h_formatted = h % 12
        if h_formatted == 0:
            h_formatted = 12
        return f"{h_formatted:02d}:{m:02d}:{s:02d} {ampm}"
    except Exception:
        return iso_str

def format_time_short(iso_str):
    if not iso_str:
        return "N/A"
    try:
        parts = iso_str.split('T')
        if len(parts) < 2:
            return iso_str
        time_part = parts[1]
        for char in ['+', '-']:
            if char in time_part:
                time_part = time_part.split(char)[0]
        hms = time_part.split(':')
        h = int(hms[0])
        m = int(hms[1])
        ampm = "AM" if h < 12 else "PM"
        h_formatted = h % 12
        if h_formatted == 0:
            h_formatted = 12
        return f"{h_formatted:02d}:{m:02d} {ampm}"
    except Exception:
        return iso_str

def fetch_raw_api(url, token):
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[Backend] Error calling raw API {url}: {e}")
        return None

def map_horoscope_data(raw_data, sign):
    daily_pred = raw_data.get("daily_prediction", {})
    sign_name = daily_pred.get("sign_name", sign.capitalize())
    date = daily_pred.get("date", time.strftime("%Y-%m-%d"))
    prediction = daily_pred.get("prediction", "")
    
    sentences = [s.strip() for s in prediction.split('.') if s.strip()]
    personal = sentences[0] + "." if len(sentences) > 0 else "Focus on self-reflection and establishing steady habits today."
    health = sentences[1] + "." if len(sentences) > 1 else "Ground yourself. Take a walk in nature to release mental tension."
    profession = sentences[2] + "." if len(sentences) > 2 else "A good day to reorganize your workspace and career priorities."
    relationship = sentences[3] + "." if len(sentences) > 3 else "Speak from the heart. Compassion will solve any minor disputes."
    
    return {
        "sign": sign_name,
        "date": date,
        "prediction": prediction,
        "areas": {
            "personal": personal,
            "health": health,
            "profession": profession,
            "relationship": relationship
        }
    }

def map_kundli_data(kundli_raw, planet_positions_raw):
    nak_details = kundli_raw.get("nakshatra_details", {})
    nak_info = nak_details.get("nakshatra", {})
    nak_lord = nak_info.get("lord", {})
    
    nakshatra_mapped = {
        "name": nak_info.get("name", "N/A"),
        "lord": nak_lord.get("name", "N/A"),
        "pada": nak_info.get("pada", 1),
        "description": f"Associated with characteristics of {nak_info.get('name', 'N/A')} Nakshatra."
    }
    
    chandra_rasi = nak_details.get("chandra_rasi", {})
    chandra_rasi_lord = chandra_rasi.get("lord", {})
    chandra_rasi_name = chandra_rasi.get("name", "N/A")
    chandra_rasi_english = RASHI_MAP.get(chandra_rasi_name, chandra_rasi_name)
    
    moon_degree = 0.0
    planets = planet_positions_raw.get("planet_position", [])
    for p in planets:
        if p.get("name") == "Moon":
            moon_degree = p.get("degree", 0.0)
            break
            
    moon_sign_mapped = {
        "name": chandra_rasi_english,
        "lord": chandra_rasi_lord.get("name", "N/A"),
        "degree": moon_degree,
        "description": SIGN_DESCRIPTIONS.get(chandra_rasi_english, "Emotionally active and sensitive.")
    }
    
    asc_name_english = "Leo"
    asc_lord_name = "Sun"
    asc_degree = 15.0
    for p in planets:
        if p.get("name") == "Ascendant":
            rasi_name = p.get("rasi", {}).get("name", "")
            asc_name_english = RASHI_MAP.get(rasi_name, rasi_name)
            asc_lord_name = p.get("rasi", {}).get("lord", {}).get("name", "N/A")
            asc_degree = p.get("degree", 0.0)
            break
            
    ascendant_mapped = {
        "name": asc_name_english,
        "lord": asc_lord_name,
        "degree": asc_degree,
        "description": SIGN_DESCRIPTIONS.get(asc_name_english, "Natural leader, expressive and proud.")
    }
    
    planetary_positions_mapped = []
    for p in planets:
        p_name = p.get("name")
        if p_name == "Ascendant":
            continue
        p_rasi_name = p.get("rasi", {}).get("name", "")
        p_rasi_english = RASHI_MAP.get(p_rasi_name, p_rasi_name)
        planetary_positions_mapped.append({
            "planet": p_name,
            "sign": p_rasi_english,
            "house": p.get("position", 1),
            "degree": p.get("degree", 0.0)
        })
        
    return {
        "ascendant": ascendant_mapped,
        "moon_sign": moon_sign_mapped,
        "nakshatra": nakshatra_mapped,
        "planetary_positions": planetary_positions_mapped
    }

def map_mangal_data(mangal_raw):
    has_dosha = mangal_raw.get("has_dosha", False)
    desc = mangal_raw.get("description", "Not Manglik")
    remedy = "Practice daily grounding, meditate for 10 minutes, and channel any excess physical energy into positive habits." if has_dosha else "Maintain your current active physical routine to keep energy channels balanced."
    
    return {
        "has_mangal_dosha": has_dosha,
        "type": mangal_raw.get("dosha_type") or ("Anshik (Partial)" if has_dosha else "None"),
        "description": desc + (" This indicates that Mars is positioned in a house that can lead to high energy levels or emotional blockages." if has_dosha else ""),
        "remedy": remedy
    }

def map_matching_data(matching_raw):
    guna_milan = matching_raw.get("guna_milan", {})
    score = guna_milan.get("total_points", 0.0)
    max_score = guna_milan.get("maximum_points", 36.0)
    
    if score >= 25:
        verdict = "Excellent Match"
    elif score >= 18:
        verdict = "Average Match"
    else:
        verdict = "Low Compatibility"
        
    guna_details = {}
    gunas_list = guna_milan.get("guna", [])
    for g in gunas_list:
        name = g.get("name", "Guna")
        obtained = g.get("obtained_points", 0.0)
        maximum = g.get("maximum_points", 0.0)
        obs_str = f"{int(obtained)}" if obtained.is_integer() else f"{obtained}"
        max_str = f"{int(maximum)}" if maximum.is_integer() else f"{maximum}"
        guna_details[name] = f"{obs_str}/{max_str}"
        
    message = matching_raw.get("message", {})
    alignment_advice = message.get("description", "This relationship holds high potential. Clear communication and regular mutual alignment check-ins will help sustain long-term synergy.")
    
    return {
        "score": score,
        "max_score": max_score,
        "verdict": verdict,
        "guna_details": guna_details,
        "alignment_advice": alignment_advice
    }

def map_panchang_data(panchang_raw, dt, lat, lng):
    tithis = panchang_raw.get("tithi", [])
    nakshatras = panchang_raw.get("nakshatra", [])
    yogas = panchang_raw.get("yoga", [])
    karanas = panchang_raw.get("karana", [])
    
    tithi_name = tithis[0].get("name", "N/A") if tithis else "N/A"
    nakshatra_name = nakshatras[0].get("name", "N/A") if nakshatras else "N/A"
    yoga_name = yogas[0].get("name", "N/A") if yogas else "N/A"
    karana_name = karanas[0].get("name", "N/A") if karanas else "N/A"
    
    tithi_end = format_time_short(tithis[0].get("end")) if tithis else "N/A"
    nakshatra_end = format_time_short(nakshatras[0].get("end")) if nakshatras else "N/A"
    yoga_end = format_time_short(yogas[0].get("end")) if yogas else "N/A"
    karana_end = format_time_short(karanas[0].get("end")) if karanas else "N/A"
    
    auspicious_timings = []
    for p in panchang_raw.get("auspicious_period", []):
        name = p.get("name")
        for slot in p.get("period", []):
            auspicious_timings.append({
                "name": name,
                "start": format_time_short(slot.get("start")),
                "end": format_time_short(slot.get("end"))
            })
            
    inauspicious_timings = []
    for p in panchang_raw.get("inauspicious_period", []):
        name = p.get("name")
        for slot in p.get("period", []):
            inauspicious_timings.append({
                "name": name,
                "start": format_time_short(slot.get("start")),
                "end": format_time_short(slot.get("end"))
            })
            
    return {
        "datetime": dt,
        "coordinates": f"{lat},{lng}",
        "sunrise": format_time_ampm(panchang_raw.get("sunrise")),
        "sunset": format_time_ampm(panchang_raw.get("sunset")),
        "moonrise": format_time_ampm(panchang_raw.get("moonrise")),
        "moonset": format_time_ampm(panchang_raw.get("moonset")),
        "tithi": {
            "name": tithi_name,
            "end_time": tithi_end
        },
        "nakshatra": {
            "name": nakshatra_name,
            "end_time": nakshatra_end
        },
        "yoga": {
            "name": yoga_name,
            "end_time": yoga_end
        },
        "karana": {
            "name": karana_name,
            "end_time": karana_end
        },
        "auspicious_timings": auspicious_timings,
        "inauspicious_timings": inauspicious_timings
    }

_timezone_cache = {}

def get_timezone_offset(lat, lng):
    if not lat or not lng:
        return "+05:30"
    
    try:
        cache_key = f"{round(float(lat), 2)}_{round(float(lng), 2)}"
    except Exception:
        cache_key = f"{lat}_{lng}"
        
    global _timezone_cache
    if cache_key in _timezone_cache:
        return _timezone_cache[cache_key]
        
    url = f"https://timeapi.io/api/TimeZone/coordinate?latitude={lat}&longitude={lng}"
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            offset_obj = data.get("currentUtcOffset") or data.get("standardUtcOffset")
            if isinstance(offset_obj, dict):
                total_seconds = offset_obj.get("seconds", 0)
                sign = "+" if total_seconds >= 0 else "-"
                abs_seconds = abs(total_seconds)
                hours = abs_seconds // 3600
                minutes = (abs_seconds % 3600) // 60
                offset = f"{sign}{hours:02d}:{minutes:02d}"
                _timezone_cache[cache_key] = offset
                return offset
    except Exception as e:
        print(f"[Backend] Error fetching timezone offset from TimeAPI: {e}")
    
    # Fallback to geographical longitude estimation
    try:
        hours = float(lng) / 15.0
        h_part = int(hours)
        m_part = int(abs(hours - h_part) * 60)
        sign = "+" if hours >= 0 else "-"
        offset = f"{sign}{abs(h_part):02d}:{m_part:02d}"
        _timezone_cache[cache_key] = offset
        return offset
    except Exception:
        return "+05:30"

def adjust_datetime_timezone(dt_str, lat, lng):
    if not dt_str:
        return dt_str
    if len(dt_str) >= 19:
        local_part = dt_str[:19]
        offset = get_timezone_offset(lat, lng)
        return f"{local_part}{offset}"
    return dt_str

class DashboardProxyHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        sys.stderr.write(f"[Dashboard Server] {format % args}\n")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if path.startswith('/api/'):
            self.handle_api_request(path, query_params)
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            params = {}
            if self.headers.get('Content-Type') == 'application/json':
                try:
                    params = json.loads(post_data)
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            else:
                params = urllib.parse.parse_qs(post_data)
                params = {k: v[0] for k, v in params.items()}
                
            self.handle_api_request(path, params)
        else:
            self.send_error(404, "Not Found")

    def handle_api_request(self, path, params):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_data = {}
        
        if path == '/api/config':
            response_data = {
                "configured": not DEMO_MODE or bool(ASTRONOMY_APP_ID) or bool(DIVINE_API_KEY),
                "demo_mode": DEMO_MODE and not bool(ASTRONOMY_APP_ID) and not bool(DIVINE_API_KEY),
                "client_id_configured": bool(CLIENT_ID),
                "astronomy_api_configured": bool(ASTRONOMY_APP_ID),
                "divine_api_configured": bool(DIVINE_API_KEY)
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        def get_param(name, default=""):
            val = params.get(name)
            if isinstance(val, list) and len(val) > 0:
                return val[0]
            elif val is not None:
                return val
            return default

        la = get_param('la', 'en')
        provider = get_param('provider', 'prokerala')

        # 1. Daily Horoscope
        if path == '/api/horoscope/daily':
            sign = get_param('sign', 'aries')
            if provider == 'astronomyapi':
                response_data = get_mock_horoscope(sign)
                if response_data and "data" in response_data:
                    old_pred = response_data["data"].get("prediction", "")
                    response_data["data"]["prediction"] = f"[AstronomyAPI Mode - Showing Estimated Forecast / AstronomyAPI मोड - अनुमानित फलादेश] {old_pred}"
            elif provider == 'divineapi' and DIVINE_API_KEY:
                dt = get_param('datetime', time.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
                response_data = get_divine_horoscope(sign, dt)
            else:
                if DEMO_MODE:
                    response_data = get_mock_horoscope(sign)
                else:
                    token = get_access_token()
                    if not token:
                        response_data = get_mock_horoscope(sign)
                    else:
                        dt = get_param('datetime', time.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
                        api_url = f"https://api.prokerala.com/v2/horoscope/daily?sign={sign}&datetime={urllib.parse.quote(dt)}&la={la}"
                        raw_res = fetch_raw_api(api_url, token)
                        if raw_res and raw_res.get("status") == "ok":
                            response_data = {
                                "status": "success",
                                "data": map_horoscope_data(raw_res.get("data", {}), sign)
                            }
                        else:
                            response_data = get_mock_horoscope(sign)
                    
        # 2. Panchang
        elif path == '/api/astrology/panchang':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            dt = adjust_datetime_timezone(dt, lat, lng)
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_panchang(dt or "2026-07-09T06:00:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_panchang(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/panchang/advanced?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la={la}"
                    raw_res = fetch_raw_api(api_url, token)
                    if raw_res and raw_res.get("status") == "ok":
                        response_data = {
                            "status": "success",
                            "data": map_panchang_data(raw_res.get("data", {}), dt, lat, lng)
                        }
                    else:
                        response_data = get_mock_panchang(dt, lat, lng)

        # 3. Kundli
        elif path == '/api/astrology/kundli':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            dt = adjust_datetime_timezone(dt, lat, lng)
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_kundli(dt or "1995-05-15T08:30:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_kundli(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    kundli_url = f"https://api.prokerala.com/v2/astrology/kundli?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la={la}"
                    planet_url = f"https://api.prokerala.com/v2/astrology/planet-position?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la={la}"
                    
                    kundli_res = fetch_raw_api(kundli_url, token)
                    planet_res = fetch_raw_api(planet_url, token)
                    
                    if kundli_res and planet_res and kundli_res.get("status") == "ok" and planet_res.get("status") == "ok":
                        response_data = {
                            "status": "success",
                            "data": map_kundli_data(kundli_res.get("data", {}), planet_res.get("data", {}))
                        }
                    else:
                        response_data = get_mock_kundli(dt, lat, lng)
                    
        # 4. Mangal Dosha
        elif path == '/api/astrology/mangal-dosha':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            dt = adjust_datetime_timezone(dt, lat, lng)
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_mangal_dosha(dt or "1995-05-15T08:30:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_mangal_dosha(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/mangal-dosha?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la={la}"
                    raw_res = fetch_raw_api(api_url, token)
                    if raw_res and raw_res.get("status") == "ok":
                        response_data = {
                            "status": "success",
                            "data": map_mangal_data(raw_res.get("data", {}))
                        }
                    else:
                        response_data = get_mock_mangal_dosha(dt, lat, lng)
                    
        # 5. Kundli Matching
        elif path == '/api/astrology/kundli-matching':
            g_dob = get_param('girl_dob')
            g_lat = get_param('girl_latitude')
            g_lng = get_param('girl_longitude')
            b_dob = get_param('boy_dob')
            b_lat = get_param('boy_latitude') or get_param('boy_coordinates')
            b_lng = get_param('boy_longitude')
            
            g_dob = adjust_datetime_timezone(g_dob, g_lat, g_lng)
            b_dob = adjust_datetime_timezone(b_dob, b_lat, b_lng)
            
            if DEMO_MODE or not g_dob or not b_dob or not g_lat or not b_lat:
                response_data = get_mock_kundli_matching(g_dob or "1996-08-20T10:15:00+05:30", b_dob or "1994-12-05T14:45:00+05:30")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_kundli_matching(g_dob, b_dob)
                else:
                    g_coords = f"{g_lat},{g_lng}"
                    b_coords = f"{b_lat},{b_lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/kundli-matching/advanced?girl_dob={urllib.parse.quote(g_dob)}&girl_coordinates={urllib.parse.quote(g_coords)}&boy_dob={urllib.parse.quote(b_dob)}&boy_coordinates={urllib.parse.quote(b_coords)}&ayanamsa=1&la={la}"
                    raw_res = fetch_raw_api(api_url, token)
                    if raw_res and raw_res.get("status") == "ok":
                        response_data = {
                            "status": "success",
                            "data": map_matching_data(raw_res.get("data", {}))
                        }
                    else:
                        response_data = get_mock_kundli_matching(g_dob, b_dob)
                    
        # 6. Planet Positions
        elif path == '/api/astrology/planet-position':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            ayanamsa = get_param('ayanamsa', '0')
            dt = adjust_datetime_timezone(dt, lat, lng)
            
            response_data = None
            if provider == 'astronomyapi' and dt and lat and lng:
                response_data = get_astronomy_planet_position(dt, lat, lng)
            elif provider == 'divineapi' and DIVINE_API_KEY and dt and lat and lng:
                response_data = get_divine_planet_position(dt, lat, lng, ayanamsa)
                
            if not response_data:
                if DEMO_MODE or not dt or not lat or not lng:
                    response_data = get_mock_planet_position(dt or "2026-07-09T06:00:00+05:30", lat or "19.076", lng or "72.877", ayanamsa)
                else:
                    token = get_access_token()
                    if not token:
                        response_data = get_mock_planet_position(dt, lat, lng, ayanamsa)
                    else:
                        coordinates = f"{lat},{lng}"
                        api_url = f"https://api.prokerala.com/v2/astrology/natal-planet-position?profile[datetime]={urllib.parse.quote(dt)}&profile[coordinates]={urllib.parse.quote(coordinates)}&ayanamsa={ayanamsa}&house_system=placidus"
                        raw_res = fetch_raw_api(api_url, token)
                        if raw_res and raw_res.get("status") == "ok":
                            raw_data = raw_res.get("data", {})
                            planets_list = raw_data.get("planet_position") or raw_data.get("planet_positions") or []
                            mapped_planets = []
                            for p in planets_list:
                                name = p.get("name") or "N/A"
                                lon = p.get("longitude")
                                deg = p.get("degree")
                                is_retro = p.get("is_retrograde", False)
                                zod = p.get("zodiac", {})
                                
                                mapped_planets.append({
                                    "name": name,
                                    "planet": name,
                                    "longitude": lon,
                                    "degree": deg,
                                    "is_retrograde": is_retro,
                                    "rasi": {
                                        "name": zod.get("name") or "N/A",
                                        "lord": {
                                            "name": zod.get("lord", {}).get("name") or "N/A",
                                            "vedic_name": zod.get("lord", {}).get("name") or "N/A"
                                        }
                                    }
                                })
                            
                            response_data = {
                                "status": "success",
                                "data": {
                                    "planetary_positions": mapped_planets
                                }
                            }
                        else:
                            response_data = get_mock_planet_position(dt, lat, lng, ayanamsa)

            if response_data.get("status") in ["success", "ok"] and "data" in response_data:
                data_dict = response_data["data"]
                planets = data_dict.get("planet_position") or data_dict.get("planetary_positions")
                if planets:
                    planets_sorted = normalize_positions_helper(planets, provider, ayanamsa, dt, lat, lng)
                    if "planet_position" in data_dict:
                        data_dict["planet_position"] = planets_sorted
                    if "planetary_positions" in data_dict:
                        data_dict["planetary_positions"] = planets_sorted
                    
                    normalized_planets = []
                    for p in planets:
                        name = p.get("name") or p.get("planet") or "N/A"
                        longitude = p.get("longitude")
                        if longitude is not None:
                            normalized_planets.append({
                                "planet": name,
                                "longitude": float(longitude)
                             })
                    aspects = calculate_aspects(normalized_planets)
                    response_data["data"]["aspects"] = aspects

        # 7. Western Natal Chart
        elif path == '/api/astrology/natal-chart':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            ayanamsa = get_param('ayanamsa', '0')
            style = get_param('style', 'default')
            dt = adjust_datetime_timezone(dt, lat, lng)
            
            response_data = None
            positions = None
            
            if dt and lat and lng:
                if provider == 'astronomyapi':
                    pos_res = get_astronomy_planet_position(dt, lat, lng)
                    if pos_res and pos_res.get("status") == "success":
                        positions = pos_res.get("data", {}).get("planetary_positions", [])
                elif provider == 'divineapi' and DIVINE_API_KEY:
                    pos_res = get_divine_planet_position(dt, lat, lng, ayanamsa)
                    if pos_res and pos_res.get("status") == "success":
                        positions = pos_res.get("data", {}).get("planetary_positions", [])
                elif provider == 'prokerala' and CLIENT_ID:
                    token = get_access_token()
                    if token:
                        coordinates = f"{lat},{lng}"
                        api_url = f"https://api.prokerala.com/v2/astrology/natal-planet-position?profile[datetime]={urllib.parse.quote(dt)}&profile[coordinates]={urllib.parse.quote(coordinates)}&ayanamsa={ayanamsa}&house_system=placidus"
                        raw_res = fetch_raw_api(api_url, token)
                        if raw_res and raw_res.get("status") == "ok":
                            raw_data = raw_res.get("data", {})
                            planets_list = raw_data.get("planet_position") or raw_data.get("planet_positions") or []
                            mapped_planets = []
                            for p in planets_list:
                                name = p.get("name") or "N/A"
                                lon = p.get("longitude")
                                deg = p.get("degree")
                                is_retro = p.get("is_retrograde", False)
                                zod = p.get("zodiac", {})
                                mapped_planets.append({
                                    "name": name,
                                    "planet": name,
                                    "longitude": lon,
                                    "degree": deg,
                                    "is_retrograde": is_retro,
                                    "rasi": {
                                        "name": zod.get("name") or "N/A",
                                        "lord": {
                                            "name": zod.get("lord", {}).get("name") or "N/A",
                                            "vedic_name": zod.get("lord", {}).get("name") or "N/A"
                                        }
                                    }
                                })
                            positions = mapped_planets

            if style == 'sky':
                if not positions:
                    mock_pos_res = get_mock_planet_position(dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877", ayanamsa)
                    positions = mock_pos_res.get("data", {}).get("planetary_positions", [])
                positions = normalize_positions_helper(positions, provider if provider != 'prokerala' else 'mock', ayanamsa, dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877")
                response_data = get_mock_chart(dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877", ayanamsa, custom_positions=positions, style='sky')
            else:
                if provider == 'prokerala' and CLIENT_ID and dt and lat and lng:
                    token = get_access_token()
                    if token:
                        coordinates = f"{lat},{lng}"
                        api_url = f"https://api.prokerala.com/v2/astrology/natal-chart?profile[datetime]={urllib.parse.quote(dt)}&profile[coordinates]={urllib.parse.quote(coordinates)}&ayanamsa={ayanamsa}&house_system=placidus&aspect_filter=all&orb=default"
                        req = urllib.request.Request(api_url)
                        req.add_header('Authorization', f'Bearer {token}')
                        try:
                            with urllib.request.urlopen(req, timeout=15) as response:
                                svg_content = response.read().decode('utf-8')
                                response_data = {
                                    "status": "success",
                                    "data": {
                                        "svg": svg_content
                                    }
                                }
                        except Exception as e:
                            print(f"[Backend] Error calling Prokerala Natal Chart API: {e}")
                            
                if not response_data:
                    if not positions:
                        mock_pos_res = get_mock_planet_position(dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877", ayanamsa)
                        positions = mock_pos_res.get("data", {}).get("planetary_positions", [])
                    positions = normalize_positions_helper(positions, provider if provider != 'prokerala' else 'mock', ayanamsa, dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877")
                    response_data = get_mock_chart(dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877", ayanamsa, custom_positions=positions, style=style)

        # 8. Transit History (configurable interval up to 2 months)
        elif path == '/api/astrology/transit-history':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            ayanamsa = get_param('ayanamsa', '0')
            limit = int(get_param('limit', '50'))
            offset_idx = int(get_param('offset', '0'))
            interval_min = int(get_param('interval', '15'))  # minutes: 1,5,10,15,30,60
            # Validate interval
            if interval_min not in [1, 5, 10, 15, 30, 60]:
                interval_min = 15
            # Max steps: 2 months = ~87840 min / interval_min; cap limit to 200 per request
            limit = min(limit, 200)
            
            import datetime
            try:
                if 'T' in dt:
                    base_dt = datetime.datetime.strptime(dt.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S")
                else:
                    base_dt = datetime.datetime.strptime(dt.split('+')[0].split('Z')[0], "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    base_dt = datetime.datetime.strptime(dt.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M")
                except:
                    base_dt = datetime.datetime.now()
            
            # Maximum lookback: 2 months = 87840 minutes
            max_steps = int(87840 / interval_min)
            
            history_data = []
            for i in range(limit):
                step_idx = offset_idx + i
                if step_idx >= max_steps:
                    break
                step_dt = base_dt - datetime.timedelta(minutes=interval_min * step_idx)
                step_dt_str = step_dt.strftime("%Y-%m-%dT%H:%M:%S+05:30")
                
                step_pos_raw = get_mock_planet_position(step_dt_str, lat, lng, ayanamsa)["data"]["planetary_positions"]
                step_pos = normalize_positions_helper(step_pos_raw, 'mock', ayanamsa, step_dt_str, lat, lng)
                
                step_entry = {
                    "datetime": step_dt.strftime("%Y-%m-%d %H:%M"),
                    "planets": {}
                }
                for p in step_pos:
                    p_name = p.get("name") or p.get("planet") or ""
                    sign_name = p.get("rasi", {}).get("name") or "Aries"
                    deg_val = p.get("degree", 0.0)
                    # Use tropical_longitude for full 0-360 degree display
                    lon_val = p.get("tropical_longitude") or p.get("longitude") or 0.0
                    step_entry["planets"][p_name] = {
                        "sign": sign_name,
                        "degree": deg_val,
                        "longitude": float(lon_val)
                    }
                
                history_data.append(step_entry)
                
            response_data = {
                "status": "success",
                "data": {
                    "history": history_data,
                    "has_more": (offset_idx + limit) < max_steps,
                    "interval_min": interval_min,
                    "max_steps": max_steps
                }
            }

        else:
            response_data = {"status": "error", "message": "Unknown endpoint"}
            
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def fetch_prokerala_api(self, url, token, fallback_func):
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {token}')
        req.add_header('Accept', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                api_response = json.loads(response.read().decode('utf-8'))
                return {
                    "status": "success",
                    "data": api_response.get("data")
                }
        except Exception as e:
            print(f"[Backend] Error calling Prokerala API: {e}")
            print("[Backend] Falling back to Demo/Mock responses.")
            return fallback_func()

def run_server():
    load_env()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[Backend] Testing configurations...")
        print(f"Loaded credentials status: CLIENT_ID is {'set' if CLIENT_ID else 'empty'}, CLIENT_SECRET is {'set' if CLIENT_SECRET else 'empty'}.")
        print(f"Demo Mode: {DEMO_MODE}")
        print("[Backend] Test passed successfully!")
        sys.exit(0)
        
    print("==========================================================")
    print("      PROKERALA ASTROLOGY API SHOWCASE & DASHBOARD      ")
    print("==========================================================")
    print(f" Port: {PORT}")
    print(f" Host: {HOST}")
    print(f" Mode: {'REAL PROKERALA API' if not DEMO_MODE else 'DEMO/MOCK MODE (No Credentials)'}")
    print(" Serving local website files at: http://{}:{}".format(HOST, PORT))
    print(" Press Ctrl+C to stop.")
    print("==========================================================")
    
    socketserver.TCPServer.allow_reuse_address = True
    # Change CWD context to serve static files from astrology-dashboard directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer((HOST, PORT), DashboardProxyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Backend] Stopping server...")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()
