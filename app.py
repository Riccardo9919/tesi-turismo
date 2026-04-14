import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cicerone 4.0", page_icon="🏛️", layout="wide")

# --- 2. INIZIALIZZAZIONE API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione Client: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata nei Secrets di Streamlit!")
    st.stop()

# --- 3. CARICAMENTO INTELLIGENTE DEI DOCUMENTI ---
@st.cache_data
def carica_documenti():
    testo_per_ai = ""
    nomi_file_caricati = []
    
    # Limite di caratteri per ogni file (circa 10-15 pagine l'uno)
    # Questo permette di incrociare i dati senza far scattare il blocco quota (429)
    LIMITE_PER_FILE = 2000 
    
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    
    if not files:
        return None, []

    for nome_file in files:
        try:
            with open(nome_file, "r", encoding="utf-8") as f:
                # Leggiamo solo la parte iniziale di ogni documento gigante
                estratto = f.read(LIMITE_PER_FILE)
                # Pulizia base per risparmiare spazio (token)
                estratto = " ".join(estratto.split())
                
                testo_per_ai += f"\n\n--- INIZIO DOCUMENTO: {nome_file} ---\n{estratto}\n"
                nomi_file_caricati.append(nome_file)
        except Exception as e:
            st.sidebar.error(f"Errore nel file {nome_file}: {e}")
            
    return testo_per_ai, nomi_file_caricati

# Carichiamo i dati all'avvio
conoscenza, lista_doc = carica_documenti()

# --- 4. INTERFACCIA LATERALE (SIDEBAR) ---
with st.sidebar:
    st.title("📚 Database")
    if lista_doc:
        st.write(f"Documenti trovati: {len(lista_doc)}")
        for d in lista_doc:
            st.success(f"✅ {d}")
        st.info("Nota: Di ogni file sono state caricate le prime 15 pagine per garantire l'incrocio dei dati.")
    else:
        st.warning("⚠️ Nessun file .txt trovato nella cartella principale.")

# --- 5. INTERFACCIA CHAT ---
st.title("🏛️ Cicerone 4.0")
st.caption("Ciao! Chiedimi pure ciò che vuoi in ambito turistico italiano")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra lo storico dei messaggi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input dell'utente
if prompt := st.chat_input("Chiedimi un'analisi comparativa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Strategia di Fallback: se il modello 2.0 è occupato, prova l'1.5
        modelli_da_provare = ['gemini-2.0-flash', 'gemini-1.5-flash']
        risposta_ottenuta = False

        for m_name in modelli_da_provare:
            try:
                istruzioni = (
                    "Sei un assistente esperto per una tesi magistrale in turismo. "
                    "Usa i dati degli estratti forniti qui sotto per rispondere. "
                    "Cita sempre esplicitamente il nome del file da cui prendi le informazioni. "
                    "Se i dati mancano nell'estratto, suggerisci all'utente di approfondire quel file specifico."
                )
                
                response = client.models.generate_content(
                    model=m_name,
                    contents=f"{istruzioni}\n\nDATABASE:\n{conoscenza}\n\nDOMANDA:\n{prompt}"
                )
                
                testo_risposta = response.text
                st.markdown(testo_risposta)
                st.session_state.messages.append({"role": "assistant", "content": testo_risposta})
                risposta_ottenuta = True
                break # Se ha funzionato, non prova l'altro modello

            except Exception as e:
                # Se è un errore di sovraccarico (503), continua il ciclo
                if "503" in str(e) or "504" in str(e):
                    continue
                # Se è un errore di quota (429), si ferma e avvisa
                elif "429" in str(e):
                    st.warning("⚠️ Google è momentaneamente saturo. Attendi 30-60 secondi e riprova questa domanda.")
                    risposta_ottenuta = True
                    break
                else:
                    st.error(f"❌ Errore tecnico: {e}")
                    risposta_ottenuta = True
                    break

        if not risposta_ottenuta:
            st.error("⚠️ I server di Google non rispondono. Riprova tra un istante.")
