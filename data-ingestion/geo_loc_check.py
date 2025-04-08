import googlemaps

with open("gmaps_api_key.txt") as f:
    key = f.read().strip()

gmaps = googlemaps.Client(key=key)
results = gmaps.geocode("Cambridge, MA")
print(results[0]["geometry"]["location"])