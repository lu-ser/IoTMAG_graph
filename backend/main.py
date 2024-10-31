import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.entity_extraction_agent import EntityExtractionAgent
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import logging

app = FastAPI()

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL del frontend Vite
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
