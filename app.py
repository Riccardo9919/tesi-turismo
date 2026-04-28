import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PROFESSIONALE ---
st.set_page_config(
    page_title="Cicerone 4.0", 
    page_icon="🏛️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PERSONALIZZATO (Barra fissa e Reset) ---
st.markdown("""
    <style>
    /* Forza la barra di input a rimanere in fondo */
    .stChatInputContainer {
        position: fixed;
        bottom: 30px;
        z-index: 1000;
    }
    
    /* Crea un'area per il tasto reset galleggiante in basso a destra */
    .floating-reset {
        position: fixed;
        bottom: 95px;
        right: 50px;
        z-index: 1001;
    }

    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    
    /* Nasconde il footer di default per pulizia */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONNESSIONE API ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore critico di connessione: {e}")
        st.stop()
else:
    st.error("🔑 API Key mancante nei Secrets!")
    st.stop()

# --- 4. GESTIONE DATABASE (CACHE CONDIVISA) ---
@st.cache_data
def inizializza_database():
    testo_database = ""
    file_caricati = []
    LIMITE_CARATTERI = 50000 
    
    documenti = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    for nome in documenti:
        try:
            with open(nome, "r", encoding="utf-8") as f:
                estratto = f.read(LIMITE_CARATTERI)
                estratto = " ".join(estratto.split())
                testo_database += f"\n\n--- FONTE UFFICIALE: {nome} ---\n{estratto}\n"
                file_caricati.append(nome)
        except: pass
    return testo_database, file_caricati

database_testuale, elenco_fonti = inizializza_database()

# --- 5. INTERFACCIA LATERALE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/museum.png", width=80)
    st.title("Cicerone Intelligence")
    st.subheader("Database Turistico")
    if elenco_fonti:
        for f in elenco_fonti: st.success(f"📂 {f}")
    else:
        st.error("Nessun file .txt rilevato.")
    st.divider()
    st.info("Sistema configurato per analisi multi-utente.")

# --- 6. VISUALIZZAZIONE CHAT ---
st.title("🏛️ Cicerone 4.0")
st.markdown("### *Assistente specializzato nel turismo italiano*")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Container per i messaggi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. AREA INPUT E RESET ---

# Tasto reset "galleggiante" sopra la barra di input
with st.container():
    col1, col2 = st.columns([0.9, 0.1])
    with col2:
        if st.button("🗑️", help="Azzera la sessione"):
            st.session_state.messages = []
            st.rerun()

# Barra di input (fuori dalle colonne per rimanere sticky in basso)
if prompt := st.chat_input("Inserisci qui la tua richiesta di analisi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        modelli = ['gemini-2.0-flash', 'gemini-1.5-flash']
        successo = False
        
        with st.spinner("Analisi in corso..."):
            for m_name in modelli:
                try:
                    prompt_sistema = (
                        "Sei un Assistente Turistico Specializzato nel turismo italiano. "
                        "Analizza i dati provenienti dai documenti ufficiali forniti (ISTAT, CNR, PST). "
                        "Il tuo tono è professionale, autorevole ma accessibile. "
                        "Regola aurea: Cita sempre la fonte specifica (es. 'Secondo il report ISTAT...') "
                        "e confronta i dati tra i diversi file per evidenziare trend, obiettivi o discrepanze. "
                        "Non inventare dati non presenti nei file."
                    )
                    
                    response = client.models.generate_content(
                        model=m_name,
                        contents=f"{prompt_sistema}\n\nDATABASE DOCUMENTALE:\n{database_testuale}\n\nRICHIESTA:\n{prompt}"
                    )
                    
                    risposta_finale = response.text
                    st.markdown(risposta_finale)
                    st.session_state.messages.append({"role": "assistant", "content": risposta_finale})
                    successo = True
                    break 

                except Exception as e:
                    if "503" in str(e) or "504" in str(e):
                        continue
                    elif "429" in str(e):
                        st.warning("⚠️ Limite raggiunto. Attendi qualche secondo.")
                        successo = True
                        break
                    else:
                        st.error(f"Errore di sistema: {e}")
                        successo = True
                        break
            if not successo:
                st.error("Servizio momentaneamente non disponibile.")
