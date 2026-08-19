# Weather Reasoning AI - Setup Guide

## 📋 Struktur Project
```
weather-reasoning-ai/
├── backend/               # FastAPI Python backend
│   ├── app/
│   │   └── main.py       # Main FastAPI application
│   ├── services/         # Business logic services
│   ├── requirements.txt  # Python dependencies
│   └── __init__.py
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx      # React entry point
│   │   └── styles.css
│   ├── package.json
│   └── index.html
├── venv/                 # Python virtual environment (created)
├── .env.example          # Environment template
└── kode_wilayah_tingkat_iv_detail.csv
```

## ✅ Setup Yang Sudah Dilakukan

### Backend (Python)
- ✓ Membuat `requirements.txt` dengan semua dependencies
- ✓ Membuat Python virtual environment (`venv/`)
- ✓ Install semua Python packages:
  - fastapi (FastAPI framework)
  - uvicorn (ASGI server)
  - python-dotenv (Environment variables)
  - requests (HTTP client)
  - numpy & scikit-fuzzy (Fuzzy logic)
  - pydantic (Data validation)

### Frontend (Node.js/React)
- ✓ Semua npm dependencies sudah terinstall
- ✓ Framework siap:
  - React 18.3.1
  - Vite 6.0.5 (build tool)
  - React Router 6.28.0
  - Lucide React (icons)

### Environment
- ✓ Membuat `.env.example` sebagai template

---

## 🚀 Cara Menjalankan Project

### 1. Backend (FastAPI Server)

**Di terminal pertama:**
```powershell
cd c:\weather-reasoning-ai
.\venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: http://localhost:8000

**Docs API tersedia di:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Frontend (React Development Server)

**Di terminal kedua:**
```powershell
cd c:\weather-reasoning-ai\frontend
npm run dev
```

Frontend akan berjalan di: http://localhost:5173 (atau port lain yang ditampilkan)

---

## 🛠️ Commands Penting

### Backend
```powershell
# Aktivasi virtual environment
.\venv\Scripts\Activate.ps1

# Jalankan development server dengan auto-reload
uvicorn app.main:app --reload

# Deaktivasi virtual environment
deactivate
```

### Frontend
```powershell
# Development server
npm run dev

# Build untuk production
npm run build

# Preview production build
npm run preview
```

---

## ⚠️ Catatan Penting

1. **Virtual Environment**: Pastikan selalu activate `venv` sebelum menjalankan backend
2. **Ports**: 
   - Backend default port: 8000
   - Frontend default port: 5173
3. **CORS**: Backend sudah dikonfigurasi dengan CORS middleware untuk frontend
4. **Environment Variables**: Copy `.env.example` ke `.env` jika diperlukan konfigurasi khusus

---

## 📝 Struktur Backend Services

- `bmkg_service.py` - Integrasi BMKG API untuk data cuaca
- `maritime_service.py` - Data dan logika maritim (pelayaran)
- `fuzzy_service.py` - Fuzzy logic untuk klasifikasi cuaca
- `reasoning_service.py` - AI reasoning untuk rekomendasi
- `regional_service.py` - Data wilayah dan geografis

---

## ✨ Project Ready!

Project sudah siap dijalankan. Buka 2 terminal:
1. Terminal 1: Jalankan backend
2. Terminal 2: Jalankan frontend

Selamat mengembangkan! 🎉
