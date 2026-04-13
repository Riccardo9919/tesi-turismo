import streamlit as st
from google import genai
import os

# Configurazione Pagina
st.set_page_config(page_title="Cicerone 4.0", page_icon="🇮🇹", layout="wide")

# 1. SETUP NUOVO CLIENT (Standard 2026)
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione Google: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata nei Secrets!")
    st.stop()

# 2. CARICAMENTO DATI
@st.cache_data
def carica_conoscenza():
    testo = ""
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            with open(file, "r", encoding="utf-8") as f:
                testo += f"\n--- {file} ---\n" + f.read()
    return testo

conoscenza = carica_conoscenza()

# 3. INTERFACCIA
st.title("🏛️ Cicerone 4.0")
st.caption("Analisi turistica avanzata per tesi di laurea")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Chiedimi un'analisi sui flussi turistici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

   with st.chat_message("assistant"):
        try:
            # 1. CERCA IL MODELLO MIGLIORE DISPONIBILE (Così evitiamo il 404)
            modelli_disponibili = [m.name for m in client.models.list()]
            # Sceglie il primo modello 'flash' che trova (di solito il 2.0 o il 1.5 stabile)
            modello_scelto = next((m for m in modelli_disponibili if 'flash' in m), 'gemini-2.0-flash')
            
            # 2. CHIAMATA (Con limite di testo per evitare il 429)
            response = client.models.generate_content(
                model=modello_scelto,
                contents=f"Agisci come esperto tesi. Dati: {conoscenza[:10000]}\n\nDomanda: {prompt}"
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Google è un po' lento ad attivare la tua nuova chiave. Aspetta 5 minuti esatti senza scrivere nulla e poi riprova.")
            else:
                st.error(f"❌ Errore: {e}")
