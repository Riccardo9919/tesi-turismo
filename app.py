import streamlit as st
from google import genai
import os

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Cicerone 4.0", page_icon="🇮🇹", layout="wide")

# 2. INIZIALIZZAZIONE CLIENT GOOGLE
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata nei Secrets!")
    st.stop()

# 3. CARICAMENTO DOCUMENTI
@st.cache_data
def carica_conoscenza():
    testo = ""
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            with open(file, "r", encoding="utf-8") as f:
                testo += f"\n--- {file} ---\n" + f.read()
    return testo

conoscenza = carica_conoscenza()

# 4. INTERFACCIA UTENTE
st.title("🏛️ Cicerone 4.0")
st.caption("Analisi turistica avanzata per tesi di laurea")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5. LOGICA DELLA CHAT
if prompt := st.chat_input("Chiedimi un'analisi sui flussi turistici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Trova automaticamente il miglior modello disponibile per evitare il 404
            modelli = [m.name for m in client.models.list()]
            modello_scelto = next((m for m in modelli if 'flash' in m), 'gemini-2.0-flash')
            
            # Chiamata al modello con limite di caratteri per evitare il 429
            response = client.models.generate_content(
                model=modello_scelto,
                contents=f"Usa questi dati per rispondere: {conoscenza[:12000]}\n\nDomanda: {prompt}"
            )
            
            risposta = response.text
            st.markdown(risposta)
            st.session_state.messages.append({"role": "assistant", "content": risposta})
            
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Limite raggiunto. Attendi un istante e riprova.")
            else:
                st.error(f"❌ Errore: {e}")
