from agents.entity_extraction_agent import EntityExtractionAgent
import json


def test_entity_extraction():
    # Inizializza l'agente
    agent = EntityExtractionAgent()

    # Test messages
    messages = [
        """Mi chiamo Marco e sono uno sviluppatore software. 
        Lavoro principalmente con Python e JavaScript, ma nel tempo libero 
        mi piace suonare la chitarra e fare escursioni in montagna.""",
        """Ultimamente sto studiando machine learning e deep learning. 
        Ho anche iniziato un corso di fotografia digitale perché voglio 
        unire la mia passione per la tecnologia con l'arte.""",
    ]

    # Processa ogni messaggio e stampa i risultati
    for i, message in enumerate(messages, 1):
        print(f"\n--- Processing Message {i} ---")
        print(f"Message: {message}\n")

        entities, relations = agent.process_message(message)

        print("Extracted Entities:")
        for entity in entities:
            print(f"\nName: {entity.name}")
            print(f"Type: {entity.type}")
            print(f"Attributes: {entity.attributes}")

        print("\nExtracted Relations:")
        for relation in relations:
            print(f"\nSource: {relation.source}")
            print(f"Target: {relation.target}")
            print(f"Type: {relation.type}")
            print(f"Weight: {relation.weight}")

    # Alla fine, stampa l'intero grafo
    print("\n--- Final Graph State ---")
    graph_data = agent.get_graph_data()
    print(json.dumps(graph_data, indent=2))


if __name__ == "__main__":
    test_entity_extraction()
