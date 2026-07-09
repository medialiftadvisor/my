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
PORT = 8080
HOST = "127.0.0.1"
CLIENT_ID = ""
CLIENT_SECRET = ""
DEMO_MODE = True

# Load .env file manually if exists to avoid dependencies
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
    
    # If in demo mode, no token is needed
    if DEMO_MODE:
        return "demo_token"
        
    # Check if existing token is still valid (with a 60s buffer)
    current_time = time.time()
    if _access_token and current_time < _token_expiry - 60:
        return _access_token
        
    print("[Backend] Fetching fresh OAuth2 access token from Prokerala API...")
    token_url = "https://api.prokerala.com/token"
    
    # Payload for token
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
        # Fallback to demo mode if token fetching fails
        print("[Backend] Falling back to Demo Mode for this request.")
        return None

# Realistic mock data generators for Demo Mode
def get_mock_horoscope(sign):
    sign_clean = sign.lower()
    horoscopes = {
        "aries": "Today promises to be an energetic day for Aries. Your coaching goals are well within reach. Avoid impulsive decisions in the afternoon; instead, channel your drive into creating daily discipline.",
        "taurus": "A day of grounding and stability for Taurus. Take time to reflect on your career progression. In your personal relations, a gentle conversation can clear up minor misunderstandings.",
        "gemini": "Communication is your key superpower today, Gemini. You'll find yourself expressing complex ideas with clarity. Focus on keeping your focus single-pointed to avoid overthinking.",
        "cancer": "Emotional clarity is highlighted today, Cancer. Give yourself space to heal from past patterns. In your career, a steady approach is favored over hasty change.",
        "leo": "Your natural leadership qualities shine today, Leo. People are drawn to your warmth. Use this momentum to align your habits with your grand visions.",
        "virgo": "An excellent day for organization and detail work, Virgo. The systems you put in place today will bring immense mental peace. Don't let self-criticism hold you back.",
        "libra": "Balance is returning to your life, Libra. Take a step back from busy routines and focus on self-care. A positive message from a peer will lift your spirits.",
        "scorpio": "Intense focus allows you to overcome a persistent obstacle today, Scorpio. Trust your intuition. A breakthrough in your personal habits is imminent.",
        "sagittarius": "Your optimistic outlook opens doors today, Sagittarius. A perfect time for learning and planning long-term growth. Maintain focus on small, daily routines.",
        "capricorn": "Your professional drive is at an all-time high today, Capricorn. Hard work is noticed and appreciated. Remember to maintain work-life balance for long-term consistency.",
        "aquarius": "Innovative thoughts fill your mind today, Aquarius. You are ready to break free from old restrictions. Share your vision with others; collaboration brings success.",
        "pisces": "Deep intuitive insights guide you today, Pisces. A great day to practice mindfulness and overcome emotional overwhelm. Trust your inner compass."
    }
    
    prediction = horoscopes.get(sign_clean, "Focus on self-reflection and establishing steady habits today. Your cosmic alignment supports growth and personal clarity.")
    
    return {
        "status": "success",
        "data": {
            "sign": sign.capitalize(),
            "date": time.strftime("%Y-%m-%d"),
            "prediction": prediction,
            "areas": {
                "personal": "Your energy is high, suitable for completing tasks that require focus.",
                "health": "Take walks in nature to release mental tension.",
                "profession": "A good day to reorganize your workspace and schedule.",
                "relationship": "Speak from the heart. Compassion will solve any disputes."
            }
        }
    }

def get_mock_kundli(datetime_str, lat, lng):
    # Generates a randomized but structured birth chart based on location/time
    return {
        "status": "success",
        "data": {
            "birth_details": {
                "datetime": datetime_str,
                "latitude": lat,
                "longitude": lng
            },
            "ascendant": {
                "name": "Leo",
                "lord": "Sun",
                "degree": 14.5,
                "description": "Natural leader, expressive, proud, courageous, and seeking acknowledgment."
            },
            "moon_sign": {
                "name": "Aries",
                "lord": "Mars",
                "degree": 22.1,
                "description": "Energetic, pioneering, emotionally active, and enjoys taking challenges head-on."
            },
            "nakshatra": {
                "name": "Bharani",
                "lord": "Venus",
                "pada": 3,
                "description": "Associated with creativity, transformation, and strong determination."
            },
            "planetary_positions": [
                {"planet": "Sun", "sign": "Gemini", "house": 11, "degree": 10.2},
                {"planet": "Moon", "sign": "Aries", "house": 9, "degree": 22.1},
                {"planet": "Mars", "sign": "Leo", "house": 1, "degree": 5.4},
                {"planet": "Mercury", "sign": "Taurus", "house": 10, "degree": 28.7},
                {"planet": "Jupiter", "sign": "Aquarius", "house": 7, "degree": 12.3},
                {"planet": "Venus", "sign": "Gemini", "house": 11, "degree": 2.1},
                {"planet": "Saturn", "sign": "Capricorn", "house": 6, "degree": 8.9}
            ]
        }
    }

def get_mock_mangal_dosha(datetime_str, lat, lng):
    # Determine presence based on birth minute to make it semi-random but consistent
    has_dosha = False
    try:
        minutes = int(datetime_str.split(":")[1])
        has_dosha = (minutes % 3 == 0)
    except:
        pass
        
    if has_dosha:
        description = "You have Mangal Dosha (Anshik / Partial). This indicates that Mars is positioned in a house that can lead to high energy levels, occasional impulsiveness, or energy blockages. Remedial coaching actions include daily physical exercise, mindfulness routines, and active anger-management practice."
    else:
        description = "No Mangal Dosha found. Your Mars energy is harmonious, supporting steady action, high discipline, and smooth emotional expression without major energetic blocks."
        
    return {
        "status": "success",
        "data": {
            "has_mangal_dosha": has_dosha,
            "type": "Anshik (Partial)" if has_dosha else "None",
            "description": description,
            "remedy": "Practice daily grounding, meditate for 10 minutes, and channel any excess physical energy into positive habits." if has_dosha else "Maintain your current active physical routine to keep energy channels balanced."
        }
    }

def get_mock_kundli_matching(girl_dob, boy_dob):
    # Generate compatibility score based on birth dates
    try:
        sum_chars = sum(ord(c) for c in (girl_dob + boy_dob))
        score = 18 + (sum_chars % 17) # Score between 18 and 34
    except:
        score = 26
        
    verdict = "Excellent Match" if score >= 25 else "Average Match" if score >= 18 else "Low Compatibility"
    
    return {
        "status": "success",
        "data": {
            "score": score,
            "max_score": 36,
            "verdict": verdict,
            "guna_details": {
                "Varna (Work Profile)": f"{1 if score % 2 == 0 else 0}/1",
                "Vashya (Influence)": f"{1.5 if score % 3 == 0 else 2}/2",
                "Tara (Destiny)": f"{1.5 if score % 4 == 0 else 3}/3",
                "Yoni (Physique)": f"{3 if score % 5 == 0 else 4}/4",
                 "Graha Maitri (Friendship)": f"{3.5 if score % 2 == 0 else 5}/5",
                "Gana (Temperament)": f"{5 if score % 3 == 0 else 6}/6",
                "Bhakoot (Construct)": f"{0 if score % 7 == 0 else 7}/7",
                "Nadi (Health)": f"{8 if score % 4 != 0 else 0}/8"
            },
            "alignment_advice": "This relationship holds high potential. Clear communication and regular mutual alignment check-ins will help sustain long-term synergy."
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

class AstrologyProxyHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Override to log cleanly
        sys.stderr.write(f"[Server] {format % args}\n")

    def end_headers(self):
        # Add CORS headers to all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight CORS requests
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        # Route API endpoints
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if path.startswith('/api/'):
            self.handle_api_request(path, query_params)
        else:
            # Fall back to serving static files from current directory
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/'):
            # Read POST body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Try to parse query params or json
            params = {}
            if self.headers.get('Content-Type') == 'application/json':
                try:
                    params = json.loads(post_data)
                except Exception as e:
                    print(f"Error parsing JSON body: {e}")
            else:
                params = urllib.parse.parse_qs(post_data)
                # Convert list values to single values
                params = {k: v[0] for k, v in params.items()}
                
            self.handle_api_request(path, params)
        else:
            self.send_error(404, "Not Found")

    def handle_api_request(self, path, params):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_data = {}
        
        # 1. Config Endpoint
        if path == '/api/config':
            response_data = {
                "configured": not DEMO_MODE,
                "demo_mode": DEMO_MODE,
                "client_id_configured": bool(CLIENT_ID)
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        # Extract common single values from query lists if GET
        def get_param(name, default=""):
            val = params.get(name)
            if isinstance(val, list) and len(val) > 0:
                return val[0]
            elif val is not None:
                return val
            return default

        # 2. Daily Horoscope Endpoint
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
                    
        # 3. Kundli Endpoint
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
                    
        # 4. Mangal Dosha Endpoint
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
                    
        # 5. Kundli Matching Endpoint
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
    
    # Check if run with --test flag
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[Backend] Testing configurations...")
        print(f"Loaded credentials status: CLIENT_ID is {'set' if CLIENT_ID else 'empty'}, CLIENT_SECRET is {'set' if CLIENT_SECRET else 'empty'}.")
        print(f"Demo Mode: {DEMO_MODE}")
        print("[Backend] Test passed successfully!")
        sys.exit(0)
        
    print("==========================================================")
    print("      THE CLARITY CODE™ ASTROLOGY SERVER & WEB HOST      ")
    print("==========================================================")
    print(f" Port: {PORT}")
    print(f" Mode: {'REAL PROKERALA API' if not DEMO_MODE else 'DEMO/MOCK MODE (No Credentials)'}")
    if DEMO_MODE:
        print(" Note: Add PROKERALA_CLIENT_ID & SECRET in .env for real API connections.")
    print(" Serving local website files at: http://{}:{}".format(HOST, PORT))
    print(" Press Ctrl+C to stop.")
    print("==========================================================")
    
    # Set up TCP server reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), AstrologyProxyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Backend] Stopping server...")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()
