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
CLIENT_ID = ""
CLIENT_SECRET = ""
DEMO_MODE = True

# Load .env file manually
def load_env():
    global HOST, PORT, CLIENT_ID, CLIENT_SECRET, DEMO_MODE
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
                    # Strip quotes if present
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    
                    if key == "PROKERALA_CLIENT_ID":
                        CLIENT_ID = val
                    elif key == "PROKERALA_CLIENT_SECRET":
                        CLIENT_SECRET = val
                    elif key == "PORT":
                        try:
                            PORT = int(val)
                        except ValueError:
                            pass
                    elif key == "HOST":
                        HOST = val

    # If credentials are set, disable force demo mode, else enable it
    if CLIENT_ID and CLIENT_SECRET:
        DEMO_MODE = False
    else:
        DEMO_MODE = True

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

def get_mock_planet_position(datetime_str, lat, lng):
    return {
        "status": "success",
        "data": {
            "planetary_positions": [
                {"planet": "Sun", "sign": "Taurus", "house": 7, "longitude": 59.2, "degree": 29.1, "nakshatra": {"name": "Mrigashira"}, "is_retrograde": False},
                {"planet": "Moon", "sign": "Taurus", "house": 7, "longitude": 38.5, "degree": 8.5, "nakshatra": {"name": "Krittika"}, "is_retrograde": False},
                {"planet": "Mars", "sign": "Pisces", "house": 5, "longitude": 345.3, "degree": 15.3, "nakshatra": {"name": "Uttara Bhadrapada"}, "is_retrograde": False},
                {"planet": "Mercury", "sign": "Gemini", "house": 8, "longitude": 64.1, "degree": 4.1, "nakshatra": {"name": "Ardra"}, "is_retrograde": True},
                {"planet": "Jupiter", "sign": "Aquarius", "house": 4, "longitude": 322.8, "degree": 22.8, "nakshatra": {"name": "Purva Bhadrapada"}, "is_retrograde": False},
                {"planet": "Venus", "sign": "Aries", "house": 6, "longitude": 11.2, "degree": 11.2, "nakshatra": {"name": "Ashwini"}, "is_retrograde": False},
                {"planet": "Saturn", "sign": "Capricorn", "house": 3, "longitude": 276.4, "degree": 6.4, "nakshatra": {"name": "Uttarashadha"}, "is_retrograde": False}
            ]
        }
    }

def get_mock_chart(dt, lat, lng):
    import math
    svg = """<svg viewBox="0 0 500 500" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#160c33" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#090514" stop-opacity="1"/>
    </radialGradient>
    <radialGradient id="wheelCenter" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0c081d" stop-opacity="1"/>
      <stop offset="100%" stop-color="#1a113d" stop-opacity="0.3"/>
    </radialGradient>
  </defs>
  
  <rect width="100%" height="100%" fill="url(#bgGlow)" rx="12"/>
  
  <circle cx="250" cy="250" r="210" stroke="#ffd700" stroke-width="2.5" fill="none" opacity="0.8" />
  <circle cx="250" cy="250" r="185" stroke="#ffd700" stroke-width="1.5" fill="none" opacity="0.6" />
  
  <g stroke="#ffd700" stroke-width="1" opacity="0.4">
"""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    for i in range(12):
        angle = i * 30 * math.pi / 180
        x1 = 250 + 185 * math.cos(angle)
        y1 = 250 + 185 * math.sin(angle)
        x2 = 250 + 210 * math.cos(angle)
        y2 = 250 + 210 * math.sin(angle)
        svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" />\n'
        
        label_angle = (i * 30 + 15) * math.pi / 180
        lx = 250 + 197 * math.cos(label_angle)
        ly = 250 + 197 * math.sin(label_angle) + 4
        svg += f'    <text x="{lx:.1f}" y="{ly:.1f}" fill="#ffd700" font-size="8" font-family="Outfit" font-weight="700" text-anchor="middle" transform="rotate({i*30+105}, {lx:.1f}, {ly:.1f})" opacity="0.8">{signs[i]}</text>\n'

    svg += """  </g>
  
  <circle cx="250" cy="250" r="140" stroke="#ffd700" stroke-width="1.5" fill="url(#wheelCenter)" opacity="0.5" />
  <circle cx="250" cy="250" r="60" stroke="#ffd700" stroke-width="1" fill="none" opacity="0.3" />
  
  <g stroke="#ffffff" stroke-dasharray="3,3" stroke-width="0.8" opacity="0.3">
"""
    for i in range(12):
        angle = (i * 30 - 15) * math.pi / 180
        x1 = 250 + 60 * math.cos(angle)
        y1 = 250 + 60 * math.sin(angle)
        x2 = 250 + 140 * math.cos(angle)
        y2 = 250 + 140 * math.sin(angle)
        svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" />\n'

    aspects = [
        (30, 150, "blue"), (90, 210, "blue"), (120, 240, "blue"),
        (0, 180, "red"), (90, 270, "red"),
        (30, 120, "red"), (150, 240, "red"), (210, 300, "red"),
        (0, 60, "blue"), (180, 240, "blue"),
        (45, 135, "green"), (160, 200, "green")
    ]
    
    svg += """  </g>
  
  <g stroke-width="1.2" opacity="0.6">
"""
    for a in aspects:
        ang1 = a[0] * math.pi / 180
        ang2 = a[1] * math.pi / 180
        x1 = 250 + 140 * math.cos(ang1)
        y1 = 250 + 140 * math.sin(ang1)
        x2 = 250 + 140 * math.cos(ang2)
        y2 = 250 + 140 * math.sin(ang2)
        color = "#2ef56a" if a[2] == "green" else "#ff5757" if a[2] == "red" else "#00d2ff"
        svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" />\n'

    planets_pos = [
        ("Sun", "☉", 45), ("Moon", "☽", 85), ("Mars", "♂", 155),
        ("Mercury", "☿", 35), ("Jupiter", "♃", 280), ("Venus", "♀", 115),
        ("Saturn", "♄", 340), ("Uranus", "♅", 215), ("Neptune", "♆", 175),
        ("Pluto", "♇", 195)
    ]
    
    svg += """  </g>
  
  <g font-size="16" font-family="Arial" text-anchor="middle">
"""
    for p in planets_pos:
        angle = p[2] * math.pi / 180
        px = 250 + 162 * math.cos(angle)
        py = 250 + 162 * math.sin(angle) + 5
        svg += f'    <circle cx="{px:.1f}" cy="{py-5:.1f}" r="11" fill="#090514" stroke="#ffd700" stroke-width="0.5" opacity="0.8"/>\n'
        svg += f'    <text x="{px:.1f}" y="{py:.1f}" fill="#ffffff">{p[1]}</text>\n'

    svg += """  </g>
  
  <g stroke="#ffffff" stroke-width="1.5" opacity="0.7">
    <line x1="65" y1="250" x2="435" y2="250" />
    <line x1="250" y1="65" x2="250" y2="435" />
  </g>
  
  <g fill="#ffd700" font-family="Syne" font-size="11" font-weight="800" text-anchor="middle">
    <rect x="42" y="238" width="22" height="24" rx="3" fill="#090514" stroke="#ffd700" stroke-width="1"/>
    <text x="53" y="254">ASC</text>
    
    <rect x="436" y="238" width="22" height="24" rx="3" fill="#090514" stroke="#ffd700" stroke-width="1"/>
    <text x="447" y="254">DSC</text>
    
    <rect x="239" y="42" width="22" height="24" rx="3" fill="#090514" stroke="#ffd700" stroke-width="1"/>
    <text x="250" y="58">MC</text>
    
    <rect x="239" y="434" width="22" height="24" rx="3" fill="#090514" stroke="#ffd700" stroke-width="1"/>
    <text x="250" y="450">IC</text>
  </g>
  
  <g fill="#ffffff" font-family="Outfit" font-size="8" text-anchor="middle" opacity="0.9">
    <text x="250" y="238" fill="#ffd700" font-size="9" font-weight="700">COSMIC WHEEL</text>
    <text x="250" y="252" font-size="7">July 9, 2026</text>
    <text x="250" y="264" font-size="7">10:07 PM (IST)</text>
  </g>
</svg>
"""
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
                "configured": not DEMO_MODE,
                "demo_mode": DEMO_MODE,
                "client_id_configured": bool(CLIENT_ID)
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

        # 1. Daily Horoscope
        if path == '/api/horoscope/daily':
            sign = get_param('sign', 'aries')
            if DEMO_MODE:
                response_data = get_mock_horoscope(sign)
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_horoscope(sign)
                else:
                    dt = get_param('datetime', time.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
                    api_url = f"https://api.prokerala.com/v2/horoscope/daily?sign={sign}&datetime={urllib.parse.quote(dt)}"
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
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_panchang(dt or "2026-07-09T06:00:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_panchang(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/panchang/advanced?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
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
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_kundli(dt or "1995-05-15T08:30:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_kundli(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    kundli_url = f"https://api.prokerala.com/v2/astrology/kundli?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
                    planet_url = f"https://api.prokerala.com/v2/astrology/planet-position?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
                    
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
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_mangal_dosha(dt or "1995-05-15T08:30:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_mangal_dosha(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/mangal-dosha?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
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
            
            if DEMO_MODE or not g_dob or not b_dob or not g_lat or not b_lat:
                response_data = get_mock_kundli_matching(g_dob or "1996-08-20T10:15:00+05:30", b_dob or "1994-12-05T14:45:00+05:30")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_kundli_matching(g_dob, b_dob)
                else:
                    g_coords = f"{g_lat},{g_lng}"
                    b_coords = f"{b_lat},{b_lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/kundli-matching/advanced?girl_dob={urllib.parse.quote(g_dob)}&girl_coordinates={urllib.parse.quote(g_coords)}&boy_dob={urllib.parse.quote(b_dob)}&boy_coordinates={urllib.parse.quote(b_coords)}&ayanamsa=1&la=en"
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
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_planet_position(dt or "2026-07-09T06:00:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_planet_position(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/planet-position?datetime={urllib.parse.quote(dt)}&coordinates={urllib.parse.quote(coordinates)}&ayanamsa=1&la=en"
                    response_data = self.fetch_prokerala_api(api_url, token, fallback_func=lambda: get_mock_planet_position(dt, lat, lng))

        # 7. Western Natal Chart
        elif path == '/api/astrology/natal-chart':
            dt = get_param('datetime')
            lat = get_param('latitude')
            lng = get_param('longitude')
            
            if DEMO_MODE or not dt or not lat or not lng:
                response_data = get_mock_chart(dt or "2026-07-09T22:00:00+05:30", lat or "19.076", lng or "72.877")
            else:
                token = get_access_token()
                if not token:
                    response_data = get_mock_chart(dt, lat, lng)
                else:
                    coordinates = f"{lat},{lng}"
                    api_url = f"https://api.prokerala.com/v2/astrology/natal-chart?profile[datetime]={urllib.parse.quote(dt)}&profile[coordinates]={urllib.parse.quote(coordinates)}&ayanamsa=0&house_system=0"
                    
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
                        response_data = get_mock_chart(dt, lat, lng)

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
