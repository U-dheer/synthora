from langchain_pinecone import PineconeVectorStore


async def store_in_pinecone(chunks: list, embeddings):
	vector_store = PineconeVectorStore(index=index, embedding=embeddings)
	return vector_store
