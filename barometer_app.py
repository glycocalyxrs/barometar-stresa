import streamlit as st
import numpy as np
import pandas as pd
# import os # Nije neophodan za ovu verziju

# --- Funkcija za učitavanje PDF-a (keširana) ---
@st.cache_data # Kešira rezultat da se fajl ne čita stalno
def load_pdf_bytes(pdf_path):
    """Učitava PDF fajl i vraća njegov sadržaj kao bytes."""
    try:
        with open(pdf_path, "rb") as file:
            return file.read()
    except FileNotFoundError:
        # Ispisuje grešku unutar Streamlit aplikacije ako fajl nedostaje
        st.error(f"Greška: Fajl '{pdf_path}' nije pronađen. Proverite da li se nalazi u istom direktorijumu kao i Python skripta.")
        return None
    except Exception as e:
        st.error(f"Došlo je do greške prilikom čitanja fajla '{pdf_path}': {e}")
        return None

# --- Konfiguracija Stranice ---
st.set_page_config(
    page_title="Ćelijski Barometar Stresa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Naslov i Dugme za Preuzimanje PDF-a ---

# Definiši ime PDF fajla (pretpostavlja se da je u istom direktorijumu)
pdf_filename = "Inflamacija.pdf"
pdf_bytes_content = load_pdf_bytes(pdf_filename)

# Koristi kolone da postaviš naslov i dugme jedno pored drugog
col_title, col_button = st.columns([4, 1]) # Odnos širine kolona (npr. 4:1)

with col_title:
    st.title("🧬 Ćelijski Barometar Stresa")

with col_button:
    # Dodaj malo praznog prostora iznad dugmeta za bolje vertikalno poravnanje
    st.write("") # Prazan red može pomoći, ili koristi CSS za finije podešavanje
    if pdf_bytes_content:
        st.download_button(
            label="📄 Preuzmi PDF Model",    # Tekst na dugmetu
            data=pdf_bytes_content,         # Sadržaj fajla (bytes)
            file_name="Inflamacija_Celijski_Barometar_Stresa.pdf", # Predloženo ime fajla za korisnika
            mime="application/pdf",         # MIME tip za PDF
            key='pdf-download',             # Jedinstveni ključ za dugme
            help="Kliknite da preuzmete PDF dokument sa detaljnim objašnjenjem modela barometra stresa." # Tooltip
        )
    # Ako fajl nije pronađen, funkcija load_pdf_bytes će već ispisati grešku

# --- Uvodni Opis Aplikacije ---
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
    contributions = {
        "ROS": weights["ROS"] * ros**2,
        "ΔΨm": weights["dpsi"] * dpsi,
        "Membrane (PEO/EFA)": weights["peo"] * peo,
        "Cink (Zn)": weights["zn"] * zn,
        "cPLA2": weights["cpla2"] * cpla2,
        "sPLA2": weights["spla2"] * spla2
    }

    logit = sum(contributions.values())
    p = 1 / (1 + np.exp(-logit))
    p = np.clip(p, 0, 1)

    if not contributions:
        dominant_factor = "Nema podataka"
        dominant_value = 0
    else:
        dominant_factor = max(contributions, key=lambda k: abs(contributions[k]))
        dominant_value = contributions[dominant_factor]

    if dominant_value > 0.01:
        influence = " (Povećava Rizik)"
    elif dominant_value < -0.01:
        influence = " (Smanjuje Rizik)"
    else:
        influence = " (Minimalan Uticaj)"

    if p < 0.33:
        risk_level = "🟢 Nizak"
    elif p < 0.66:
        risk_level = "🟡 Umeren"
    else:
        risk_level = "🔴 Visok"

    return p, risk_level, dominant_factor + influence, contributions

# --- Izračunavanje i Prikaz Rezultata ---

# Poziv funkcije za izračunavanje
p_damage, risk_level_str, dominant_factor_str, contrib_dict = calculate_barometer_vitals(
    ros, dpsi, peo, zn, cpla2, spla2
)

st.subheader("📊 Rezultat Procene Barometra")

# Koristi kolone za raspored rezultata i vizualizacije doprinosa
col_result, col_contrib = st.columns([1, 2])

with col_result:
    st.metric(label="Verovatnoća Oštećenja P(d)", value=f"{p_damage*100:.1f}%")
    # Koristi Markdown za prikaz statusa sa bojom
    color_map = {"🟢": "green", "🟡": "orange", "🔴": "red"}
    status_emoji = risk_level_str.split(" ")[0]
    status_text = " ".join(risk_level_str.split(" ")[1:])
    st.markdown(f"**Status:** <span style='color:{color_map.get(status_emoji, 'black')}; font-size: 1.1em;'>{status_emoji} {status_text}</span>", unsafe_allow_html=True)
    st.markdown(f"**Ključni Faktor:** `{dominant_factor_str}`")

with col_contrib:
    st.markdown("**Vizuelni Prikaz Doprinosa Riziku:**")
    # Provera da li postoje doprinosi pre kreiranja DataFrame-a
    if contrib_dict:
        df_contrib = pd.DataFrame({
            'Faktor': contrib_dict.keys(),
            'Apsolutni Doprinos': [abs(v) for v in contrib_dict.values()],
            'Smer': ['Povećava Rizik' if v > 0 else 'Smanjuje Rizik' for v in contrib_dict.values()],
            'Stvarni Doprinos': [v for v in contrib_dict.values()] # Za ispis tačne vrednosti
        })
        df_contrib = df_contrib.sort_values(by='Apsolutni Doprinos', ascending=False)

        st.markdown("*(Prikaz relativnog uticaja svakog faktora na skor rizika)*")
        # Određivanje maksimalnog apsolutnog doprinosa za normalizaciju barova
        max_abs_contrib = df_contrib['Apsolutni Doprinos'].max() if not df_contrib.empty else 1

        # Prikaz barova pomoću Markdown
        for index, row in df_contrib.iterrows():
            # Izračunavanje dužine bara normalizovano
            if max_abs_contrib > 0:
                 bar_len = int((row['Apsolutni Doprinos'] / max_abs_contrib) * 20) # Skaliranje na max 20 blokova
            else:
                 bar_len = 0

            bar = "█" * bar_len # Korišćenje unicode bloka za bar
            color = "red" if row['Smer'] == 'Povećava Rizik' else "green"

            # Prikaz samo ako faktor ima značajan uticaj
            if abs(row['Stvarni Doprinos']) > 0.01:
                 st.markdown(f"`{row['Faktor']}`: <span style='color:{color}'>{bar}</span> ({row['Stvarni Doprinos']:.2f})", unsafe_allow_html=True)
    else:
        # Poruka ako nema podataka o doprinosima
        st.write("Nema dostupnih podataka o doprinosima.")

# --- Napomena / Disclaimer ---
st.markdown("---")
st.caption("🧠 **Napomena:** Ova procena je zasnovana na hipotetičkom modelu i težinskim faktorima. Služi isključivo u edukativne i istraživačke svrhe i ne predstavlja medicinski savet niti zamenu za kliničku dijagnozu. Težine i formula zahtevaju dalju validaciju.")