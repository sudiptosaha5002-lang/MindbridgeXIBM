import urllib.request
import json

cities = [
    ("Delhi", 28.6139, 77.2090),
    ("Kolkata", 22.5626, 88.3630),
    ("Bengaluru", 12.9716, 77.5946),
    ("Mumbai", 19.0760, 72.8777)
]

print("=" * 60)
print("TESTING LOCATION-BASED EMERGENCY PROVIDERS DISPATCH API")
print("=" * 60)

for name, lat, lon in cities:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/emergency/nearest-ambulance",
        data=json.dumps({"lat": lat, "lon": lon, "locality": name}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"\n[CITY: {name}] ({lat}, {lon})")
        print(f" Detected Address : {data.get('user_location', {}).get('address')}")
        nearest = data.get("nearest", {})
        print(f" Nearest Provider : {nearest.get('name')}")
        print(f" Distance & ETA   : {nearest.get('distance_km')} km | ETA: {nearest.get('eta')}")
        print(f" Emergency Phone  : {nearest.get('phone_display')}")
        print(f" Google Maps Nav  : {nearest.get('google_maps_directions')}")
        providers = data.get("nearby_providers", [])
        print(f" Total Providers  : {len(providers)}")
        for idx, p in enumerate(providers[:4], 1):
            print(f"   {idx}. {p['name']} ({p['distance_km']} km away, ETA {p['eta']}) [Call: {p['primary_phone']}]")

print("\n" + "=" * 60)
print("ALL CITIES TESTED SUCCESSFULLY")
print("=" * 60)
