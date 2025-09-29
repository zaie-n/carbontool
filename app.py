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
        background-color: ##abcf3b;
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
st.title("Hempcrete Net Carbon Storage Calculator")

col1, col2 = st.columns([2,1])
with col1:
    wall_area = st.number_input("Wall area (ft²)", min_value=1, value=1000, step=100)
    zipcode = st.text_input("ZIP Code", value="12345")
with col2:
    st.write("This calculator estimates **net carbon storage** over the lifecycle of your hempcrete project. \
             Enter your wall area and project ZIP code to get started!")
st.subheader("Comparator Material (Supplier EPD)")

with st.expander("➕ Add comparator material"):
    epd_value = st.number_input(
        "Enter supplier EPD value (kg CO₂e per m³ of material)",
        min_value=0.0,
        step=1.0,
        value=250.0,
        help="Paste the GWP value from the supplier's EPD (usually A1–A3, per m³ of material)."
    )
    compare = st.checkbox("Compare hempcrete to this material")
    # ------------------ COMPARATOR ------------------
    if compare:
        # Normalize supplier EPD to 1 DU (0.3 m³ of wall)
        comp_per_DU = epd_value * 0.3
        comp_total = DU * comp_per_DU

        delta = comp_total - total

        st.markdown("### 🆚 Comparison with Supplier Material")
        st.markdown(f"""
        **Supplier material (EPD):**
        - Reported value: {epd_value:.1f} kg CO₂e / m³ (A1–A3)
        - Normalized to 1 DU (0.3 m³ wall): {comp_per_DU:.1f} kg CO₂e / m² wall
        - Total project emissions: {comp_total:.1f} kg CO₂e

        **Hempcrete (full A1–C4 LCA):**
        - Total project storage: {total:.1f} kg CO₂e

        **Net difference:**
        - Hempcrete saves {delta:.1f} kg CO₂e compared to this material
        """)

        # Visual comparison
        comp_df = pd.DataFrame({
            "Material": ["Hempcrete (A1–C4)", "Comparator (A1–A3)"],
            "kgCO2e": [total, comp_total]
        })
        fig2 = px.bar(
            comp_df, x="Material", y="kgCO2e",
            text="kgCO2e", color="Material",
            color_discrete_sequence=["#2E5041", "#B22222"]
        )
        fig2.update_layout(
            title="Hempcrete vs Supplier Material",
            yaxis_title="kg CO₂e (total project)",
            template="simple_white"
        )
        st.plotly_chart(fig2, use_container_width=True)

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
    if total < 0:
        card_html = f"""
        <div class="result-card" style="background-color:#e6f4ea;">
            <h3>Net Carbon Storage </h3>
            <div class="result-value">{abs(total):.1f} kg CO₂e stored</div>
        </div>
        """
    else:
        card_html = f"""
        <div class="result-card" style="background-color:#fdecea;">
            <h3>Net Carbon Emissions </h3>
            <div class="result-value">{total:.1f} kg CO₂e emitted</div>
        </div>
        """

    st.markdown(card_html, unsafe_allow_html=True)

    # ------------------ CHART ------------------
    df = pd.DataFrame({
        "Module": ["A1 Raw materials","A2 Upstream transport","A4 Site transport",
                   "A5 Installation","B1 Use phase","C1–C4 End-of-life"],
        "kgCO2e": [A1, A2, A4, A5, B1, C]
    })
    fig = px.bar(df, x="Module", y="kgCO2e",
                 text="kgCO2e", color="Module",
                 color_discrete_sequence=["#2E5041","#6B8F71","#C4B6A6","#88A093","#B6A19E","#F2E8CF"])
    fig.update_layout(title="Lifecycle Breakdown", yaxis_title="kg CO₂e",xaxis_title="Lifecycle Stage", template="simple_white",
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------ COLLAPSIBLE DETAILS ------------------
    with st.expander("Show calculation details"):
        st.write("**Formulas applied:**")
        st.code(f"""
DU = wall_area_ft² × 0.092903 convert to m2
A1 = DU × {A1_PER_DU}
A2 = DU × {A2_PER_DU}
A4 = (DU × {MASS_T_PER_DU} t) × distance_km × {EF_TRUCK}
A5 = DU × {A5_PER_DU}
B1 = DU × {B1_PER_DU}
C1–C4 = DU × {C_PER_DU}
        """)
        
        st.write("**Raw module results (kg CO₂e):**")
        st.dataframe(df.style.format({"kgCO2e": "{:.1f}"}))
