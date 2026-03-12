from langchain_text_splitters import RecursiveCharacterTextSplitter


async def chunk_text(documents: list):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      
        chunk_overlap=5,    
        separators=["\n\n", "\n", " ", ""] 
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Chunked into {len(chunks)} pieces.")
    return chunks
