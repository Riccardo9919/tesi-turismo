import streamlit as st
from google import genai
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cicerone 4.0", page_icon="🏛️", layout="wide")

# --- 2. INIZIALIZZAZIONE API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        # Usiamo il client ufficiale Google GenAI (versione 2026)
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Errore inizializzazione Client: {e}")
        st.stop()
else:
    st.error("🔑 API Key non trovata nei Secrets di Streamlit! Vai in Settings -> Secrets.")
    st.stop()

# --- 3. CARICAMENTO INTELLIGENTE (SLICING) ---
@st.cache_data
def carica_documenti():
    testo_per_ai = ""
    nomi_file_caricati = []
    
    # IMPORTANTE: Dato che i file sono da 200 pagine, leggiamo solo una parte.
    # 8.000 caratteri sono circa 5-6 pagine fitte di dati. 
    # È il limite ideale per non far scattare il blocco quota "429".
    LIMITE_PER_FILE = 8000 
    
    # Cerca tutti i file .txt nella cartella principale (escludendo requirements)
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f != "requirements.txt"]
    
    if not files:
        return None, []

    for nome_file in files:
        try:
            with open(nome_file, "r", encoding="utf-8") as f:
                # Leggiamo l'estratto iniziale
                estratto = f.read(LIMITE_PER_FILE)
                # "Compriamo" il testo togliendo spazi extra per risparmiare token
                estratto = " ".join(estratto.split())
                
                testo_per_ai += f"\n\n--- DOCUMENTO: {nome_file} ---\n{estratto}\n"
                nomi_file_caricati.append(nome_file)
        except Exception as e:
            st.sidebar.error(f"Errore nel file {nome_file}: {e}")
            
    return testo_per_ai, nomi_file_caricati

# Eseguiamo il caricamento
conoscenza, lista_doc = carica_documenti()

# --- 4. INTERFACCIA LATERALE (SIDEBAR) ---
with st.sidebar:
    st.title("📚 Database Tesi")
    if lista_doc:
        st.write(f"Documenti analizzati: {len(lista_doc)}")
        for d in lista_doc:
            st.success(f"✅ {d}")
        st.info("Nota: Per ogni file sono state caricate le prime pagine per permettere il confronto dei dati senza bloccare l'API.")
    else:
        st.warning("⚠️ Nessun file .txt trovato. Assicurati che i file siano su GitHub nella cartella principale.")
    
    if st.button("Pulisci Cronologia Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACCIA CHAT ---
st.title("🏛️ Cicerone 4.0")
st.caption("Analisi turistica avanzata con incrocio dati ISTAT, CNR e PST")

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
        # Strategia di Fallback: proviamo il modello più leggero (1.5) e poi il 2.0
        # Gemini 1.5 Flash è solitamente più tollerante per i limiti gratuiti.
        modelli_da_provare = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash']
        risposta_ottenuta = False

        for m_name in modelli_da_provare:
            try:
                istruzioni = (
                    "Sei un assistente esperto per una tesi magistrale in turismo. "
                    "Usa i dati degli estratti caricati per rispondere. "
                    "Cita sempre esplicitamente il nome del file da cui prendi le informazioni. "
                    "Se i dati non sono presenti nell'estratto, consiglia di consultare il file completo."
                )
                
                # Chiamata API
                response = client.models.generate_content(
                    model=m_name,
                    contents=f"{istruzioni}\n\nDATABASE:\n{conoscenza}\n\nDOMANDA:\n{prompt}"
                )
                
                testo_risposta = response.text
                st.markdown(testo_risposta)
                st.session_state.messages.append({"role": "assistant", "content": testo_risposta})
                risposta_ottenuta = True
                break # Se ha funzionato, interrompiamo i tentativi

            except Exception as e:
                # Gestione specifica degli errori di sovraccarico o quota
                errore_str = str(e)
                if "503" in errore_str or "504" in errore_str:
                    # Il server è occupato, il ciclo proverà il prossimo modello
                    continue
                elif "429" in errore_str:
                    st.warning("⚠️ Google sta elaborando troppe richieste contemporaneamente. Attendi 60 secondi e riprova.")
                    risposta_ottenuta = True # Evitiamo messaggi d'errore multipli
                    break
                else:
                    st.error(f"❌ Errore tecnico: {e}")
                    risposta_ottenuta = True
                    break

        if not risposta_ottenuta:
            st.error("⚠️ Tutti i server di Google sono occupati. Riprova tra un minuto.")
