from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import tempfile
import os

async def load_document(file: UploadFile):
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        file_extension = file.filename.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            loader = PyPDFLoader(tmp_file_path)
        elif file_extension in ['docx', 'doc']:
            loader = Docx2txtLoader(tmp_file_path)
        elif file_extension == 'txt':
            loader = TextLoader(tmp_file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        documents = loader.load()
        
        return documents
    except Exception as e:
        raise ValueError(f"Failed to load document: {str(e)}")
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)