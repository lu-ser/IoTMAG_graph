from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import os
import yaml
from dotenv import load_dotenv


class LangChainAgent:
    def __init__(
        self,
        provider: str = "groq",
        system: str = "",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.config = config or self.load_config()
        self.provider = provider.lower()
        self.system_message = system
        self.messages = []
        self.llm = self._initialize_llm()

        if self.system_message:
            self.messages.append(SystemMessage(content=system))

    @staticmethod
    def load_config() -> Dict[str, Any]:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, ".env"))
        config_path = os.path.join(project_root, "config", "config.yaml")
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        config["api_keys"] = {
            "groq": os.getenv("GROQ_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
        }
        return config

    def _initialize_llm(self) -> BaseChatModel:
        if self.provider == "groq":
            if not self.config["api_keys"]["groq"]:
                raise ValueError("GROQ_API_KEY mancante")
            return ChatGroq(
                api_key=self.config["api_keys"]["groq"],
                model_name=self.config["providers"]["groq"]["model"],
                temperature=self.config["providers"]["groq"].get("temperature", 0),
            )
        elif self.provider == "openai":
            if not self.config["api_keys"]["openai"]:
                raise ValueError("OPENAI_API_KEY mancante")
            return ChatOpenAI(
                api_key=self.config["api_keys"]["openai"],
                model_name=self.config["providers"]["openai"]["model"],
                temperature=self.config["providers"]["openai"].get("temperature", 0),
            )
        else:
            raise ValueError(f"Provider {self.provider} non supportato")

    def add_message(self, message: str, role: str = "human") -> None:
        if role == "human":
            self.messages.append(HumanMessage(content=message))
        elif role == "ai":
            self.messages.append(AIMessage(content=message))
        elif role == "system":
            self.messages.append(SystemMessage(content=message))

    def get_response(self) -> str:
        response = self.llm.invoke(self.messages)
        self.messages.append(AIMessage(content=response.content))
        return response.content

    def get_conversation_history(self) -> list:
        return [{"role": msg.type, "content": msg.content} for msg in self.messages]
