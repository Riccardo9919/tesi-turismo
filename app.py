import streamlit as st
from google import genai
import os

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Cicerone 4.0", page_icon="🏛️", layout="wide")

# 2. INIZIALIZZAZIONE CLIENT
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata!")
    st.stop()

# 3. CARICAMENTO DOCUMENTI (Con indicatore di quali file legge)
@st.cache_data
def carica_conoscenza():
    testo_completo = ""
    elenco_file = []
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            try:
                with open(file, "r", encoding="utf-8") as f:
                    contenuto = f.read()
                    # Aggiungiamo dei marcatori chiari per separare i file
                    testo_completo += f"\n\n--- DOCUMENTO: {file} ---\n{contenuto}\n"
                    elenco_file.append(file)
            except Exception as e:
                st.sidebar.error(f"Errore caricamento {file}: {e}")
    return testo_completo, elenco_file

conoscenza, lista_doc = carica_conoscenza()

# 4. SIDEBAR INFO
with st.sidebar:
    st.title("📚 Database Tesi")
    st.write("Documenti analizzati:")
    for doc in lista_doc:
        st.success(f"✅ {doc}")
    st.divider()
    st.info("Il bot incrocia i dati di tutti i file sopra elencati.")

# 5. INTERFACCIA CHAT
st.title("🏛️ Cicerone 4.0")
st.caption("Analisi integrata di ISTAT, CNR, PST e fonti caricat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Chiedimi un'analisi comparativa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 1. Cerchiamo il modello (Flash è ideale per molti documenti)
            modelli = [m.name for m in client.models.list()]
            modello_scelto = next((m for m in modelli if 'flash' in m), 'gemini-2.0-flash')
            
            # 2. ISTRUZIONI: Chiediamo esplicitamente di usare TUTTE le fonti
            istruzioni = (
                f"Sei un assistente per una tesi magistrale. "
                f"Usa i dati di TUTTI i seguenti documenti: {conoscenza[:100000]}. " # Limite alzato a 100k caratteri
                f"Se le informazioni sono presenti in più file, confrontale. "
                f"Cita sempre il nome del file da cui prendi l'informazione."
            )
            
            response = client.models.generate_content(
                model=modello_scelto,
                contents=f"{istruzioni}\n\nDomanda dell'utente: {prompt}"
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Troppe richieste. Aspetta 30 secondi.")
            else:
                st.error(f"❌ Errore: {e}")
