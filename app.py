import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.llms import CTransformers

# --- Load all configurations and models ONCE on startup ---

# !!! IMPORTANT: SET YOUR MODEL PATH AND INDEX NAME HERE !!!
MODEL_PATH = r"C:\Users\Admin\Downloads\llama-2-7b-chat.ggmlv3.q4_0.bin" # Update this path to your local Llama 2 model

INDEX_NAME = "medical-bot"  # Must match the name in ingest.py
INDEX_NAME = "medical-bot"  # Must match the name in ingest.py

# Load environment variables (PINECONE_API_KEY)
load_dotenv()

# This is the prompt template.
custom_prompt_template = """
Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
This is a medical bot, and accuracy is critical.

Context: {context}
Question: {question}

Only return the helpful answer below and nothing else.
Helpful answer:
"""

def set_custom_prompt():
    prompt = PromptTemplate(
        template=custom_prompt_template,
        input_variables=['context', 'question']
    )
    return prompt

def load_llm():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
    print("Loading local LLM...")
    llm = CTransformers(
        model=MODEL_PATH,
        model_type="llama",
        config={'max_new_tokens': 512, 'temperature': 0.8}
    )
    print("LLM loaded successfully.")
    return llm

def retrieval_qa_chain(llm, prompt, vectorstore):
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={'k': 2}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain

def load_bot():
    """
    Called once to load all components into memory.
    """
    print("Setting up the bot...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    print(f"Loading vector store from Pinecone index '{INDEX_NAME}'...")
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    print("Vector store loaded.")
    
    llm = load_llm()
    
    qa_prompt = set_custom_prompt()
    
    bot = retrieval_qa_chain(llm, qa_prompt, vectorstore)
    
    print("__Bot is ready!__")
    return bot

# --- Initialize Flask App and Load the Bot ---
app = Flask(__name__)

# Try to load the bot. If it fails, the app won't start.
try:
    bot = load_bot()
except FileNotFoundError as e:
    print(f"FATAL ERROR: {e}")
    print("Please update 'MODEL_PATH' in app.py before running.")
    bot = None
except Exception as e:
    print(f"An error occurred during bot setup: {e}")
    bot = None

# --- Define API Routes ---

@app.route("/")
def home():
    """
    This route serves your index.html file (the frontend).
    """
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    This is the API endpoint your JavaScript will call.
    It takes a JSON message and returns a JSON answer.
    """
    if bot is None:
        return jsonify({"answer": "Bot is not configured. Check server logs."}), 500

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Get the response from the bot
        # We use .invoke() as recommended by the deprecation warning
        response = bot.invoke({'query': user_message})
        
        # Create a clean JSON response
        return jsonify({
            "answer": response["result"],
            "sources": [doc.metadata.get('source', 'N/A') for doc in response["source_documents"]]
        })
    except Exception as e:
        print(f"Error during chat: {e}")
        return jsonify({"answer": "Sorry, an error occurred while processing your request."}), 500

# --- Run the Flask App ---
if __name__ == "__main__":
    app.run(debug=True)