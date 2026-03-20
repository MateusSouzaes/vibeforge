from src.rag.rag_service import perguntar

def analisar_codigo(codigo):
    prompt = f"""
    Analise o código abaixo com base em boas práticas:

    {codigo}

    Diga:
    - pontos fortes
    - problemas
    - melhorias
    """

    return perguntar(prompt)