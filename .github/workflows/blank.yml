# app.py – Hempcrete Net Carbon Storage Calculator
# Run with: streamlit run app.py

import math
import os
import requests
import pgeocode
import pandas as pd
import streamlit as st
import plotly.express as px

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Hempcrete Carbon Storage", page_icon="🌿", layout="wide")

PRIMARY = "#2E5041"  # deep hemp green
ACCENT = "#8A9A5B"   # sage
SAND = "#F7F4EF"     # warm neutral

# ------------------ STYLES ------------------
st.markdown(
    f"""
    <style>
    .stApp {{ background:{SAND}; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
    h1, h2, h3, h4, h5, h6 {{ color:{PRIMARY}; font-family: 'Helvetica Neue', Arial, sans-serif; }}
    .ameri-hero {{
        background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(247,244,239,0.95)),
        url('https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1600&auto=format&fit=crop');
        background-size: cover; background-position: center; border-radius: 18px; padding: 3rem; margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    }}
    .stButton>button {{ background:{ACCENT}; color:white; border:0; border-radius:12px; padding:0.6rem 1rem; font-weight:600; }}
    .stButton>button:hover {{ background:{PRIMARY}; }}
    .metric-card {{ border-radius:16px; padding:1rem; background:white; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }}
    .pill {{ display:inline-block; padding:0.25rem 0.6rem; border-radius:999px; background:{PRIMARY}; color:white; font-size:0.8rem; margin-right:0.5rem; }}
    .small {{ color:#4b5d55; font-size:0.9rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------ CONSTANTS (per DU) ------------------
# DU (Declared Unit) = 1 m² of wall at 0.3 m thickness
A1_PER_DU = -43.95   # kg CO2e
A2_PER_DU = 8.42     # kg CO2e (fixed EU->US chain)
A5_PER_DU = 42.44    # kg CO2e
B1_PER_DU = -31.70   # kg CO2e
C_PER_DU  = 11.94    # kg CO2e  (C1–C4)

# A4 (to-site trucking) parameters
MASS_T_PER_DU = 0.0617   # tonnes per DU (61.67 kg)
EF_TRUCK_KG_PER_TKM = 0.08  # kg CO2e per tonne-km (EURO 6 lorry)

# ORIGIN: Port Newark–Elizabeth Marine Terminal (Port of NY/NJ)
PORT_LAT, PORT_LON = 40.6840, -74.1419

# Optional env var to use your own OSRM/ORS endpoint
OSRM_ENDPOINT = os.getenv("OSRM_ENDPOINT", "https://router.project-osrm.org")

# ------------------ HELPERS ------------------
nomi = pgeocode.Nominatim("us")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@st.cache_data(show_spinner=False)
def geocode_zip(zip_code: str):
    rec = nomi.query_postal_code(zip_code)
    if rec is None or pd.isna(rec.latitude) or pd.isna(rec.longitude):
        return None
    return float(rec.latitude), float(rec.longitude)

@st.cache_data(show_spinner=False)
def driving_distance_km(origin_lat, origin_lon, dest_lat, dest_lon):
    """Try OSRM driving distance; fallback to haversine * 1.2 (road factor)."""
    try:
        url = f"{OSRM_ENDPOINT}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=false"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            dist_m = data["routes"][0]["distance"]
            return dist_m / 1000.0
    except Exception:
        pass
    return haversine_km(origin_lat, origin_lon, dest_lat, dest_lon) * 1.2

def calc_A4_kg(DU: float, distance_km: float) -> float:
    tonne_km = (DU * MASS_T_PER_DU) * distance_km
    return tonne_km * EF_TRUCK_KG_PER_TKM

# ------------------ UI ------------------
st.markdown(
    """
    <div class="ameri-hero">
      <div class="pill">Hempcrete LCA</div>
      <h1>Estimate Net Carbon Storage</h1>
      <p class="small">Enter your project’s <strong>wall area</strong> and <strong>ZIP code</strong>. 
      We’ll compute life-cycle module impacts (A1, A2, A4, A5, B1, C1–C4) and total net carbon storage using your LCA assumptions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Inputs")
    wall_area_ft2 = st.number_input("Wall area (ft²)", min_value=1.0, value=1000.0, step=10.0)
    zip_code = st.text_input("Project ZIP code", value="10007", help="US ZIP only")
    st.caption("Origin: Port Newark–Elizabeth Marine Terminal (Port of NY/NJ)")
    submitted = st.button("Calculate")

if submitted or True:
    # Convert to DU (1 DU = 1 m²)
    DU = wall_area_ft2 * 0.092903

    dest = geocode_zip(zip_code)
    if dest is None:
        st.error("Invalid ZIP code. Please enter a valid US ZIP.")
        st.stop()
    dest_lat, dest_lon = dest
    distance_km = driving_distance_km(PORT_LAT, PORT_LON, dest_lat, dest_lon)

    # Modules
    A1 = DU * A1_PER_DU
    A2 = DU * A2_PER_DU
    A4 = calc_A4_kg(DU, distance_km)
    A5 = DU * A5_PER_DU
    B1 = DU * B1_PER_DU
    C  = DU * C_PER_DU

    total = A1 + A2 + A4 + A5 + B1 + C

    # Results
    st.subheader("Results")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Net Carbon Storage (kg CO₂e)", f"{total:,.1f}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Declared Units (DU)", f"{DU:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Truck Route Distance (km)", f"{distance_km:,.1f}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Breakdown chart
    chart_df = pd.DataFrame({
        "Module": ["A1 Raw materials", "A2 Upstream transport", "A4 Site transport",
                   "A5 Installation", "B1 Use phase", "C1–C4 End-of-life"],
        "kg CO₂e": [A1, A2, A4, A5, B1, C]
    })
    fig = px.bar(chart_df, x="Module", y="kg CO₂e", text_auto=True)
    fig.update_layout(yaxis_title="kg CO₂e", xaxis_title="Lifecycle Module",
                      bargap=0.25, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Calculation details & assumptions"):
        st.markdown(
            f"""
            - **DU (Declared Unit)**: 1 m² wall at 0.3 m thickness. DU = wall_area_ft² × 0.092903.
            - **A1** = DU × {A1_PER_DU} kg CO₂e
            - **A2** = DU × {A2_PER_DU} kg CO₂e (fixed chain EU→US)
            - **A4** = (DU × {MASS_T_PER_DU} t) × distance_km × {EF_TRUCK_KG_PER_TKM} kg CO₂e/(t·km)
            - **A5** = DU × {A5_PER_DU} kg CO₂e
            - **B1** = DU × {B1_PER_DU} kg CO₂e
            - **C1–C4** = DU × {C_PER_DU} kg CO₂e
            - **Origin**: Port Newark–Elizabeth (40.6840, −74.1419).
            - **Routing**: OSRM driving distance when available; fallback: haversine × 1.2.
            """
        )

    st.info("Negative totals indicate net carbon storage (biogenic uptake exceeds fossil/process emissions).")
