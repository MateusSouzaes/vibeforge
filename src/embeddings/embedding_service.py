import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def gerar_embedding(texto):
    response = genai.embed_content(
        model="models/embedding-001",
        content=texto
    )
    return response["embedding"]