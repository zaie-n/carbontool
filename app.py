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
    return haversine(PORT_LAT, PORT_LON, lat, lon) * 1.2

def calc_A4(DU, dist_km):
    tonne_km = (DU * MASS_T_PER_DU) * dist_km
    return tonne_km * EF_TRUCK

# ------------------ STYLING ------------------
st.set_page_config(page_title="Hempcrete Carbon Calculator", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: #F7F4EF;
        font-family: "Helvetica Neue", sans-serif;
    }
    h1, h2, h3 {
        color: #2E5041;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #2E5041;
        color: white;
        border-radius: 12px;
        padding: 0.6em 1.2em;
        font-size: 1em;
    }
    .stButton>button:hover {
        background-color: #3c6d57;
        color: #fff;
    }
    .result-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .result-value {
        font-size: 2em;
        font-weight: bold;
        color: #2E5041;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ UI ------------------
st.title("🌿 Hempcrete Net Carbon Storage Calculator")

col1, col2 = st.columns([2,1])
with col1:
    wall_area = st.number_input("Wall area (ft²)", min_value=1, value=1000, step=10)
    zipcode = st.text_input("ZIP Code", value="10007")
with col2:
    st.write("This calculator estimates **net carbon storage** over the lifecycle of your hempcrete wall project. \
             Enter your wall area and project ZIP code to get started.")

if st.button("Calculate"):
    # Convert to DU
    DU = wall_area * 0.092903
    
    # Geocode
    lat, lon = get_latlon_from_zip(zipcode)
    dist_km = get_driving_distance(lat, lon)
    
    # Modules
    A1 = DU * A1_PER_DU
    A2 = DU * A2_PER_DU
    A4 = calc_A4(DU, dist_km)
    A5 = DU * A5_PER_DU
    B1 = DU * B1_PER_DU
    C  = DU * C_PER_DU
    
    total = A1 + A2 + A4 + A5 + B1 + C
    
    # ------------------ RESULTS ------------------
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(f'<div class="result-card"><h3>Net Carbon Storage</h3><div class="result-value">{total:.1f} kg CO₂e</div></div>', unsafe_allow_html=True)
    with colB:
        st.markdown(f'<div class="result-card"><h3>Declared Units (DU)</h3><div class="result-value">{DU:.2f}</div></div>', unsafe_allow_html=True)
    with colC:
        st.markdown(f'<div class="result-card"><h3>Truck Distance</h3><div class="result-value">{dist_km:.1f} km</div></div>', unsafe_allow_html=True)

    # ------------------ CHART ------------------
    df = pd.DataFrame({
        "Module": ["A1 Raw materials","A2 Upstream transport","A4 Site transport",
                   "A5 Installation","B1 Use phase","C1–C4 End-of-life"],
        "kgCO2e": [A1, A2, A4, A5, B1, C]
    })
    fig = px.bar(df, x="Module", y="kgCO2e",
                 text="kgCO2e", color="Module",
                 color_discrete_sequence=["#2E5041","#6B8F71","#C4B6A6","#88A093","#B6A19E","#F2E8CF"])
    fig.update_layout(title="Lifecycle Module Breakdown", yaxis_title="kg CO₂e", template="simple_white",
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------ DETAILS ------------------
    st.subheader("Calculation details")
    st.code(f"""
DU = wall_area_ft² × 0.092903
A1 = DU × {A1_PER_DU}
A2 = DU × {A2_PER_DU}
A4 = (DU × {MASS_T_PER_DU} t) × distance_km × {EF_TRUCK}
A5 = DU × {A5_PER_DU}
B1 = DU × {B1_PER_DU}
C1–C4 = DU × {C_PER_DU}
    """)
