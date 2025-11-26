from langchain_google_genai import GoogleGenerativeAIEmbeddings
import getpass
import os
import dotenv

dotenv.load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

async def embed_text(chunks: list):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    texts = [chunk.page_content for chunk in chunks]
    
    chunk_embeddings = embeddings.embed_documents(texts)
    
    print(f"Generated {len(chunk_embeddings)} embeddings.")
    return embeddings

# AIzaSyDI-6wjA0eOofqgn4UcXAn5lJc7eMUFPVw