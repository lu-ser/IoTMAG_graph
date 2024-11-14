import os
import sys
from pyngrok import ngrok
import uvicorn
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.entity_extraction_agent import EntityExtractionAgent
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime, timezone
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.ngrok.io",
        "https://*.ngrok-free.app",  # Aggiungi questo
        "*",  # Temporaneamente per debug
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modello Pydantic per il messaggio
class Message(BaseModel):
    text: str
    timestamp: Optional[str] = None


# Inizializza l'agente
agent = EntityExtractionAgent()


@app.post("/process-message")
async def process_message(message: Message) -> Dict:
    try:
        # Convert ISO string to UTC datetime if provided
        if message.timestamp:
            try:
                timestamp = datetime.fromisoformat(message.timestamp)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid timestamp format: {str(e)}"
                )
        else:
            timestamp = None

        agent.process_message(message=message.text, timestamp=timestamp)
        return {"success": True}
    except Exception as e:
        logging.error(f"Error in process_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph")
async def get_graph(time_filter: str = "now"):
    try:
        if time_filter not in ["now", "1h", "1d", "1w", "1m"]:
            raise HTTPException(status_code=400, detail="Invalid time filter")
        return agent.get_graph_data(time_filter)
    except Exception as e:
        logging.error(f"Error in get_graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_graph():
    """Reset the knowledge graph, removing all entities and relations."""
    try:
        logging.info("Resetting knowledge graph")
        agent.reset()
        return {"success": True, "message": "Graph reset successfully"}
    except Exception as e:
        logging.error(f"Error resetting graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def start_ngrok():
    """Avvia e configura ngrok per backend e frontend"""
    try:
        # Ottieni il token da .env
        ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
        if not ngrok_token:
            logger.error("NGROK_AUTH_TOKEN non trovato nel file .env")
            raise ValueError("NGROK_AUTH_TOKEN mancante")

        # Configura il token ngrok
        ngrok.set_auth_token(ngrok_token)

        # Chiudi eventuali tunnel esistenti
        ngrok.kill()

        # Apri il tunnel per il backend (FastAPI - porta 8000)
        backend_tunnel = ngrok.connect(8000, "http", name="fastapi_tunnel")
        logger.info(f"Backend tunnel established at: {backend_tunnel.public_url}")

        # Apri il tunnel per il frontend (Vite - porta 5173)
        frontend_tunnel = ngrok.connect(5173, "http", name="vite_tunnel")
        logger.info(f"Frontend tunnel established at: {frontend_tunnel.public_url}")

        # Aggiorna il file .env del frontend usando os.path per gestire i path Windows
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        frontend_env_path = os.path.join(root_dir, "frontend", ".env")

        # Crea la directory frontend se non esiste
        frontend_dir = os.path.dirname(frontend_env_path)
        if not os.path.exists(frontend_dir):
            os.makedirs(frontend_dir)

        with open(frontend_env_path, "w") as f:
            f.write(f"VITE_API_URL={backend_tunnel.public_url}\n")

        return backend_tunnel.public_url, frontend_tunnel.public_url

    except Exception as e:
        logger.error(f"Error setting up ngrok: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Avvia ngrok
        backend_url, frontend_url = start_ngrok()

        print("\n=== NGROK URLs ===")
        print(f"Backend (FastAPI): {backend_url}")
        print(f"Frontend (Vite): {frontend_url}")
        print(f"\nIl file .env del frontend è stato aggiornato con l'URL del backend")
        print("==================\n")

        # Avvia il server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Errore durante l'avvio del server: {str(e)}")
        ngrok.kill()
        sys.exit(1)
