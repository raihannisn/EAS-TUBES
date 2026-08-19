import os
import math
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BMKG_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

import csv
from pathlib import Path

# Create session with retry strategy dan proper headers
def create_session():
    session = requests.Session()
    
    # Retry strategy
    retry = Retry(
        total=3,
        connect=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Set user agent untuk menghindari 403 dari Cloudflare
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return session

# Global session instance
_session = create_session()

# Hardcoded reference locations with coordinates
BMKG_REFERENCE_LOCATIONS = {
    "31.71.03.1001": {"name": "Kemayoran, Jakarta Pusat", "maritime_code": "H.01", "lat": -6.164721, "lon": 106.845384},
    "32.73.01.1001": {"name": "Bandung, Jawa Barat", "maritime_code": "H.02", "lat": -6.917464, "lon": 107.619123},
    "35.74.01.1001": {"name": "Surabaya, Jawa Timur", "maritime_code": "H.03", "lat": -7.257472, "lon": 112.752090},
    "73.71.01.1001": {"name": "Makassar, Sulawesi Selatan", "maritime_code": "H.04", "lat": -5.147665, "lon": 119.432732}
}

# Load location catalog from CSV
_LOCATION_CATALOG = None
_ADM4_MAPPING = None

def _load_location_catalog():
    """Load locations dari CSV dan cache ke memory."""
    global _LOCATION_CATALOG, _ADM4_MAPPING
    
    if _LOCATION_CATALOG is not None:
        return _LOCATION_CATALOG, _ADM4_MAPPING
    
    _LOCATION_CATALOG = []
    _ADM4_MAPPING = {}
    
    try:
        csv_path = os.path.join(
            Path(__file__).parent.parent.parent,
            "kode_wilayah_tingkat_iv_detail.csv"
        )
        
        if not os.path.exists(csv_path):
            print(f"[BMKG] CSV file not found: {csv_path}")
            return _LOCATION_CATALOG, _ADM4_MAPPING
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                adm4 = row.get("kode_desa_kelurahan", "").strip()
                desa_name = row.get("nama_desa_kelurahan", "").strip()
                kec_name = row.get("nama_kecamatan", "").strip()
                kabu_name = row.get("nama_kabupaten_kota", "").strip()
                prov_name = row.get("nama_provinsi", "").strip()
                
                if not adm4:
                    continue
                
                # Create location name from hierarchy
                location_name = f"{desa_name}, {kec_name}, {kabu_name}, {prov_name}"
                
                # Get coordinates from reference if available, else use default
                if adm4 in BMKG_REFERENCE_LOCATIONS:
                    ref = BMKG_REFERENCE_LOCATIONS[adm4]
                    lat, lon = ref["lat"], ref["lon"]
                    maritime_code = ref.get("maritime_code", "")
                else:
                    # Default: use center of Indonesia or first reference location
                    lat, lon = -6.2, 107.0  # Rough center
                    maritime_code = ""
                
                location_obj = {
                    "adm4": adm4,
                    "name": location_name,
                    "desa": desa_name,
                    "kecamatan": kec_name,
                    "kabupaten": kabu_name,
                    "provinsi": prov_name,
                    "lat": lat,
                    "lon": lon,
                    "maritime_code": maritime_code
                }
                
                _LOCATION_CATALOG.append(location_obj)
                _ADM4_MAPPING[adm4] = location_obj
        
        print(f"[BMKG] Loaded {len(_LOCATION_CATALOG)} locations from CSV")
    
    except Exception as e:
        print(f"[BMKG] Error loading location catalog: {e}")
    
    return _LOCATION_CATALOG, _ADM4_MAPPING


def get_bmkg_location_catalog():
    """Get full location catalog."""
    catalog, _ = _load_location_catalog()
    return catalog


def get_location_by_adm4(adm4):
    """Get location info by adm4 code."""
    _, mapping = _load_location_catalog()
    return mapping.get(adm4)



def get_weather_data(adm4=None):
    adm4 = adm4 or os.getenv("BMKG_ADM4", "31.71.03.1001")

    params = {
        "adm4": adm4
    }

    try:
        print(f"[BMKG] Fetching weather data for ADM4: {adm4}")
        response = _session.get(
            BMKG_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        print(f"[BMKG] Status code: {response.status_code}")

        data = response.json()
        print(f"[BMKG] Response received, normalizing data...")

        result = normalize_weather_data(data)
        print(f"[BMKG] Data normalized successfully")
        return result

    except requests.exceptions.ConnectionError as e:
        print(f"[BMKG] Connection error: {e}")
        print(f"[BMKG] Make sure BMKG API is accessible at: {BMKG_URL}")
        return None
    
    except requests.exceptions.Timeout as e:
        print(f"[BMKG] Timeout error: {e}")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"[BMKG] HTTP error: {e}")
        print(f"[BMKG] Response status: {e.response.status_code}")
        print(f"[BMKG] Response text: {e.response.text[:500]}")
        return None

    except ValueError as e:
        print(f"[BMKG] Data validation error: {e}")
        return None

    except Exception as e:
        print(f"[BMKG] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_nearest_location(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None

    def haversine(a_lat, a_lon, b_lat, b_lon):
        radius = 6371
        d_lat = math.radians(b_lat - a_lat)
        d_lon = math.radians(b_lon - a_lon)
        a1 = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(a_lat))
            * math.cos(math.radians(b_lat))
            * math.sin(d_lon / 2) ** 2
        )
        return 2 * radius * math.asin(math.sqrt(a1))

    catalog = [
        {
            "adm4": adm4,
            **reference
        }
        for adm4, reference in BMKG_REFERENCE_LOCATIONS.items()
    ]
    nearest = None
    nearest_distance = None

    for option in catalog:
        if option.get("lat") is None or option.get("lon") is None:
            continue
        distance = haversine(lat, lon, option["lat"], option["lon"])
        if nearest_distance is None or distance < nearest_distance:
            nearest = option
            nearest_distance = distance

    if nearest is None:
        return None

    nearest["distance_km"] = round(nearest_distance, 2)
    return nearest


def normalize_weather_data(data):

    lokasi = data["lokasi"]
    weather_groups = data["data"][0]["cuaca"]

    weather_items = []

    for group in weather_groups:
        for item in group:
            weather_items.append(item)

    if not weather_items:
        raise ValueError("Data cuaca BMKG kosong")

    current = weather_items[0]

    return {
        "location": {
            "adm4": lokasi.get("adm4"),
            "province": lokasi.get("provinsi"),
            "city": lokasi.get("kotkab"),
            "district": lokasi.get("kecamatan"),
            "village": lokasi.get("desa"),
            "latitude": lokasi.get("lat"),
            "longitude": lokasi.get("lon")
        },

        "weather": {
            "timestamp": current.get("local_datetime"),
            "temperature": current.get("t"),
            "humidity": current.get("hu"),
            "precipitation": current.get("tp"),
            "wind_speed": current.get("ws"),
            "cloud_cover": current.get("tcc"),
            "visibility": current.get("vs_text"),
            "condition": current.get("weather_desc")
        }
    }


if __name__ == "__main__":

    result = get_weather_data()

    print("\n=== DATA CUACA NORMALIZED ===")

    if result:
        print(result)
    else:
        print("Gagal mengambil data BMKG")