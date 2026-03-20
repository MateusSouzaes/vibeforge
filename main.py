from src.rag.rag_service import perguntar

while True:
    pergunta = input("Pergunta: ")

    resposta = perguntar(pergunta)

    print("\nResposta:\n", resposta)