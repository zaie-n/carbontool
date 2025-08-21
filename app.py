import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math

# ------------------ CONSTANTS ------------------
A1_PER_DU = -43.95
A2_PER_DU = 8.42
A5_PER_DU = 42.44
B1_PER_DU = -31.70
C_PER_DU  = 11.94

MASS_T_PER_DU = 0.0617   # tonnes per DU
EF_TRUCK = 0.08          # kg CO2e per t·km

PORT_LAT, PORT_LON = 40.6840, -74.1419  # Port Newark, NJ

# ------------------ HELPERS ------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_latlon_from_zip(zipcode):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zipcode}&country=USA&format=json"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "streamlit-app"})
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass
    return PORT_LAT, PORT_LON

def get_driving_distance(lat, lon):
    url = f"http://router.project-osrm.org/route/v1/driving/{PORT_LON},{PORT_LAT};{lon},{lat}?overview=false"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data["routes"][0]["distance"] / 1000  # meters → km
    except:
        pass
    # fallback: haversine × 1.2
    return haversine(PORT_LAT_
