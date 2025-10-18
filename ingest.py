import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

# !!! IMPORTANT: SET YOUR INDEX NAME HERE !!!
# This must match the index name you created in your Pinecone dashboard.
INDEX_NAME = "medical-bot"  # Or whatever you named it

# Load environment variables (PINECONE_API_KEY)
load_dotenv()

DATA_PATH = "data/"

def create_vector_db():
    print(f"Loading documents from {DATA_PATH}...")
    loader = DirectoryLoader(DATA_PATH, glob='*.pdf', loader_cls=PyPDFLoader)
    documents = loader.load()
    if not documents:
        print("No documents found. Please add PDFs to the 'data' folder.")
        return

    print(f"Loaded {len(documents)} document(s).")

    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks.")

    print("Loading embedding model (this may take a moment)...")
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        model_kwargs={'device': 'cpu'}
    )

    print(f"Uploading vectors to Pinecone index '{INDEX_NAME}'...")
    # This command creates and uploads the embeddings
    PineconeVectorStore.from_documents(
        texts,
        embeddings,
        index_name=INDEX_NAME
    )
    print("Successfully uploaded to Pinecone.")

if __name__ == "__main__":
    create_vector_db()