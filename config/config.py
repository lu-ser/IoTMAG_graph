# config/config.py
import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any
from groq import Groq
from openai import OpenAI


def load_config() -> Dict[str, Any]:
    # Ottieni il path assoluto della directory del progetto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Carica le variabili d'ambiente dal file .env nella root
    load_dotenv(os.path.join(project_root, ".env"))

    # Carica la configurazione YAML
    config_path = os.path.join(project_root, "config", "config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Aggiungi le API keys dalle variabili d'ambiente
    config["api_keys"] = {
        "groq": os.getenv("GROQ_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
    }

    return config
