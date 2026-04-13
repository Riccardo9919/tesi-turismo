import streamlit as st
import google.generativeai as genai
import os

# Configurazione della pagina
st.set_page_config(page_title="Tesi Turismo 2026", page_icon="🇮🇹", layout="wide")

# 1. CONFIGURAZIONE API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ API Key non trovata nei Secrets di Streamlit!")

# 2. CARICAMENTO DOCUMENTI
def carica_testi():
    testo = ""
    # Legge tutti i file .txt caricati nella cartella principale
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            try:
                with open(file, "r", encoding="utf-8") as f:
                    testo += f"\n--- FONTE: {file} ---\n" + f.read()
            except Exception as e:
                st.warning(f"Errore nel leggere {file}: {e}")
    return testo

contesto = carica_testi()

# 3. INTERFACCIA UTENTE
st.title("📊 Assistente AI per Tesi Economica")
st.caption("Analisi flussi turistici basata su dati ufficiali (ISTAT, CNR, PST)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra la cronologia dei messaggi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 4. LOGICA DEL BOT
if prompt := st.chat_input("Chiedimi un'analisi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Proviamo i nomi di modello più comuni per il 2026
        nomi_modelli = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']
        
        successo = False
        for nome in nomi_modelli:
            try:
                model = genai.GenerativeModel(nome)
                full_prompt = f"Usa questi dati per rispondere alla domanda: {contesto}\n\nDomanda: {prompt}"
                response = model.generate_content(full_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                successo = True
                break 
            except Exception:
                continue
        
        if not successo:
            st.error("⚠️ Il modello non risponde. Controlla che la tua API Key sia corretta.")
