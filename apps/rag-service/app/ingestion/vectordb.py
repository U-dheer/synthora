from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import getpass
import os
import dotenv

dotenv.load_dotenv()

if not os.getenv("PINECONE_API_KEY"):
    os.environ["PINECONE_API_KEY"] = getpass.getpass("Enter your Pinecone API key: ")

pinecone_api_key = os.environ.get("PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index_name = "sinthora-3"  # change if desired

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)


async def store_in_pinecone(embeddings , documents):
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    vector_store.add_documents(documents)
    return vector_store
