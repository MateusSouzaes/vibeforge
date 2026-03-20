import google.generativeai as genai
from src.embeddings.embedding_service import gerar_embedding
from src.rag.vector_db import buscar
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def perguntar(pergunta):
    emb = gerar_embedding(pergunta)

    resultados = buscar(emb)

    contexto = "\n\n".join(resultados["documents"][0])

    resposta = model.generate_content(f"""
    Você é um especialista em engenharia de software.

    Baseie-se no estilo do Akita.

    Pergunta:
    {pergunta}

    Contexto:
    {contexto}
    """)

    return resposta.text