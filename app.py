import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PROFESSIONALE ---
st.set_page_config(
    page_title="Cicerone 4.0 - Suite Professionale", 
    page_icon="🏛️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS per rifinire l'interfaccia e allineare i bottoni in basso
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    div[data-testid="stForm"] { border: none; padding: 0; }
    /* Stile per il tasto di reset accanto all'input */
    .reset-btn-container {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE API ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore critico di connessione: {e}")
        st.stop()
else:
    st.error("🔑 API Key mancante nei Secrets!")
    st.stop()

# --- 3. GESTIONE DATABASE (CACHE CONDIVISA) ---
@st.cache_data
def inizializza_database():
    testo_database = ""
    file_caricati = []
    
    # Con il piano Pay-as-you-go, carichiamo porzioni sostanziose (circa 35 pag/file)
    LIMITE_CARATTERI = 50000 
    
    documenti = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    
    for nome in documenti:
        try:
            with open(nome, "r", encoding="utf-8") as f:
                estratto = f.read(LIMITE_CARATTERI)
                estratto = " ".join(estratto.split())
                testo_database += f"\n\n--- FONTE UFFICIALE: {nome} ---\n{estratto}\n"
                file_caricati.append(nome)
        except:
            pass
            
    return testo_database, file_caricati

database_testuale, elenco_fonti = inizializza_database()

# --- 4. INTERFACCIA LATERALE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/museum.png", width=80)
    st.title("Cicerone Intelligence")
    st.subheader("Database Turistico")
    
    if elenco_fonti:
        for f in elenco_fonti:
            st.success(f"📂 {f}")
    else:
        st.error("Nessun file .txt rilevato.")
    
    st.divider()
    st.info("Sistema configurato per analisi multi-utente con priorità Pay-as-you-go.")

# --- 5. VISUALIZZAZIONE CHAT ---
st.title("🏛️ Cicerone 4.0")
st.markdown("### *Assistente specializzato nel turismo italiano*")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra lo storico dei messaggi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. AREA INPUT E RESET (AFFIANCATI) ---
# Creiamo due colonne: una grande per l'input e una piccola per il tasto reset
col_input, col_reset = st.columns([0.9, 0.1])

with col_reset:
    # Il tasto Reset è posizionato qui per essere cliccato velocemente
    if st.button("🗑️", help="Azzera la conversazione corrente"):
        st.session_state.messages = []
        st.rerun()

with col_input:
    if prompt := st.chat_input("Inserisci qui la tua richiesta di analisi..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            modelli = ['gemini-2.0-flash', 'gemini-1.5-flash']
            successo = False
            
            with st.spinner("Interrogazione database in corso..."):
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
                            st.warning("⚠️ Limite di velocità raggiunto. Attendi qualche secondo.")
                            successo = True
                            break
                        else:
                            st.error(f"Errore di sistema: {e}")
                            successo = True
                            break

                if not successo:
                    st.error("Servizio momentaneamente non disponibile.")
