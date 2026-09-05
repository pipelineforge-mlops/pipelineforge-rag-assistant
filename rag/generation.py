"""
generation.py — PipelineForge RAG (Hafsa Elhilali, Sprint 3)

Construit le prompt à partir des chunks récupérés et appelle le LLM (Groq)
pour générer une réponse sourcée.
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

LLM_MODEL = "openai/gpt-oss-20b"

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def build_prompt(question: str, chunks: list[dict]) -> str:
    """
    Construit le prompt en insérant les extraits récupérés comme contexte.
    """
    context_parts = []
    for i, chunk in enumerate(chunks):
        title = chunk["metadata"].get("title", "Titre inconnu")
        context_parts.append(f"[Source {i+1} — {title}]\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    prompt = f"""Tu es un assistant scientifique. Réponds TOUJOURS en français, même si
les extraits fournis sont en anglais. Réponds à la question uniquement
en te basant sur les extraits d'articles fournis ci-dessous. Si les extraits ne
contiennent pas assez d'information pour répondre, dis-le clairement plutôt que
d'inventer une réponse. Cite le numéro de la source pertinente entre crochets, ex. [Source 1].

Extraits :
{context}

Question : {question}

Réponse :"""

    return prompt


def generate_answer(question: str, chunks: list[dict]) -> str:
    """
    Génère une réponse sourcée à partir de la question et des chunks récupérés.
    """
    prompt = build_prompt(question, chunks)

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    from retriever import retrieve

    question = "What are the side effects of chemotherapy in cancer patients?"
    chunks = retrieve(question, top_k=3)
    answer = generate_answer(question, chunks)
    print(answer)