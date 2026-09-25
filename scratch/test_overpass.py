import urllib.request
import urllib.parse
import json

lat, lon = 28.6139, 77.2090
query = f"""
[out:json][timeout:10];
(
  node["amenity"="hospital"](around:8000,{lat},{lon});
  way["amenity"="hospital"](around:8000,{lat},{lon});
  node["amenity"="clinic"](around:8000,{lat},{lon});
  node["emergency"="ambulance_station"](around:8000,{lat},{lon});
);
out center 10;
"""

url = "https://overpass-api.de/api/interpreter"
req = urllib.request.Request(
    url, 
    data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
    headers={"User-Agent": "MindBridge-Healthcare-Platform/2.0"}
)

try:
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Success! Found {len(elements)} real providers:")
        for el in elements[:5]:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en")
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if name:
                print(f" - {name} ({el_lat}, {el_lon}) | Phone: {tags.get('phone') or tags.get('contact:phone')}")
except Exception as e:
    print("Overpass error:", e)
