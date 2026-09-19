"""
test_rag.py — PipelineForge RAG (Hafsa Elhilali, Sprint 3)

Jeu de questions de test représentatif du domaine (santé/biomédical),
basé sur les mots-clés de collecte du Sprint 1. Chaque question est
tracée dans MLflow via rag_chain.answer_question().
"""

from rag_chain import answer_question

TEST_QUESTIONS = [
    "What are the side effects of chemotherapy in cancer patients?",
    "How is diabetes diagnosed?",
    "What treatments exist for cardiovascular disease?",
    "What are the risk factors for infectious disease outbreaks?",
    "How effective are vaccines against common infectious diseases?",
    "What are the phases of a clinical trial?",
    "How does machine learning help in medical diagnosis?",
    "What are common epidemiological methods used to study public health?",
]


def run_all():
    for i, question in enumerate(TEST_QUESTIONS):
        print(f"\n{'='*80}")
        print(f"[{i+1}/{len(TEST_QUESTIONS)}] QUESTION : {question}")
        print('='*80)

        result = answer_question(question, top_k=5)

        print("\nRÉPONSE :")
        print(result["answer"])

        print("\nSOURCES :")
        for s in result["sources"]:
            print(f"- {s['title']} (section: {s['section']}, distance: {s['distance']:.4f})")


if __name__ == "__main__":
    run_all()