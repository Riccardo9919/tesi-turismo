import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cicerone 4.0", page_icon="🏛️", layout="wide")

# --- 2. INIZIALIZZAZIONE CLIENT ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata!")
    st.stop()

# --- 3. CARICAMENTO DOCUMENTI (Taglio a 8000 per sicurezza quota) ---
@st.cache_data
def carica_database():
    testo_completo = ""
    elenco_file = []
    LIMITE = 8000 
    
    documenti = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    for nome in documenti:
        try:
            with open(nome, "r", encoding="utf-8") as f:
                estratto = " ".join(f.read(LIMITE).split())
                testo_completo += f"\n\n--- FONTE: {nome} ---\n{estratto}\n"
                elenco_file.append(nome)
        except: pass
    return testo_completo, elenco_file

conoscenza, lista_file = carica_database()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📂 Fonti Analizzate")
    for f in lista_file: st.success(f"📌 {f}")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACCIA CHAT ---
st.title("🏛️ Cicerone 4.0")
st.subheader("Assistente Specializzato in Analisi del Turismo Italiano")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. LOGICA DI RISPOSTA ---
if prompt := st.chat_input("Chiedimi un'analisi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # STRATEGIA 2026: Proviamo i modelli stabili e quelli con i nuovi nomi
        # Invertiamo l'ordine: prima i modelli 2.0 che sono i più probabili
        modelli_da_provare = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b']
        successo = False

        for m_name in modelli_da_provare:
            try:
                istruzioni = (
                    "Agisci come un Assistente Turistico Specializzato. "
                    "Usa i dati forniti e cita sempre la fonte. "
                    "Sii professionale e analitico."
                )
                
                # Rimuoviamo eventuali prefissi 'models/' se presenti per evitare il 404
                model_id = m_name.replace("models/", "")
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=f"{istruzioni}\n\nDATABASE:\n{conoscenza}\n\nDOMANDA:\n{prompt}"
                )
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                successo = True
                break 

            except Exception as e:
                errore_str = str(e)
                # Se il modello non esiste (404), passa al prossimo nella lista
                if "404" in errore_str:
                    continue
                # Se è un problema di troppo traffico (429/503), avvisa l'utente
                elif "429" in errore_str or "503" in errore_str:
                    st.warning("⚠️ I server di Google sono carichi. Attendi 30 secondi.")
                    successo = True
                    break
                else:
                    st.error(f"Errore tecnico: {e}")
                    successo = True
                    break

        if not successo:
            st.error("Nessun modello compatibile trovato. Controlla la tua console Google Cloud.")
