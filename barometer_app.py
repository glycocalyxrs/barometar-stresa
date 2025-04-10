import streamlit as st
import numpy as np
import pandas as pd # Dodato za lakše pravljenje grafikona

# --- Konfiguracija Stranice ---
st.set_page_config(
    page_title="Ćelijski Barometar Stresa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Naslov i Uvodni Opis ---
st.title("🧬 Ćelijski Barometar Stresa")
st.markdown("""
Ovaj alat procenjuje verovatnoću ćelijskog oštećenja **P(oštećenje)** na osnovu
integrativnog modela koji uključuje ključne unutarćelijske parametre.
Podesite vrednosti u bočnoj traci da vidite kako utiču na ćelijski stres.
""")
st.markdown("---")

# --- Sidebar za Unos Parametara ---
st.sidebar.title("🔧 Podesite Parametre")
st.sidebar.markdown("**Osnovni Parametri Modela:**")

# Slajderi za ćelijske bio-parametre sa objašnjenjima
ros = st.sidebar.slider("🔼 ROS Nivo", 0.0, 1.0, 0.5, help="Nivo reaktivnih kiseoničnih vrsta (0=nizak, 1=visok)")
dpsi = st.sidebar.slider("⚡ Mitohondrijalni Potencijal (ΔΨm)", 0.0, 1.0, 0.5, help="Potencijal membrane mitohondrija (0=loš/nizak, 1=optimalan/visok)")
peo = st.sidebar.slider("🛡️ Kvalitet Membrana (PEO/EFA)", 0.0, 1.0, 0.5, help="Integritet i sastav ćelijskih membrana (0=loš, 1=dobar)")
zn = st.sidebar.slider("🥉 Cink (Zn++) Status", 0.0, 1.0, 0.5, help="Status cinka kao kofaktora (0=nizak/loš, 1=optimalan)")
cpla2 = st.sidebar.slider("🔥 cPLA2 Aktivnost", 0.0, 1.0, 0.5, help="Aktivnost citosolne fosfolipaze A2 (0=niska, 1=visoka)")
spla2 = st.sidebar.slider("💧 sPLA2 Aktivnost", 0.0, 1.0, 0.5, help="Aktivnost sekretorne fosfolipaze A2 (0=niska, 1=visoka)")

# --- Opcioni Klinički Kontekst (ne ulazi direktno u kalkulaciju) ---
st.sidebar.markdown("---")
st.sidebar.markdown("**🧪 Klinički Kontekst (Opciono):**")
st.sidebar.caption("Ovi parametri trenutno služe samo za kontekst.")
show_clinical = st.sidebar.checkbox("Prikaži kliničke slajdere", value=False)

if show_clinical:
    hba1c = st.sidebar.slider("HbA1c (%)", 4.0, 12.0, 5.5)
    crp = st.sidebar.slider("CRP (mg/L)", 0.0, 100.0, 5.0)
    feritin = st.sidebar.slider("Feritin (ng/mL)", 10.0, 1000.0, 150.0)
    vitd = st.sidebar.slider("Vitamin D (ng/mL)", 5.0, 100.0, 40.0)
    egfr = st.sidebar.slider("eGFR (ml/min)", 15.0, 120.0, 90.0)
    alt = st.sidebar.slider("ALT (U/L)", 5.0, 200.0, 25.0)
    # Dodaj još po potrebi...

# --- Funkcija za Kalkulaciju Barometra ---
def calculate_barometer_vitals(ros, dpsi, peo, zn, cpla2, spla2):
    """
    Izračunava P(oštećenje) i identifikuje ključne doprinose.
    """
    # Definicija težina (mogu se kalibrisati)
    weights = {
        "ROS": 3.0,
        "dpsi": -2.5, # Negativno jer visok dpsi smanjuje rizik
        "peo": -1.5, # Negativno jer dobar PEO smanjuje rizik
        "zn": -2.0, # Negativno jer dobar Zn smanjuje rizik
        "cpla2": 2.0,
        "spla2": 1.5
    }

    # Izračunavanje ponderisanih doprinosa
    # Napomena: Zaštitni faktori (dpsi, peo, zn) ulaze sa svojom vrednošću,
    # ali imaju negativne težine. ROS ulazi kvadrirano.
    contributions = {
        "ROS": weights["ROS"] * ros**2,
        "ΔΨm": weights["dpsi"] * dpsi, # npr. ako dpsi=1, doprinos = -2.5
        "Membrane (PEO/EFA)": weights["peo"] * peo, # npr. ako peo=1, doprinos = -1.5
        "Cink (Zn)": weights["zn"] * zn, # npr. ako zn=1, doprinos = -2.0
        "cPLA2": weights["cpla2"] * cpla2,
        "sPLA2": weights["spla2"] * spla2
    }

    # Ukupni logit skor (suma ponderisanih doprinosa)
    # Ispravka: treba sabrati vrednosti iz rečnika contributions
    logit = sum(contributions.values())

    # Verovatnoća P(oštećenje) pomoću logističke funkcije
    # Ispravka: treba koristiti logit, a ne x
    p = 1 / (1 + np.exp(-logit)) # Korišćenje standardnog minusa ovde
    p = np.clip(p, 0, 1) # Osigurava da je uvek između 0 i 1

    # Određivanje dominantnog faktora
    if not contributions: # Ako je rečnik prazan
        dominant_factor = "Nema podataka"
        dominant_value = 0
    else:
        # Pronalazi ključ sa najvećom apsolutnom vrednošću doprinosa
        dominant_factor = max(contributions, key=lambda k: abs(contributions[k]))
        dominant_value = contributions[dominant_factor]

    # Određivanje uticaja dominantnog faktora
    if dominant_value > 0.01: # Mala tolerancija za skoro nulte vrednosti
        influence = " (Povećava Rizik)"
    elif dominant_value < -0.01: # Korišćenje standardnog minusa
        influence = " (Smanjuje Rizik)"
    else:
        influence = " (Minimalan Uticaj)"

    # Kvalitativna ocena rizika
    if p < 0.33:
        risk_level = "🟢 Nizak"
    elif p < 0.66:
        risk_level = "🟡 Umeren"
    else:
        risk_level = "🔴 Visok"

    return p, risk_level, dominant_factor + influence, contributions

# --- Izračunavanje i Prikaz Rezultata ---

# Poziv funkcije
p_damage, risk_level_str, dominant_factor_str, contrib_dict = calculate_barometer_vitals(
    ros, dpsi, peo, zn, cpla2, spla2
)

st.subheader("📊 Rezultat Procene Barometra")

col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="Verovatnoća Oštećenja P(d)", value=f"{p_damage*100:.1f}%")
    # Koristi Markdown za prikaz sa bojom
    color_map = {"🟢": "green", "🟡": "orange", "🔴": "red"}
    status_emoji = risk_level_str.split(" ")[0]
    status_text = " ".join(risk_level_str.split(" ")[1:])
    st.markdown(f"**Status:** <span style='color:{color_map.get(status_emoji, 'black')}; font-size: 1.1em;'>{status_emoji} {status_text}</span>", unsafe_allow_html=True)
    st.markdown(f"**Ključni Faktor:** `{dominant_factor_str}`")


with col2:
    st.markdown("**Vizuelni Prikaz Doprinosa Riziku:**")
    # Pripremi podatke za grafikon - koristimo apsolutne vrednosti za visinu bara
    # a boja može ukazivati na smer (npr. crveno za povećanje, zeleno za smanjenje)
    # Ispravka: Proveriti da li je contrib_dict popunjen pre kreiranja DataFrame-a
    if contrib_dict:
        df_contrib = pd.DataFrame({
            'Faktor': contrib_dict.keys(),
            'Apsolutni Doprinos': [abs(v) for v in contrib_dict.values()],
            'Smer': ['Povećava Rizik' if v > 0 else 'Smanjuje Rizik' for v in contrib_dict.values()],
            'Stvarni Doprinos': [v for v in contrib_dict.values()] # Dodato za prikaz tačne vrednosti
        })
        df_contrib = df_contrib.sort_values(by='Apsolutni Doprinos', ascending=False)

        # Stilizovaniji prikaz pomoću Markdown
        st.markdown("*(Prikaz relativnog uticaja svakog faktora na skor rizika)*")
        max_abs_contrib = df_contrib['Apsolutni Doprinos'].max() if not df_contrib.empty else 1 # Za normalizaciju bara

        for index, row in df_contrib.iterrows():
            # Jednostavna vizuelna skala (npr. koristeći unicode blokove)
            # Normalizacija dužine bara prema maksimalnom apsolutnom doprinosu
            if max_abs_contrib > 0:
                 bar_len = int((row['Apsolutni Doprinos'] / max_abs_contrib) * 20) # Skaliranje na max 20 blokova
            else:
                 bar_len = 0

            bar = "█" * bar_len
            color = "red" if row['Smer'] == 'Povećava Rizik' else "green"
            # Prikazi samo ako ima značajnog uticaja
            if abs(row['Stvarni Doprinos']) > 0.01:
                 st.markdown(f"`{row['Faktor']}`: <span style='color:{color}'>{bar}</span> ({row['Stvarni Doprinos']:.2f})", unsafe_allow_html=True)
    else:
        st.write("Nema dostupnih podataka o doprinosima.")


# --- Napomena / Disclaimer ---
st.markdown("---")
st.caption("🧠 **Napomena:** Ova procena je zasnovana na hipotetičkom modelu i težinskim faktorima. Služi isključivo u edukativne i istraživačke svrhe i ne predstavlja medicinski savet niti zamenu za kliničku dijagnozu. Težine i formula zahtevaju dalju validaciju.")