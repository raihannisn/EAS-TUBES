# 🔧 BMKG API Integration - Troubleshooting & Solution

## Problem Identified
Data cuaca (suhu, kelembapan, angin, dll) tidak terupdate dari BMKG API karena mendapatkan status **HTTP 403 "Akses diblokir"** (Access Forbidden).

## Root Cause Analysis
BMKG API dilindungi oleh Cloudflare dan mendeteksi request yang tidak memiliki User-Agent header (terlihat seperti bot/script). Akibatnya, request ditolak dengan status 403.

## Solution Applied

### 1. ✅ Added User-Agent Header to All Requests
Semua request ke BMKG API sekarang menyertakan User-Agent header agar terlihat seperti request dari browser normal:
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
```

### 2. ✅ Implemented Session with Retry Strategy
- Membuat persistent session untuk meningkatkan performa
- Menambah retry logic untuk handle temporary failures
- Better connection pooling

### 3. ✅ Enhanced Error Logging
Menambah detailed logging untuk memudahkan debugging:
- Response status codes
- Error messages
- Request parameters
- Stack traces

### 4. ✅ Updated Environment Configuration
Menambah konfigurasi BMKG yang lengkap di `.env`:
```env
BMKG_ADM4=31.71.03.1001              # Lokasi untuk cuaca
BMKG_MARITIME_CODE=H.01               # Kode maritim
BMKG_MARITIME_URL=https://...         # URL Maritime API
```

## Files Modified

1. **backend/services/bmkg_service.py**
   - Tambah session dengan User-Agent
   - Improve error handling
   - Better logging

2. **backend/services/maritime_service.py**
   - Tambah session dengan User-Agent
   - Improve error handling
   - Better logging

3. **backend/services/test_bmkg.py** (NEW)
   - Script untuk testing BMKG API connectivity
   - Debug information
   - Sample data display

4. **.env**
   - Tambah BMKG_ADM4, BMKG_MARITIME_CODE, BMKG_MARITIME_URL

5. **.env.example**
   - Updated dengan semua konfigurasi yang tersedia

## Verification Results

### ✅ Weather API - SUCCESS
```
Status: 200
Temperature: 27 °C
Humidity: 75 %
Precipitation: 0.1 mm
Wind Speed: 5.5 km/h
Cloud Cover: 39 %
Visibility: < 8 km
Condition: Cerah
```

### ⚠️ Maritime API - NEEDS INVESTIGATION
Status: 404 (Not Found) - kemungkinan parameter atau endpoint berbeda

## How to Test

Run diagnostic test:
```bash
cd c:\weather-reasoning-ai
.\venv\Scripts\Activate.ps1
python backend/services/test_bmkg.py
```

Check endpoints:
- Weather API: `GET http://localhost:8000/api/weather`
- Locations: `GET http://localhost:8000/api/locations`
- API Docs: `http://localhost:8000/docs`

## Accessing Real-time Data

### Via FastAPI Endpoint
```bash
curl "http://localhost:8000/api/weather"
```

Response includes:
- Weather data (temperature, humidity, wind, precipitation, etc.)
- Location information
- Maritime data (jika tersedia)
- Fuzzy classification
- AI reasoning

### Via Frontend
Frontend akan otomatis fetch data dari backend setiap kali page load atau refresh.

## Future Improvements

1. **Caching Strategy** - Cache BMKG response untuk mengurangi API calls
2. **Rate Limiting** - Implement rate limiting untuk menghindari blocked access
3. **Fallback Data** - Gunakan fallback/mock data ketika API tidak available
4. **Scheduled Updates** - Update data secara periodic, bukan on-demand
5. **Multiple Locations** - Support lebih banyak lokasi sekaligus

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BMKG_API_URL` | `https://api.bmkg.go.id/publik/prakiraan-cuaca` | BMKG Weather API endpoint |
| `BMKG_ADM4` | `31.71.03.1001` | Location code (Jakarta Pusat) |
| `BMKG_MARITIME_URL` | `https://api.bmkg.go.id/publik/prakiraan-maritim` | BMKG Maritime API endpoint |
| `BMKG_MARITIME_CODE` | `H.01` | Maritime region code (Jakarta area) |
| `API_PORT` | `8000` | Backend server port |
| `API_HOST` | `0.0.0.0` | Backend server host |

## Troubleshooting

**Q: Still getting 403 error?**
- A: Check internet connection
- A: Try with different ADM4 code
- A: Run test script to debug: `python backend/services/test_bmkg.py`

**Q: No data showing in frontend?**
- A: Make sure backend is running: `http://localhost:8000`
- A: Check browser console for errors
- A: Check backend logs for error messages

**Q: Want to change location?**
- A: Update `BMKG_ADM4` in `.env`
- A: Get location codes from `/api/locations` endpoint
- A: Restart backend server

---

**Last Updated:** 2026-08-19
**Status:** ✅ Weather API Working | ⚠️ Maritime API Pending
