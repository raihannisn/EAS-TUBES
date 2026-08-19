import re
import requests
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = (
    "https://peta-maritim.bmkg.go.id/"
    "public_api/perairan/"
)

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


def get_maritime_data(maritime_code):

    if not maritime_code:
        return None

    url = (
        BASE_URL
        + quote(maritime_code, safe="")
        + ".json"
    )

    try:
        print(f"[BMKG Maritime] Fetching data for code: {maritime_code}")
        response = _session.get(
            url,
            timeout=20
        )
        
        response.raise_for_status()
        print(f"[BMKG Maritime] Status code: {response.status_code}")

        return normalize_maritime_data(
            response.json()
        )

    except requests.exceptions.HTTPError as e:
        print(f"[BMKG Maritime] HTTP error: {e}")
        print(f"[BMKG Maritime] Response status: {e.response.status_code}")
        print(f"[BMKG Maritime] Response text: {e.response.text[:500]}")
        return None

    except requests.RequestException as e:
        print(f"[BMKG Maritime] Connection error: {e}")
        return None

    except Exception as e:
        print(f"[BMKG Maritime] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_wave_range(wave_desc):

    if not wave_desc:
        return None, None

    numbers = re.findall(
        r"\d+(?:[.,]\d+)?",
        str(wave_desc)
    )

    if not numbers:
        return None, None

    values = [
        float(
            number.replace(",", ".")
        )
        for number in numbers
    ]

    if len(values) == 1:

        return values[0], values[0]

    return min(values), max(values)


def get_ffx_category(wind_speed_max):

    if wind_speed_max is None:
        return None

    if wind_speed_max < 11:
        return "rendah"

    elif wind_speed_max < 15:
        return "sedang"

    return "tinggi"


def normalize_maritime_data(data):

    if not isinstance(data, dict):

        raise ValueError(
            "Format data maritim tidak dikenali"
        )

    forecast_data = data.get(
        "data",
        []
    )

    if not forecast_data:

        raise ValueError(
            "Data prakiraan maritim kosong"
        )

    current = forecast_data[0]

    wind_speed_min = current.get(
        "wind_speed_min"
    )

    wind_speed_max = current.get(
        "wind_speed_max"
    )

    wave_desc = current.get(
        "wave_desc"
    )

    wave_min, wave_max = parse_wave_range(
        wave_desc
    )

    ffx_category = get_ffx_category(
        wind_speed_max
    )

    # Estimasi FFAVG dari rentang angin.
    if (
        wind_speed_min is not None
        and wind_speed_max is not None
    ):

        wind_speed_avg = (
            float(wind_speed_min)
            + float(wind_speed_max)
        ) / 2

    elif wind_speed_max is not None:

        wind_speed_avg = float(
            wind_speed_max
        )

    elif wind_speed_min is not None:

        wind_speed_avg = float(
            wind_speed_min
        )

    else:

        wind_speed_avg = None

    return {

        "code": data.get(
            "code"
        ),

        "name": data.get(
            "name"
        ),

        "issued": data.get(
            "issued"
        ),

        "info": data.get(
            "info"
        ),

        "forecast": {

            "valid_from": current.get(
                "valid_from"
            ),

            "valid_to": current.get(
                "valid_to"
            ),

            "time_desc": current.get(
                "time_desc"
            ),

            "weather": current.get(
                "weather"
            ),

            "weather_desc": current.get(
                "weather_desc"
            ),

            "warning_desc": current.get(
                "warning_desc"
            ),

            "station_remark": current.get(
                "station_remark"
            ),

            "wave_category": current.get(
                "wave_cat"
            ),

            "wave_desc": wave_desc,

            "wave_height_min": wave_min,

            "wave_height_max": wave_max,

            # Untuk reasoning digunakan nilai maksimum
            # dari rentang sebagai pendekatan konservatif.
            "wave_height": wave_max,

            "wind_from": current.get(
                "wind_from"
            ),

            "wind_to": current.get(
                "wind_to"
            ),

            "wind_speed_min": wind_speed_min,

            "wind_speed_max": wind_speed_max,

            "wind_speed_avg": wind_speed_avg,

            "ffx_category": ffx_category
        },

        # Endpoint saat ini belum menyediakan
        # informasi bahaya tersebut secara eksplisit.
        "hazards": {

            "lightning": None,

            "visibility_bad": None,

            "breaking_wave": None
        },

        "sunshine_duration": None
    }