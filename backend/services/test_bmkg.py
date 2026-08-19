"""
Script untuk testing koneksi dan data BMKG API
Jalankan dengan: python backend/services/test_bmkg.py
"""

import requests
import json
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BMKG_URL = os.getenv("BMKG_API_URL", "https://api.bmkg.go.id/publik/prakiraan-cuaca")
ADM4 = os.getenv("BMKG_ADM4", "31.71.03.1001")
MARITIME_URL = os.getenv("BMKG_MARITIME_URL", "https://api.bmkg.go.id/publik/prakiraan-maritim")
MARITIME_CODE = os.getenv("BMKG_MARITIME_CODE", "H.01")

def create_session():
    """Create session with retry strategy dan proper headers"""
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

def test_bmkg_weather():
    """Test BMKG Weather API"""
    print("\n" + "="*60)
    print("TEST: BMKG WEATHER API")
    print("="*60)
    print(f"URL: {BMKG_URL}")
    print(f"ADM4: {ADM4}")
    
    session = create_session()
    
    try:
        params = {"adm4": ADM4}
        response = session.get(BMKG_URL, params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API Response berhasil")
            print(f"\nStructure:")
            print(f"  - lokasi: {json.dumps(data.get('lokasi'), indent=2)}")
            print(f"  - data length: {len(data.get('data', []))}")
            
            if data.get('data'):
                first_data = data['data'][0]
                print(f"  - cuaca count: {len(first_data.get('cuaca', []))}")
                
                if first_data.get('cuaca'):
                    print(f"\nSample Weather Data:")
                    weather_items = []
                    for group in first_data['cuaca']:
                        for item in group:
                            weather_items.append(item)
                    
                    if weather_items:
                        sample = weather_items[0]
                        print(f"  - Timestamp: {sample.get('local_datetime')}")
                        print(f"  - Temperature: {sample.get('t')} °C")
                        print(f"  - Humidity: {sample.get('hu')} %")
                        print(f"  - Precipitation: {sample.get('tp')} mm")
                        print(f"  - Wind Speed: {sample.get('ws')} km/h")
                        print(f"  - Cloud Cover: {sample.get('tcc')} %")
                        print(f"  - Visibility: {sample.get('vs_text')}")
                        print(f"  - Condition: {sample.get('weather_desc')}")
            
            return True
        else:
            print(f"✗ API Error: Status {response.status_code}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        session.close()

def test_bmkg_maritime():
    """Test BMKG Maritime API"""
    print("\n" + "="*60)
    print("TEST: BMKG MARITIME API")
    print("="*60)
    print(f"URL: {MARITIME_URL}")
    print(f"Maritime Code: {MARITIME_CODE}")
    
    session = create_session()
    
    try:
        params = {"kodemaritime": MARITIME_CODE}
        response = session.get(MARITIME_URL, params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API Response berhasil")
            print(f"\nStructure:")
            print(f"  - lokasi: {json.dumps(data.get('lokasi'), indent=2)}")
            print(f"  - data length: {len(data.get('data', []))}")
            
            if data.get('data'):
                first_data = data['data'][0]
                print(f"  - forecast count: {len(first_data.get('forecast', []))}")
                
                if first_data.get('forecast'):
                    print(f"\nSample Maritime Data:")
                    sample = first_data['forecast'][0]
                    print(f"  - Timestamp: {sample.get('local_datetime')}")
                    print(f"  - Wave Height: {sample.get('height')} m")
                    print(f"  - Wind Avg: {sample.get('windspeed_avg')} knots")
                    print(f"  - Wind Max: {sample.get('windspeed_max')} knots")
                    print(f"  - FFX: {sample.get('ffx')}")
            
            return True
        else:
            print(f"✗ API Error: Status {response.status_code}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        session.close()

def test_local_endpoints():
    """Test local FastAPI endpoints"""
    print("\n" + "="*60)
    print("TEST: LOCAL FASTAPI ENDPOINTS")
    print("="*60)
    
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        ("/", "Root"),
        ("/api/weather", "Weather"),
        ("/api/locations", "Locations"),
        ("/docs", "API Docs"),
    ]
    
    for endpoint, name in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name:15} [{endpoint:20}] - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ {name:15} [{endpoint:20}] - Connection Error (Server not running?)")
        except Exception as e:
            print(f"✗ {name:15} [{endpoint:20}] - Error: {e}")

if __name__ == "__main__":
    print("\n🔍 BMKG API & Local Service Testing")
    print("="*60)
    
    print("\n[1/3] Testing BMKG Weather API...")
    weather_ok = test_bmkg_weather()
    
    print("\n[2/3] Testing BMKG Maritime API...")
    maritime_ok = test_bmkg_maritime()
    
    print("\n[3/3] Testing Local FastAPI Endpoints...")
    test_local_endpoints()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"  Weather API: {'✓ OK' if weather_ok else '✗ FAILED'}")
    print(f"  Maritime API: {'✓ OK' if maritime_ok else '✗ FAILED'}")
    print("\nTips:")
    print("  1. Pastikan BMKG_ADM4 dan BMKG_MARITIME_CODE sudah diatur di .env")
    print("  2. Pastikan internet connection aktif")
    print("  3. Cek BMKG API status: https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=31.71.03.1001")
    print("  4. Untuk FastAPI, pastikan backend server sedang running")
    print("="*60 + "\n")
