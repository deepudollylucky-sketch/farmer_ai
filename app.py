import csv
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, render_template

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "market_prices.csv"

# OpenWeather API key: default to the provided value, but allow override via env
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


HASSAN_LAT = 13.0056
HASSAN_LON = 76.1025

KARNATAKA_DISTRICTS = [
    "Bagalkot",
    "Ballari",
    "Belagavi",
    "Bengaluru Rural",
    "Bengaluru Urban",
    "Bidar",
    "Chamarajanagara",
    "Chikkaballapura",
    "Chikkamagaluru",
    "Chitradurga",
    "Dakshina Kannada",
    "Davanagere",
    "Dharwad",
    "Gadag",
    "Hassan",
    "Haveri",
    "Kalaburagi",
    "Kodagu",
    "Kolar",
    "Koppal",
    "Mandya",
    "Mysuru",
    "Raichur",
    "Ramanagara",
    "Shivamogga",
    "Tumakuru",
    "Udupi",
    "Uttara Kannada",
    "Vijayapura",
    "Vijayanagara",
    "Yadgir",
]

KARNATAKA_DISTRICT_LOOKUP = {district.casefold(): district for district in KARNATAKA_DISTRICTS}

app = Flask(__name__)

MARKETS = {
    "Hassan APMC": {"distance_km": 18, "transport_per_quintal": 30, "other_cost": 0},
    "Belur Market": {"distance_km": 24, "transport_per_quintal": 26, "other_cost": 100},
    "Arasikere Market": {"distance_km": 42, "transport_per_quintal": 24, "other_cost": 150},
    "Channarayapatna Market": {"distance_km": 58, "transport_per_quintal": 22, "other_cost": 200},
}

WEATHER = [
    {"day": "Today", "date_offset": 0, "condition": "Partly cloudy", "rainfall_mm": 2, "temp_c": 27, "humidity_pct": 68, "alert": "Clear travel window"},
    {"day": "Tomorrow", "date_offset": 1, "condition": "Rain showers", "rainfall_mm": 18, "temp_c": 25, "humidity_pct": 82, "alert": "Transport caution"},
    {"day": "Friday", "date_offset": 2, "condition": "Cloudy", "rainfall_mm": 7, "temp_c": 26, "humidity_pct": 75, "alert": "Good for covered storage"},
]

# --- Weather Functions ---
DISTRICT_COORDINATES = {
    "Bagalkot": {"lat": 16.17, "lon": 75.70},
    "Ballari": {"lat": 15.14, "lon": 76.92},
    "Belagavi": {"lat": 15.85, "lon": 74.50},
    "Bengaluru Rural": {"lat": 13.29, "lon": 77.55},
    "Bengaluru Urban": {"lat": 12.97, "lon": 77.59},
    "Bidar": {"lat": 17.91, "lon": 77.52},
    "Chamarajanagara": {"lat": 11.92, "lon": 76.94},
    "Chikkaballapura": {"lat": 13.44, "lon": 78.05},
    "Chikkamagaluru": {"lat": 13.32, "lon": 75.77},
    "Chitradurga": {"lat": 14.23, "lon": 76.40},
    "Dakshina Kannada": {"lat": 12.84, "lon": 74.84},
    "Davanagere": {"lat": 14.47, "lon": 75.92},
    "Dharwad": {"lat": 15.46, "lon": 75.00},
    "Gadag": {"lat": 15.43, "lon": 75.63},
    "Hassan": {"lat": 13.0056, "lon": 76.1025},
    "Haveri": {"lat": 14.80, "lon": 75.40},
    "Kalaburagi": {"lat": 17.33, "lon": 76.83},
    "Kodagu": {"lat": 12.42, "lon": 75.73},
    "Kolar": {"lat": 13.14, "lon": 78.13},
    "Koppal": {"lat": 15.35, "lon": 76.15},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394},
    "Mandya": {"lat": 12.5242, "lon": 76.8951},
    "Raichur": {"lat": 16.21, "lon": 77.35},
    "Ramanagara": {"lat": 12.72, "lon": 77.28},
    "Shivamogga": {"lat": 13.93, "lon": 75.57},
    "Tumakuru": {"lat": 13.34, "lon": 77.10},
    "Udupi": {"lat": 13.3409, "lon": 74.7421},
    "Uttara Kannada": {"lat": 14.81, "lon": 74.12},
    "Vijayapura": {"lat": 16.83, "lon": 75.71},
    "Vijayanagara": {"lat": 15.27, "lon": 76.39},
    "Yadgir": {"lat": 16.77, "lon": 77.14},
}

CROP_CATALOG = [
    {"crop": "Tomato", "reason": "Warm-season vegetable with strong sample market demand.", "season": "Kharif and Rabi", "soil": "Loamy or red soil", "water": "Regular irrigation", "yield": 120, "cost": 80000, "price": 2800},
    {"crop": "Onion", "reason": "Suitable for well-drained soil and dry harvest weather.", "season": "Rabi", "soil": "Loamy or black soil", "water": "Moderate irrigation", "yield": 80, "cost": 65000, "price": 2200},
    {"crop": "Potato", "reason": "Performs best in cool-season conditions and loose soil.", "season": "Rabi", "soil": "Loamy soil", "water": "Regular irrigation", "yield": 100, "cost": 90000, "price": 1950},
    {"crop": "Brinjal", "reason": "Long-season vegetable that tolerates a range of local conditions.", "season": "Kharif and Rabi", "soil": "Loamy soil", "water": "Moderate irrigation", "yield": 90, "cost": 70000, "price": 2200},
    {"crop": "Chili", "reason": "Warm-weather crop; avoid waterlogging and provide steady moisture.", "season": "Kharif", "soil": "Black or red soil", "water": "Moderate irrigation", "yield": 18, "cost": 55000, "price": 3800},
    {"crop": "Okra", "reason": "Heat-tolerant crop that can suit a range of Karnataka districts.", "season": "Kharif and summer", "soil": "Loamy or sandy soil", "water": "Moderate irrigation", "yield": 50, "cost": 45000, "price": 3000},
    {"crop": "Beans", "reason": "Short-duration vegetable suited to cooler or moderate conditions.", "season": "Rabi", "soil": "Loamy soil", "water": "Regular irrigation", "yield": 45, "cost": 50000, "price": 3200},
    {"crop": "Cabbage", "reason": "Cool-season crop with better performance in higher-elevation areas.", "season": "Rabi", "soil": "Loamy soil", "water": "Regular irrigation", "yield": 90, "cost": 75000, "price": 1800},
    {"crop": "Carrot", "reason": "Cool-season root crop that needs loose, well-drained soil.", "season": "Rabi", "soil": "Sandy or loamy soil", "water": "Regular irrigation", "yield": 75, "cost": 70000, "price": 2400},
    {"crop": "Cauliflower", "reason": "Cool-season vegetable suited to loamy soils and reliable moisture.", "season": "Rabi", "soil": "Loamy soil", "water": "Regular irrigation", "yield": 80, "cost": 72000, "price": 2500},
    {"crop": "Ragi", "reason": "Drought-tolerant millet well suited to many rain-fed areas.", "season": "Kharif", "soil": "Red or loamy soil", "water": "Low to moderate water", "yield": 14, "cost": 18000, "price": 3800},
    {"crop": "Paddy", "reason": "Staple crop suited to areas with dependable water and suitable fields.", "season": "Kharif", "soil": "Clay or loamy soil", "water": "High water availability", "yield": 25, "cost": 42000, "price": 2400},
    {"crop": "Maize", "reason": "Versatile cereal crop with broad district suitability.", "season": "Kharif and Rabi", "soil": "Loamy or black soil", "water": "Moderate water", "yield": 30, "cost": 28000, "price": 2200},
    {"crop": "Groundnut", "reason": "Oilseed crop suited to well-drained sandy and red soils.", "season": "Kharif and Rabi", "soil": "Sandy or red soil", "water": "Low to moderate water", "yield": 12, "cost": 26000, "price": 6500},
    {"crop": "Tur (Pigeon Pea)", "reason": "Deep-rooted pulse that performs well in rain-fed conditions.", "season": "Kharif", "soil": "Black or red soil", "water": "Low to moderate water", "yield": 8, "cost": 22000, "price": 8200},
]

DRY_DISTRICTS = {"Bagalkot", "Ballari", "Bidar", "Dharwad", "Gadag", "Kalaburagi", "Koppal", "Raichur", "Vijayapura", "Yadgir", "Vijayanagara"}
COASTAL_DISTRICTS = {"Dakshina Kannada", "Udupi", "Uttara Kannada"}
MALNAD_DISTRICTS = {"Chikkamagaluru", "Kodagu", "Shivamogga"}


def live_weather_outlook(lat=None, lon=None):
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OpenWeather API key not configured")

    lat = lat if lat is not None else HASSAN_LAT
    lon = lon if lon is not None else HASSAN_LON

    url = (
        "https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&units=metric&cnt=9&appid={OPENWEATHER_API_KEY}"
    )
    request = Request(url, headers={"User-Agent": "Fieldwise/1.0"})
    with urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))

    outlook = []
    for index, entry in enumerate(payload.get("list", [])[:3]):
        forecast_dt = datetime.fromtimestamp(entry["dt"])
        rain = float(entry.get("rain", {}).get("3h", 0.0))
        main = entry.get("main", {})
        weather = entry.get("weather", [{}])[0]
        outlook.append({
            "day": ("Today", "Tomorrow", "Friday")[index] if index < 3 else forecast_dt.strftime("%A"),
            "date_offset": index,
            "condition": weather.get("description", "Partly cloudy").title(),
            "rainfall_mm": round(rain),
            "temp_c": round(float(main.get("temp", 27.0))),
            "humidity_pct": int(main.get("humidity", 70)),
            "alert": "Clear travel window" if rain < 5 else "Transport caution" if rain < 15 else "Heavy rain alert",
            "date": forecast_dt.strftime("%d %b"),
        })
    if not outlook:
        raise ValueError("No forecast data available from OpenWeather")
    return outlook


def weather_outlook_for(district_name="Hassan"):
    coords = DISTRICT_COORDINATES.get(district_name, DISTRICT_COORDINATES["Hassan"])
    try:
        return live_weather_outlook(coords["lat"], coords["lon"])
    except (RuntimeError, ValueError, URLError, TimeoutError):
        return WEATHER


def weather_outlook():
    return weather_outlook_for("Hassan")


def market_price_profiles():
    samples = {}
    with DATA_PATH.open("r", newline="", encoding="utf-8") as csvfile:
        for row in csv.DictReader(csvfile):
            samples.setdefault(row["crop"].casefold(), []).append(row)

    profiles = {}
    for crop in CROP_CATALOG:
        crop_rows = samples.get(crop["crop"].casefold(), [])
        if not crop_rows:
            profiles[crop["crop"].casefold()] = {
                "price": crop["price"],
                "min_price": round(crop["price"] * 0.85 / 10) * 10,
                "max_price": round(crop["price"] * 1.05 / 10) * 10,
                "date": datetime.now().date().isoformat(),
            }
            continue

        latest_date = max(row["date"] for row in crop_rows)
        latest_prices = [int(row["price_per_quintal"]) for row in crop_rows if row["date"] == latest_date]
        all_prices = [int(row["price_per_quintal"]) for row in crop_rows]
        profiles[crop["crop"].casefold()] = {
            "price": round(sum(latest_prices) / len(latest_prices)),
            "min_price": min(all_prices),
            "max_price": max(all_prices),
            "date": latest_date,
        }
    return profiles


def crop_recommendations(district, soil_type, water_availability, land_area):
    district_name = (district or "Hassan").strip() or "Hassan"
    soil = (soil_type or "Black Soil").casefold()
    water = (water_availability or "Some Water Available").casefold()
    area = float(land_area or 4.8)
    profiles = market_price_profiles()
    scored = []

    for crop in CROP_CATALOG:
        fit_score = 55
        preferred_soils = crop["soil"].casefold().split(" or ")
        if any(preferred_soil in soil for preferred_soil in preferred_soils):
            fit_score += 20
        else:
            fit_score += 5

        drought_tolerant = crop["crop"] in {"Ragi", "Groundnut", "Tur (Pigeon Pea)"}
        if "no water" in water or "limited" in water:
            fit_score += 15 if drought_tolerant else 3
        elif "plenty" in water:
            fit_score += 15 if "high" in crop["water"].casefold() or "regular" in crop["water"].casefold() else 9
        else:
            fit_score += 10

        if district_name in COASTAL_DISTRICTS:
            fit_score += 12 if crop["crop"] in {"Paddy", "Chili", "Beans"} else 2
        elif district_name in MALNAD_DISTRICTS:
            fit_score += 12 if crop["crop"] in {"Paddy", "Maize", "Potato", "Beans"} else 3
        elif district_name in DRY_DISTRICTS:
            fit_score += 12 if crop["crop"] in {"Ragi", "Maize", "Groundnut", "Tur (Pigeon Pea)", "Chili"} else 3
        else:
            fit_score += 10 if crop["crop"] in {"Ragi", "Maize", "Tomato", "Groundnut"} else 5

        profile = profiles[crop["crop"].casefold()]
        estimated_profit = crop["yield"] * profile["price"] - crop["cost"]
        scored.append({
            **crop,
            "price_per_quintal": profile["price"],
            "estimated_profit_per_acre": estimated_profit,
            "fit_score": fit_score,
        })

    profits = [item["estimated_profit_per_acre"] for item in scored]
    minimum_profit = min(profits)
    profit_span = max(profits) - minimum_profit or 1
    for item in scored:
        profit_score = (item["estimated_profit_per_acre"] - minimum_profit) / profit_span * 100
        item["score"] = round(item["fit_score"] * 0.8 + profit_score * 0.2)

    return sorted(scored, key=lambda item: (item["score"], item["estimated_profit_per_acre"]), reverse=True)


def district_distance_km(origin, destination):
    origin_coords = DISTRICT_COORDINATES[origin]
    destination_coords = DISTRICT_COORDINATES[destination]
    earth_radius_km = 6371
    lat1, lat2 = math.radians(origin_coords["lat"]), math.radians(destination_coords["lat"])
    lat_delta = lat2 - lat1
    lon_delta = math.radians(destination_coords["lon"] - origin_coords["lon"])
    distance = 2 * earth_radius_km * math.asin(math.sqrt(
        math.sin(lat_delta / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(lon_delta / 2) ** 2
    ))
    return round(distance, 1)


def district_market_rows(crop_name, farm_district, land_area):
    profiles = market_price_profiles()
    profile = profiles.get(str(crop_name).casefold(), profiles["tomato"])
    area = float(land_area or 4.8)
    harvest = area * 20
    cultivation_cost = area * 25000
    crop_offset = sum(str(crop_name).casefold().encode("utf-8"))
    rows = []

    for index, district in enumerate(KARNATAKA_DISTRICTS):
        variation = (((index * 7 + crop_offset) % 9) - 4) * 0.015
        price = round(profile["price"] * (1 + variation) / 10) * 10
        minimum = round(profile["min_price"] * (1 + variation) / 10) * 10
        maximum = round(profile["max_price"] * (1 + variation) / 10) * 10
        distance = district_distance_km(farm_district, district)
        travel = distance * 25 * 2
        rows.append({
            "market": f"{district} APMC",
            "district": district,
            "date": profile["date"],
            "min_price": minimum,
            "max_price": maximum,
            "price_per_quintal": price,
            "distance_km": distance,
            "travel_cost": round(travel),
            "net_return": round(harvest * price - cultivation_cost - travel),
        })
    return sorted(rows, key=lambda row: row["net_return"], reverse=True)

# --- Routes ---
@app.get("/")
def home():
    return render_template("index.html", districts=KARNATAKA_DISTRICTS)


def farm_details_from_form(form):
    raw_district = str(form.get("district", "")).strip()
    district = KARNATAKA_DISTRICT_LOOKUP.get(raw_district.casefold())
    if not district:
        return None, "Please choose a valid Karnataka district."

    try:
        land_area = float(form.get("landArea", 0))
    except (TypeError, ValueError):
        return None, "Enter a valid land area."
    if land_area <= 0:
        return None, "Land area must be greater than zero."

    return {
        "district": district,
        "taluk": str(form.get("taluk", "")).strip(),
        "village": str(form.get("village", "")).strip(),
        "land_area": land_area,
        "soil_type": str(form.get("soilType", "Black Soil")).strip(),
        "water_availability": str(form.get("waterAvailability", "Some Water Available")).strip(),
    }, None


@app.post("/recommendations")
def recommendations_page():
    farm, error = farm_details_from_form(request.form)
    if error:
        return render_template("index.html", districts=KARNATAKA_DISTRICTS, error=error), 400

    recommendations = crop_recommendations(
        farm["district"], farm["soil_type"], farm["water_availability"], farm["land_area"]
    )
    return render_template(
        "recommendations.html",
        farm=farm,
        weather=weather_outlook_for(farm["district"]),
        recommendations=recommendations,
    )


@app.post("/markets")
def markets_page():
    farm, error = farm_details_from_form(request.form)
    if error:
        return render_template("index.html", districts=KARNATAKA_DISTRICTS, error=error), 400

    crop_name = str(request.form.get("crop", "")).strip()
    crop = next((item for item in CROP_CATALOG if item["crop"].casefold() == crop_name.casefold()), None)
    if not crop:
        return render_template("index.html", districts=KARNATAKA_DISTRICTS, error="Please select a recommended crop."), 400

    return render_template(
        "markets.html",
        farm=farm,
        crop=crop,
        market_rows=district_market_rows(crop["crop"], farm["district"], farm["land_area"]),
    )


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    crop = str(payload.get("crop", "Tomato")).strip() or "Tomato"
    raw_location = str(payload.get("location", "Hassan")).strip() or "Hassan"
    soil_type = str(payload.get("soilType", "Black Soil")).strip() or "Black Soil"
    water_availability = str(payload.get("waterAvailability", "Some Water Available")).strip() or "Some Water Available"
    land_area = payload.get("landArea", 4.8)
    try:
        quantity = max(0.1, float(payload.get("quantity", 10)))
        area = float(land_area)
    except (TypeError, ValueError):
        return jsonify({"error": "Quantity and land area must be positive numbers."}), 400

    canonical_location = KARNATAKA_DISTRICT_LOOKUP.get(raw_location.casefold()) or raw_location
    if canonical_location not in KARNATAKA_DISTRICTS:
        return jsonify({"error": "Please choose a valid Karnataka district."}), 400

    with DATA_PATH.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    for row in rows:
        row["date"] = datetime.strptime(row["date"], "%Y-%m-%d").date()
    if rows:
        min_date = min(row["date"] for row in rows)
        for row in rows:
            row["day_index"] = (row["date"] - min_date).days

    market_rows = district_market_rows(crop, canonical_location, area)

    recommendations = crop_recommendations(canonical_location, soil_type, water_availability, area)
    return jsonify({
        "crop": crop.title(),
        "location": f"{canonical_location}, Karnataka",
        "quantity": quantity,
        "land_area": area,
        "soilType": soil_type,
        "waterAvailability": water_availability,
        "weather": weather_outlook_for(canonical_location),
        "recommended_crops": recommendations,
        "market_rows": market_rows,
    })

if __name__ == "__main__":
    print("🚀 Starting Fieldwise Flask app with OpenWeather API...")
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
