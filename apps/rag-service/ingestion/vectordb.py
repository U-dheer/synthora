import uuid
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import getpass
import os
import dotenv
import utils.pine_utils as pine_utils

dotenv.load_dotenv()

if not os.getenv("PINECONE_API_KEY"):
    os.environ["PINECONE_API_KEY"] = getpass.getpass("Enter your Pinecone API key: ")

pinecone_api_key = os.environ.get("PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index_name = pine_utils.index_name

if not pc.has_index(pine_utils.index_name):
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)


async def store_in_pinecone(embeddings , documents,document_id):
    vector_store = PineconeVectorStore(index=index, embedding=embeddings,namespace="default")

    for doc in documents:
        if not doc.metadata:
            doc.metadata = {}
        doc.metadata["document_id"]= document_id 
        
    vector_store.add_documents(documents)
    
    return [doc.metadata.get("document_id") for doc in documents]
