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

# 3. FUNZIONE CARICAMENTO (Slicing per file da 200 pagine)
@st.cache_data
def carica_conoscenza():
    testo_completo = ""
    elenco_nomi_file = []
    # Prendiamo i primi 35.000 caratteri di ogni file (circa 20-25 pagine l'uno)
    # Questo ci permette di incrociare i dati senza far esplodere la quota di Google
    limite_caratteri_per_file = 35000 
    
    for file in os.listdir("."):
        if file.endswith(".txt") and file != "requirements.txt":
            try:
                with open(file, "r", encoding="utf-8") as f:
                    contenuto = f.read(limite_caratteri_per_file) 
                    testo_completo += f"\n\n--- DOCUMENTO: {file} ---\n{contenuto}\n"
                    elenco_nomi_file.append(file)
            except Exception as e:
                st.sidebar.error(f"Errore caricamento {file}: {e}")
                
    return testo_completo, elenco_nomi_file

# ESEGUIAMO IL CARICAMENTO
conoscenza, lista_doc = carica_conoscenza()

# 4. SIDEBAR
with st.sidebar:
    st.title("📚 Database Tesi")
    st.write("Documenti analizzati (Prime 25 pagine cad.):")
    if not lista_doc:
        st.warning("⚠️ Nessun file .txt trovato!")
    else:
        for doc in lista_doc:
            st.success(f"✅ {doc}")
    st.divider()
    st.info("Nota: Data la dimensione dei file (200 pag), il bot analizza le sezioni iniziali di ogni documento.")

# 5. INTERFACCIA CHAT
st.title("🏛️ Cicerone 4.0")
st.caption("Analisi integrata per documenti di grandi dimensioni")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Chiedimi un'analisi comparativa tra i file..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Scegliamo il modello più adatto
            modelli_da_provare = ['gemini-2.0-flash', 'gemini-1.5-flash']
            successo = False
            
            for m_name in modelli_da_provare:
                try:
                    istruzioni = (
                        "Sei un assistente esperto. Usa i dati degli estratti caricati per rispondere. "
                        "Se un dato non è nelle prime 25 pagine, dillo chiaramente. Cita i file usati."
                    )
                    
                    response = client.models.generate_content(
                        model=m_name,
                        contents=f"{istruzioni}\n\nDATABASE:\n{conoscenza}\n\nDOMANDA:\n{prompt}"
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    successo = True
                    break
                except Exception as e:
                    if "503" in str(e) or "504" in str(e):
                        continue # Prova l'altro modello se il server è occupato
                    else:
                        raise e

            if not successo:
                st.error("⚠️ I server di Google sono troppo carichi. Riprova tra un minuto.")
                
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Limite quota raggiunto. Aspetta 60 secondi.")
            else:
                st.error(f"❌ Errore tecnico: {e}")
