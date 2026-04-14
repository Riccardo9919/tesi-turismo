import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PROFESSIONALE ---
st.set_page_config(
    page_title="Cicerone 4.0 - Professional Suite", 
    page_icon="🏛️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS per migliorare l'aspetto per più utenti
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stSpinner { text-align: center; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE API (OTTIMIZZATA) ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        # Client unico per la sessione
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore critico di connessione: {e}")
        st.stop()
else:
    st.error("🔑 API Key mancante nei Secrets!")
    st.stop()

# --- 3. GESTIONE DATABASE (CACHE CONDIVISA) ---
# st.cache_data permette a 10 persone di usare lo stesso database caricato in memoria
# senza dover rileggere i file da disco ogni volta, risparmiando tempo e RAM.
@st.cache_data
def inizializza_database():
    testo_database = ""
    file_caricati = []
    
    # Con il piano a pagamento, aumentiamo drasticamente la capacità.
    # 50.000 caratteri sono circa 30-35 pagine per ogni file.
    LIMITE_CARATTERI = 50000 
    
    documenti = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    
    for nome in documenti:
        try:
            with open(nome, "r", encoding="utf-8") as f:
                estratto = f.read(LIMITE_CARATTERI)
                # Pulizia per ottimizzare i costi del piano Pay-as-you-go
                estratto = " ".join(estratto.split())
                testo_database += f"\n\n--- FONTE UFFICIALE: {nome} ---\n{estratto}\n"
                file_caricati.append(nome)
        except:
            pass
            
    return testo_database, file_caricati

database_testuale, elenco_fonti = inizializza_database()

# --- 4. INTERFACCIA UTENTE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/museum.png", width=80)
    st.title("Cicerone Intelligence")
    st.subheader("Database Turistico Attivo")
    
    if elenco_fonti:
        for f in elenco_fonti:
            st.success(f"📂 {f}")
    else:
        st.error("Nessun file .txt rilevato.")
    
    st.divider()
    st.info("Questa console è configurata per analisi professionali multi-utente.")
    if st.button("Pulisci mia sessione"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGICA CHAT ---
st.title("🏛️ Cicerone 4.0")
st.markdown("### *Consulente Specializzato in Analisi e Strategia del Turismo*")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Visualizzazione messaggi isolata per ogni utente
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. ELABORAZIONE RICHIESTE (SISTEMA MULTI-MODELLO) ---
if prompt := st.chat_input("Inserisci qui la tua richiesta di analisi professionale..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Con il piano a pagamento, usiamo il modello più potente come primario
        modelli = ['gemini-2.0-flash', 'gemini-1.5-flash']
        successo = False
        
        # St.spinner è fondamentale per l'uso multi-utente (fa capire che il bot sta pensando)
        with st.spinner("Analisi dei flussi in corso..."):
            for m_name in modelli:
                try:
                    prompt_sistema = (
                        "Sei un Assistente Turistico Specializzato di alto livello. "
                        "Analizza i dati provenienti dai documenti ufficiali forniti (ISTAT, CNR, PST). "
                        "Il tuo tono è professionale, tecnico e orientato alla consulenza strategica. "
                        "Regola aurea: Cita sempre la fonte specifica (es. 'Il documento CNR indica...') "
                        "e confronta i dati tra i diversi file per evidenziare trend o discrepanze. "
                        "Fornisci risposte strutturate, se utile usa elenchi puntati."
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
                    # In caso di errore temporaneo dei server Google, prova il modello di backup
                    if "503" in str(e) or "504" in str(e):
                        continue
                    elif "429" in str(e):
                        st.warning("⚠️ Traffico intenso. I server di Google stanno smistando le richieste. Riprova tra 10 secondi.")
                        successo = True
                        break
                    else:
                        st.error(f"Errore di sistema: {e}")
                        successo = True
                        break

            if not successo:
                st.error("Servizio momentaneamente non disponibile a causa dell'alto traffico globale di Google.")
