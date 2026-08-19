from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..services.bmkg_service import (
    get_weather_data,
    get_bmkg_location_catalog,
    find_nearest_location,
    get_location_by_adm4
)

from ..services.maritime_service import (
    get_maritime_data
)

from ..services.fuzzy_service import (
    classify_weather
)

from ..services.reasoning_service import (
    calculate_reasoning
)

from ..services.regional_service import (
    get_all_provinces,
    get_kabupaten_by_province,
    get_kecamatan_by_kabupaten,
    get_desa_by_kecamatan
)

import os
import json
import requests
from dotenv import load_dotenv


load_dotenv()


def build_grounded_ai_answer(question: str, context: dict) -> str:
    if not context:
        return (
            "Saya belum bisa menjawab karena data cuaca saat ini belum tersedia. "
            "Silakan muat ulang dashboard atau cek koneksi ke BMKG."
        )

    weather_payload = context.get("weather") or {}
    maritime_payload = context.get("maritime") or {}

    if isinstance(weather_payload, dict) and "weather" in weather_payload:
        weather = weather_payload.get("weather") or {}
        location = weather_payload.get("location") or {}
    else:
        weather = weather_payload.get("weather") or {}
        location = {}

    if isinstance(maritime_payload, dict) and "forecast" in maritime_payload:
        maritime = maritime_payload.get("forecast") or {}
    else:
        maritime = maritime_payload or {}

    recommendation = context.get("recommendation") or {}
    reasoning = recommendation.get("reasoning") or {}
    fuzzy = recommendation.get("fuzzy") or {}

    village = location.get("village") or "lokasi yang dipantau"
    district = location.get("district") or ""
    city = location.get("city") or ""
    province = location.get("province") or ""

    place = ", ".join(
        part for part in [village, district, city, province] if part
    ) or "lokasi yang dipantau"

    temperature = weather.get("temperature")
    humidity = weather.get("humidity")
    precipitation = weather.get("precipitation")
    wind_speed = weather.get("wind_speed")
    cloud_cover = weather.get("cloud_cover")
    condition = weather.get("condition") or "-"

    wave_height = maritime.get("wave_height")
    wind_avg = maritime.get("wind_speed_avg")
    wind_max = maritime.get("wind_speed_max")
    ffx = maritime.get("ffx_category")

    hypothesis = reasoning.get("hypothesis") or "-"
    hypothesis_name = reasoning.get("hypothesis_name") or "Belum tersedia"
    confidence = reasoning.get("confidence")
    recommendation_text = reasoning.get("recommendation") or "Belum tersedia"
    classification = fuzzy.get("classification") or "-"

    base = (
        f"📍 Lokasi: {place}\n"
        f"🌤️ Kondisi: {condition}\n"
        f"🌡️ Suhu: {temperature if temperature is not None else '-'} °C | 💧 Kelembapan: {humidity if humidity is not None else '-'}%\n"
        f"🌧️ Curah Hujan: {precipitation if precipitation is not None else '-'} mm | 💨 Angin: {wind_speed if wind_speed is not None else '-'} km/jam\n"
        f"☁️ Tutupan Awan: {cloud_cover if cloud_cover is not None else '-'}%\n"
        f"🌊 Gelombang: {wave_height if wave_height is not None else '-'} m | 💨 Angin Rata-rata: {wind_avg if wind_avg is not None else '-'} knot | Maks: {wind_max if wind_max is not None else '-'} knot\n"
        f"📊 Kategori FFX: {ffx if ffx else '-'}\n\n"
        f"🔍 Analisis Sistem:\n"
        f"- Klasifikasi Fuzzy: {classification}\n"
        f"- Hipotesis Terpilih: {hypothesis} ({hypothesis_name})\n"
        f"- Confidence Level: {confidence if confidence is not None else '-'}%\n"
        f"- Rekomendasi: {recommendation_text}"
    )

    # Tentukan apakah aman melaut berdasarkan hypothesis
    is_safe_to_fish = hypothesis in ["H1", "H2"]
    is_potentially_dangerous = hypothesis in ["H3", "H4"]

    # Reasoning tentang aktivitas nelayan
    fishing_reasoning = ""
    
    if is_safe_to_fish:
        fishing_reasoning = (
            f"\n\n✅ ANALISIS MENGAPA PELAUT/NELAYAN BISA MELAKUKAN AKTIVITAS:\n"
            f"Berdasarkan hipotesis {hypothesis_name} dengan confidence {confidence}%, "
            f"kondisi cuaca dan maritim di {place} masih dalam kategori yang relatif aman untuk aktivitas melaut.\n\n"
            f"🎯 Alasan Utama Bisa Melaut/Memancing:\n"
            f"1. Gelombang rendah ({wave_height if wave_height is not None else 'moderat'} m) - "
            f"stabilitas kapal terjaga\n"
            f"2. Angin dalam batas aman ({wind_avg if wind_avg is not None else 'moderat'} knot rata-rata) - "
            f"operasional kapal lancar\n"
            f"3. Curah hujan minimal ({precipitation if precipitation is not None else 'sedikit'} mm) - "
            f"visibilitas baik\n"
            f"4. Kategori FFX {ffx or 'moderat'} - risiko relatif rendah\n\n"
            f"💡 Rekomendasi Aksi:\n"
            f"✓ Nelayan BISA berangkat untuk melaut/memancing\n"
            f"✓ Disarankan berangkat pagi untuk menghindari perubahan cuaca\n"
            f"✓ Tetap pantau prakiraan cuaca BMKG sebelum berangkat\n"
            f"✓ Pastikan kapal dan equipment dalam kondisi baik"
        )
    elif is_potentially_dangerous:
        fishing_reasoning = (
            f"\n\n⚠️ ANALISIS MENGAPA PELAUT/NELAYAN HARUS WASPADA/BATAL MELAUT:\n"
            f"Berdasarkan hipotesis {hypothesis_name} dengan confidence {confidence}%, "
            f"kondisi cuaca dan maritim di {place} menunjukkan risiko yang signifikan untuk aktivitas melaut.\n\n"
            f"🚫 Alasan Utama Tidak Disarankan/Dilarang Melaut:\n"
            f"1. Gelombang tinggi ({wave_height if wave_height is not None else 'tinggi'} m) - "
            f"risiko keselamatan kapal meningkat\n"
            f"2. Angin kuat ({wind_max if wind_max is not None else 'tinggi'} knot maksimal) - "
            f"navigasi sulit dan berbahaya\n"
            f"3. Curah hujan tinggi ({precipitation if precipitation is not None else 'tinggi'} mm) - "
            f"visibilitas terbatas\n"
            f"4. Kategori FFX {ffx or 'tinggi'} - risiko sangat tinggi\n\n"
            f"❌ Rekomendasi Aksi:\n"
            f"✗ Nelayan SEBAIKNYA TIDAK/BATAL berangkat untuk melaut/memancing\n"
            f"✗ Tunggu hingga kondisi cuaca membaik\n"
            f"✗ Jika terpaksa harus melaut, tingkatkan kewaspadaan dan siapkan protokol darurat\n"
            f"✗ Pastikan semua crew menguasai teknik penyelamatan diri"
        )
    else:
        fishing_reasoning = (
            f"\n\n🔎 ANALISIS KONDISI AKTIVITAS NELAYAN:\n"
            f"Berdasarkan hipotesis {hypothesis_name} dengan confidence {confidence}%, "
            f"sistem merekomendasikan: {recommendation_text}\n\n"
            f"Kondisi saat ini di {place} memerlukan pertimbangan khusus sebelum melaut."
        )

    # Selaraskan penjelasan AI dengan keputusan H1-H4. Faktor laut tetap
    # ditampilkan sebagai evidence tambahan, bukan alasan untuk mengganti
    # kelas cuaca utama.
    if hypothesis == "H1":
        fishing_reasoning = (
            f"\n\n✅ KESIMPULAN AKTIVITAS NELAYAN:\n"
            f"Kondisi cuaca di {place} masuk kelas TIDAK_HUJAN, sehingga "
            "keputusan sistem adalah H1: Aman melaut.\n\n"
            f"Evidence cuaca: curah hujan {precipitation if precipitation is not None else '-'} mm, "
            f"tutupan awan {cloud_cover if cloud_cover is not None else '-'}%, "
            f"dan kondisi {condition}.\n"
            f"Evidence laut: gelombang {wave_height if wave_height is not None else '-'} m, "
            f"angin rata-rata {wind_avg if wind_avg is not None else '-'} knot, "
            f"kategori FFX {ffx or '-'}. Data laut tetap perlu dipantau sebelum berangkat.\n\n"
            "💡 Tindakan: Nelayan dapat melaut, tetap membawa perlengkapan keselamatan "
            "dan mengikuti pembaruan BMKG."
        )
    elif hypothesis == "H2":
        fishing_reasoning = (
            f"\n\n⚠️ KESIMPULAN AKTIVITAS NELAYAN:\n"
            f"Kondisi cuaca di {place} masuk kelas MENDUNG, sehingga "
            "keputusan sistem adalah H2: Melaut dengan kewaspadaan.\n\n"
            f"Evidence cuaca: curah hujan {precipitation if precipitation is not None else '-'} mm, "
            f"tutupan awan {cloud_cover if cloud_cover is not None else '-'}%, "
            f"dan kondisi {condition}.\n"
            f"Periksa gelombang {wave_height if wave_height is not None else '-'} m dan "
            f"angin maksimum {wind_max if wind_max is not None else '-'} knot sebelum berangkat.\n\n"
            "💡 Tindakan: Batasi area dan durasi melaut, serta tingkatkan kewaspadaan."
        )
    elif hypothesis == "H3":
        fishing_reasoning = (
            f"\n\n⏸️ KESIMPULAN AKTIVITAS NELAYAN:\n"
            f"Kondisi cuaca di {place} masuk kelas HUJAN, sehingga "
            "keputusan sistem adalah H3: Menunda aktivitas melaut.\n\n"
            f"Evidence cuaca: curah hujan {precipitation if precipitation is not None else '-'} mm "
            f"dan kondisi {condition}. Hujan dapat menurunkan visibilitas dan kenyamanan operasi.\n"
            f"Data laut: gelombang {wave_height if wave_height is not None else '-'} m, "
            f"angin maksimum {wind_max if wind_max is not None else '-'} knot.\n\n"
            "💡 Tindakan: Tunda keberangkatan sampai hujan berhenti dan kondisi ditinjau ulang."
        )
    else:
        fishing_reasoning = (
            f"\n\n🚫 KESIMPULAN AKTIVITAS NELAYAN:\n"
            f"Kondisi cuaca di {place} masuk kelas EKSTREM, sehingga "
            "keputusan sistem adalah H4: Tidak disarankan melaut.\n\n"
            f"Evidence: kondisi {condition}, curah hujan {precipitation if precipitation is not None else '-'} mm, "
            f"angin maksimum {wind_max if wind_max is not None else '-'} knot, "
            f"dan gelombang {wave_height if wave_height is not None else '-'} m.\n\n"
            "💡 Tindakan: Jangan berangkat. Jika sudah berada di laut, segera menuju titik aman "
            "sesuai prosedur keselamatan."
        )

    # Tambahkan handling untuk pertanyaan spesifik
    if "memancing" in str(question).lower():
        return (
            base + fishing_reasoning + 
            f"\n\n📌 Khusus untuk aktivitas memancing:\n"
            f"- Waktu terbaik memancing biasanya pagi (5-9 AM) atau sore (4-7 PM)\n"
            f"- Lokasi memancing sebaiknya {'' if is_safe_to_fish else 'dekat pantai atau '}"
            f"di area dengan riwayat hasil tangkapan bagus\n"
            f"- Persiapkan perlengkapan sesuai prediksi gelombang dan angin"
        )

    if "nelayan" in str(question).lower() or "melaut" in str(question).lower():
        return base + fishing_reasoning

    if "hujan" in str(question).lower():
        return base + " Untuk pertanyaan tentang hujan: curah hujan saat ini adalah " + \
               f"{precipitation if precipitation is not None else '-'} mm. Hujan" + \
               (" akan menurunkan visibilitas dan meningkatkan risiko melaut." \
               if precipitation and precipitation > 1 else " masih dalam kondisi aman.")

    if "angin" in str(question).lower():
        return base + f" Untuk pertanyaan tentang angin: angin atmosfer saat ini {wind_speed if wind_speed is not None else '-'} km/jam " + \
               f"dengan angin maritim rata-rata {wind_avg if wind_avg is not None else '-'} knot dan maksimal {wind_max if wind_max is not None else '-'} knot. " + \
               ("Angin dalam kondisi kuat dan perlu kewaspadaan." if wind_max and wind_max > 15 else "Angin masih dalam batas operasional.")

    if "gelombang" in str(question).lower() or "ombak" in str(question).lower():
        return base + f" Untuk pertanyaan tentang gelombang: tinggi gelombang saat ini {wave_height if wave_height is not None else '-'} meter. " + \
               ("Gelombang tinggi, operasional terbatas dan berbahaya." if wave_height and wave_height > 2 else "Gelombang dalam kondisi operasional.")

    if "aman" in str(question).lower():
        return base + fishing_reasoning

    return base + fishing_reasoning


def call_openai_chat(question: str, context: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return build_grounded_ai_answer(question, context)

    prompt = (
        "Anda adalah asisten analisis cuaca untuk nelayan. "
        "Jawab dengan singkat, jelas, dan berbasis data saja. "
        "Gunakan konteks berikut sebagai sumber kebenaran: "
        f"{json.dumps(context, ensure_ascii=False)}\n\n"
        f"Pertanyaan pengguna: {question}"
    )

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Kamu adalah asisten cuaca dan keputusan melaut yang grounded pada data aktual."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=30
        )

        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()

    except Exception:
        return build_grounded_ai_answer(question, context)


load_dotenv()


app = FastAPI(
    title="Weather Reasoning AI",
    description="AI rekomendasi kondisi cuaca untuk nelayan",
    version="1.0.0"
)


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {
        "message": "Weather Reasoning AI API aktif"
    }


def get_all_weather_data(adm4=None, maritime_code=None):

    weather_data = get_weather_data(adm4=adm4)

    if weather_data is None:
        return None

    maritime_code = maritime_code or os.getenv(
        "BMKG_MARITIME_CODE"
    )

    maritime_data = get_maritime_data(
        maritime_code
    )

    return {
        "atmosphere": weather_data,
        "maritime": maritime_data
    }


@app.get("/api/regions/provinces")
def regions_provinces():
    """Get all provinces (level 1)."""
    return {
        "success": True,
        "data": get_all_provinces()
    }


@app.get("/api/regions/kabupaten")
def regions_kabupaten(province_code: str = None):
    """Get kabupaten/kota by province code (level 2)."""
    if not province_code:
        return {
            "success": False,
            "message": "province_code wajib diisi"
        }

    return {
        "success": True,
        "data": get_kabupaten_by_province(province_code)
    }


@app.get("/api/regions/kecamatan")
def regions_kecamatan(kabupaten_code: str = None):
    """Get kecamatan by kabupaten code (level 3)."""
    if not kabupaten_code:
        return {
            "success": False,
            "message": "kabupaten_code wajib diisi"
        }

    return {
        "success": True,
        "data": get_kecamatan_by_kabupaten(kabupaten_code)
    }


@app.get("/api/regions/desa")
def regions_desa(kecamatan_code: str = None):
    """Get desa/kelurahan by kecamatan code (level 4)."""
    if not kecamatan_code:
        return {
            "success": False,
            "message": "kecamatan_code wajib diisi"
        }

    return {
        "success": True,
        "data": get_desa_by_kecamatan(kecamatan_code)
    }


@app.get("/api/locations")
def locations():
    return {
        "success": True,
        "locations": get_bmkg_location_catalog()
    }


@app.get("/api/location/{adm4}")
def location_by_adm4(adm4: str):
    """Get location info by ADM4 code."""
    loc = get_location_by_adm4(adm4)
    if loc is None:
        return {
            "success": False,
            "message": f"Lokasi dengan adm4 {adm4} tidak ditemukan"
        }
    
    return {
        "success": True,
        "location": loc
    }


@app.get("/api/weather")
def weather(adm4: str = None, maritime_code: str = None):

    data = get_all_weather_data(
        adm4=adm4,
        maritime_code=maritime_code
    )

    if data is None:
        return {
            "success": False,
            "message": "Gagal mengambil data BMKG"
        }

    return {
        "success": True,
        "data": data
    }


@app.get("/api/fuzzy")
def fuzzy():

    data = get_all_weather_data()

    if data is None:
        return {
            "success": False,
            "message": "Gagal mengambil data BMKG"
        }

    weather = data["atmosphere"]["weather"]

    fuzzy_result = classify_weather(
        precipitation=weather["precipitation"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],
        cloud_cover=weather["cloud_cover"],
        weather_condition=weather["condition"]
    )

    return {
        "success": True,
        "weather": data["atmosphere"],
        "maritime": data["maritime"],
        "fuzzy": fuzzy_result
    }


@app.get("/api/recommendation")
def recommendation(
    fisherman_status: str = "belum_berangkat",
    adm4: str = None,
    maritime_code: str = None
):

    allowed_status = [
        "belum_berangkat",
        "sudah_melaut"
    ]

    if fisherman_status not in allowed_status:
        return {
            "success": False,
            "message": (
                "fisherman_status harus "
                "'belum_berangkat' atau 'sudah_melaut'"
            )
        }

    data = get_all_weather_data(
        adm4=adm4,
        maritime_code=maritime_code
    )

    if data is None:
        return {
            "success": False,
            "message": "Gagal mengambil data BMKG"
        }

    weather_data = data["atmosphere"]
    maritime_data = data["maritime"]

    if maritime_data is None:
        return {
            "success": False,
            "message": "Data maritim BMKG tidak tersedia"
        }

    weather = weather_data["weather"]
    forecast = maritime_data["forecast"]
    hazards = maritime_data["hazards"]

    fuzzy_result = classify_weather(
        precipitation=weather["precipitation"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],
        cloud_cover=weather["cloud_cover"],
        weather_condition=weather["condition"]
    )

    wind_speed_avg = forecast.get(
        "wind_speed_avg"
    )

    wind_speed_max = forecast.get(
        "wind_speed_max"
    )

    wave_height = forecast.get(
        "wave_height"
    )

    ffx_category = forecast.get(
        "ffx_category"
    )

    if wind_speed_avg is None:
        return {
            "success": False,
            "message": (
                "Data kecepatan angin rata-rata "
                "tidak tersedia"
            )
        }

    if wave_height is None:
        return {
            "success": False,
            "message": (
                "Data tinggi gelombang "
                "tidak tersedia"
            )
        }

    if ffx_category is None:
        return {
            "success": False,
            "message": (
                "Kategori angin maksimum "
                "tidak tersedia"
            )
        }

    reasoning_result = calculate_reasoning(

        fuzzy_result=fuzzy_result,

        precipitation=weather["precipitation"],

        humidity=weather["humidity"],

        wind_speed_knots=wind_speed_avg,

        ffx_category=ffx_category,

        wave_height=wave_height,

        lightning=hazards.get(
            "lightning"
        ),

        visibility_bad=hazards.get(
            "visibility_bad"
        ),

        breaking_wave=hazards.get(
            "breaking_wave"
        ),

        weather_condition=weather["condition"],

        fisherman_status=fisherman_status
    )

    return {

        "success": True,

        "weather": weather_data,

        "maritime": maritime_data,

        "fuzzy": fuzzy_result,

        "reasoning": reasoning_result,

        "derived": {

            "wind_speed_knots": wind_speed_avg,

            "wind_speed_max_knots": wind_speed_max,

            "wave_height_m": wave_height
        }
    }


@app.post("/api/location/nearest")
def nearest_location(payload: dict):
    lat = (payload or {}).get("latitude")
    lon = (payload or {}).get("longitude")

    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="latitude dan longitude wajib diisi")

    match = find_nearest_location(lat, lon)
    if match is None:
        return {
            "success": False,
            "message": "Tidak dapat menemukan lokasi BMKG terdekat"
        }

    return {
        "success": True,
        "location": match
    }


@app.post("/api/ai-chat")
def ai_chat(payload: dict):
    question = str((payload or {}).get("question") or "").strip()

    if not question:
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")

    adm4 = (payload or {}).get("adm4")
    maritime_code = (payload or {}).get("maritime_code")

    data = get_all_weather_data(
        adm4=adm4,
        maritime_code=maritime_code
    )
    if data is None:
        return {
            "success": False,
            "message": "Data cuaca BMKG tidak tersedia saat ini."
        }

    recommendation_result = recommendation(
        fisherman_status="belum_berangkat",
        adm4=(payload or {}).get("adm4"),
        maritime_code=(payload or {}).get("maritime_code")
    )

    context = {
        "weather": data.get("atmosphere") or {},
        "maritime": data.get("maritime") or {},
        "recommendation": recommendation_result if isinstance(recommendation_result, dict) else {}
    }

    answer = call_openai_chat(question, context)

    return {
        "success": True,
        "answer": answer,
        "context": context
    }


@app.get("/api/test-reasoning")
def test_reasoning():

    scenarios = [
        {
            "name": "H1 - Relatif Aman",
            "status": "belum_berangkat",
            "wind": 8,
            "ffx": "rendah",
            "wave": 0.5
        },
        {
            "name": "H2 - Perlu Kewaspadaan",
            "status": "belum_berangkat",
            "wind": 13,
            "ffx": "sedang",
            "wave": 1.0
        },
        {
            "name": "H3 - Tidak Aman Berangkat",
            "status": "belum_berangkat",
            "wind": 26,
            "ffx": "tinggi",
            "wave": 2.5
        },
        {
            "name": "H4 - Berbahaya Saat di Laut",
            "status": "sudah_melaut",
            "wind": 26,
            "ffx": "tinggi",
            "wave": 2.5
        }
    ]

    results = []

    fuzzy_dummy = {
        "classification": ""
    }

    for scenario in scenarios:

        result = calculate_reasoning(
            fuzzy_result=fuzzy_dummy,

            precipitation=0,

            humidity=68,

            wind_speed_knots=scenario["wind"],

            ffx_category=scenario["ffx"],

            wave_height=scenario["wave"],

            fisherman_status=scenario["status"]
        )

        results.append({

            "scenario": scenario["name"],

            "input": {
                "status": scenario["status"],
                "wind_speed_avg": scenario["wind"],
                "ffx_category": scenario["ffx"],
                "wave_height": scenario["wave"]
            },

            "output": {
                "hypothesis": result["hypothesis"],
                "hypothesis_name": result["hypothesis_name"],
                "confidence": result["confidence"],
                "scores": result["scores"]
            }

        })

    return {
        "success": True,
        "results": results
    }