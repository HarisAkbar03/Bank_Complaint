
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_core.output_parsers import StrOutputParser

from rag.retrieval import retrieve


# Step 1: Retrieve documents using your existing code
def get_context(question):
    results = retrieve(
        query=question,
        top_k=3,
        candidate_k=20,
        rerank=True
    )
    print("\nRETRIEVED CHUNKS:")
    for chunk in results["results"]:
        print(
            chunk["rank"],
            chunk["chunk_id"],
            chunk["reranked_score"]
        )
        print(chunk["text"][:200])
    return "\n\n".join(
        f"Chunk ID: {chunk['chunk_id']}\n"
        f"Content: {chunk['text']}"
        for chunk in results["results"]
    )


# Step 2: Wrap your retrieval function
retriever = RunnableLambda(get_context)


# Step 3: Create prompt
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Answer using only the provided context. "
        "If the answer is not available, say you don't know. "
        "Cite relevant chunk IDs."
    ),
    (
        "human",
        "Question: {question}\n\nContext: {context}"
    )
])


# Step 4: Connect Qwen through Ollama
llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0,
    num_ctx=8192
)


# Step 5: Create LangChain pipeline
rag_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)


# Step 6: Run application
if __name__ == "__main__":
    question = input("Ask a question: ")

    answer = rag_chain.invoke(question)

    print("\nAnswer:")
    print(answer)
