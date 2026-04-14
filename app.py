import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cicerone 4.0 - Consulente Turistico", page_icon="🏛️", layout="wide")

# --- 2. INIZIALIZZAZIONE API ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore tecnico nell'inizializzazione: {e}")
        st.stop()
else:
    st.error("🔑 API Key mancante! Inseriscila nei Secrets di Streamlit.")
    st.stop()

# --- 3. CARICAMENTO DATI (Ottimizzato per 200 pagine) ---
@st.cache_data
def carica_database_turistico():
    conoscenza_totale = ""
    file_rilevati = []
    
    # Dato che i file sono enormi, leggiamo le sezioni principali di ognuno.
    # 10.000 caratteri permettono di leggere circa 6-8 pagine dense di dati.
    # Questo garantisce che l'IA possa incrociare tutti i file senza bloccare la quota.
    CARATTERI_PER_FILE = 10000 
    
    documenti = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    
    if not documenti:
        return None, []

    for nome in documenti:
        try:
            with open(nome, "r", encoding="utf-8") as f:
                estratto = f.read(CARATTERI_PER_FILE)
                # Compressione del testo per risparmiare spazio (token)
                estratto = " ".join(estratto.split())
                
                conoscenza_totale += f"\n\n--- FONTE: {nome} ---\n{estratto}\n"
                file_rilevati.append(nome)
        except Exception:
            pass
            
    return conoscenza_totale, file_rilevati

conoscenza, lista_file = carica_database_turistico()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📂 Fonti Analizzate")
    if lista_file:
        st.write(f"Database composto da {len(lista_file)} documenti:")
        for f in lista_file:
            st.success(f"📌 {f}")
        st.info("Configurazione: Analisi multicontesto attiva.")
    else:
        st.warning("Nessun database (.txt) trovato.")
    
    if st.button("Reset Conversazione"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACCIA PRINCIPALE ---
st.title("🏛️ Cicerone 4.0")
st.subheader("Assistente Specializzato in Analisi del Turismo Italiano")
st.caption("Ciao! Chiedimi pure ciò che vuoi")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. LOGICA DI RISPOSTA ---
if prompt := st.chat_input("Inserisci qui la tua richiesta di analisi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Modelli da provare in ordine di stabilità per il piano gratuito
        modelli = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash']
        successo = False

        for m_name in modelli:
            try:
                # PERSONA: Assistente Turistico Specializzato
                prompt_sistema = (
                    "Agisci come un Assistente Turistico Specializzato esperto in analisi dei dati e strategie di settore. "
                    "Il tuo compito è analizzare i flussi e le tendenze basandoti esclusivamente sui documenti forniti. "
                    "Fornisci risposte professionali, precise e orientate al business o alla consulenza. "
                    "Cita sempre le fonti (es. 'In base ai dati ISTAT...') e se i dati sono presenti in più file, confrontali. "
                    "Se l'informazione non è presente negli estratti, offri una stima basata sul contesto o suggerisci un approfondimento."
                )
                
                response = client.models.generate_content(
                    model=m_name,
                    contents=f"{prompt_sistema}\n\nDATABASE DOCUMENTALE:\n{conoscenza}\n\nRICHIESTA UTENTE:\n{prompt}"
                )
                
                risposta = response.text
                st.markdown(risposta)
                st.session_state.messages.append({"role": "assistant", "content": risposta})
                successo = True
                break 

            except Exception as e:
                msg_errore = str(e)
                if "503" in msg_errore or "504" in msg_errore:
                    continue # Prova il prossimo modello se il server è sovraccarico
                elif "429" in msg_errore:
                    st.warning("⚠️ Troppe richieste. Per favore, attendi un momento prima della prossima domanda.")
                    successo = True
                    break
                else:
                    st.error(f"Errore tecnico: {e}")
                    successo = True
                    break

        if not successo:
            st.error("I server di analisi sono momentaneamente occupati. Riprova tra 60 secondi.")
