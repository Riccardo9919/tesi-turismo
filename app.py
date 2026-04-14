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
    st.error("🔑 API Key non trovata nei Secrets!")
    st.stop()

# 3. CARICAMENTO DOCUMENTI
@st.cache_data
def carica_conoscenza():
    testo_completo = ""
    elenco_file = []
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            try:
                with open(file, "r", encoding="utf-8") as f:
                    contenuto = f.read()
                    testo_completo += f"\n\n--- DOCUMENTO: {file} ---\n{contenuto}\n"
                    elenco_file.append(file)
            except Exception as e:
                st.sidebar.error(f"Errore caricamento {file}: {e}")
    return testo_completo, elenco_file

conoscenza, lista_doc = carica_conoscenza()

# 4. SIDEBAR INFO
with st.sidebar:
    st.title("📚 Database")
    st.write("Documenti analizzati:")
    for doc in lista_doc:
        st.success(f"✅ {doc}")
    st.divider()
    st.info("Il bot incrocia i dati di tutti i file sopra elencati.")

# 5. INTERFACCIA CHAT
st.title("🏛️ Cicerone 4.0")
st.caption("Ciao! Chiedimi ciò che vuoi in ambito turistico e cercherò di aiutarti")

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
        # --- LOGICA DI FALLBACK (GESTIONE ERRORI 503) ---
        # Proviamo i due modelli principali: se uno è occupato, usa l'altro
        modelli_da_provare = ['gemini-2.0-flash', 'gemini-1.5-flash']
        risposta_completata = False

        for modello_nome in modelli_da_provare:
            try:
                istruzioni = (
                    f"Sei un assistente turistico esperto. "
                    f"Usa i dati di TUTTI i seguenti documenti: {conoscenza[:60000]}. "
                    f"Cita sempre il nome del file da cui prendi l'informazione."
                )
                
                response = client.models.generate_content(
                    model=modello_nome,
                    contents=f"{istruzioni}\n\nDomanda dell'utente: {prompt}"
                )
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                risposta_completata = True
                break # Successo! Esco dal ciclo dei modelli

            except Exception as e:
                # Se l'errore è 503 (Occupato), prova il prossimo modello
                if "503" in str(e) or "504" in str(e):
                    continue 
                # Se l'errore è Quota (429), avvisa l'utente
                elif "429" in str(e):
                    st.warning("⚠️ Troppe richieste in un minuto. Aspetta 30 secondi e riprova.")
                    risposta_completata = True # Fermo il ciclo
                    break
                else:
                    st.error(f"❌ Errore tecnico: {e}")
                    risposta_completata = True
                    break
        
        if not risposta_completata:
            st.warning("⚠️ Tutti i server di Google sono momentaneamente occupati. Riprova tra 60 secondi.")
