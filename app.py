import streamlit as st
import google.generativeai as genai
import os

# Configurazione estetica
st.set_page_config(page_title="Assistente Turistico Italia", page_icon="🇮🇹")
st.title("🇮🇹 Analisi Turismo Italia - Tesi")
st.markdown("Interrogazione database ISTAT, CNR, ENIT e PST")

# Configurazione API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key mancante. Configurala nei Secrets di Streamlit.")

# Funzione per leggere i tuoi documenti .txt
def carica_conoscenza():
    testo_totale = ""
    folder = "documenti"
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith(".txt"):
                with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                    testo_totale += f"\n--- FONTE: {file} ---\n" + f.read()
    return testo_totale

conoscenza_bot = carica_conoscenza()

# Istruzioni per il comportamento del bot
PROMPT_SISTEMA = f"""
Tu sei un assistente turistico avanzato creato per una tesi di laurea in Economia.
Il tuo compito è analizzare il turismo in Italia basandoti su questi dati:
{conoscenza_bot}

REGOLE:
1. Cita sempre la fonte (es. 'Dati CNR indicano...').
2. Tono accademico e professionale.
3. Se l'informazione non è nei file, usa la tua conoscenza ma avvisa l'utente.
"""

# Interfaccia Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Chiedimi dei flussi turistici o di una meta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content([PROMPT_SISTEMA, prompt])
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
