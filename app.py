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
            # Usiamo 2.0 flash che è il più moderno
            # Ma aggiungiamo un limite per non "intasare" la quota
            response = client.models.generate_content(
               model='gemini-1.5-flash-8b',
                contents=f"Usa questi dati per rispondere brevemente: {conoscenza[:15000]}\n\nDomanda: {prompt}"
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ Limite di messaggi raggiunto. Aspetta 60 secondi e riprova.")
            else:
                st.error(f"❌ Errore: {e}")
