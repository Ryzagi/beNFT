import os
import subprocess
from pathlib import Path
from fastapi import FastAPI
from langchain.document_loaders import PyPDFLoader
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from data import Message
from sql import get_info_from_sql
from utils import text_to_pdf

REFRESH_ENDPOINT = "/api/refresh_data"
MESSAGE_ENDPOINT = "/api/message"
model_name_embeddings = "text-embedding-ada-002"
THIS_DIR = Path(__file__).parent
# Create datastore
if os.path.exists("data_store"):
    vector_store = FAISS.load_local(
        "data_store",
        OpenAIEmbeddings()
    )
else:
    file = str(THIS_DIR / "beNFT.pdf")
    loader = PyPDFLoader(file)
    input_text = loader.load_and_split()
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(input_text, embeddings)
    # Save the files `to local disk.
    vector_store.save_local("data_store")

print("Index is built")

system_template = """You are BeAI Support Assistant from BeNFT Solutions. Use the following pieces of context to answer the users question.
If you don't know the answer, just say that "I don't know", don't try to make up an answer.
----------------
{summaries}"""
messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}")
]
prompt = ChatPromptTemplate.from_messages(messages)

chain_type_kwargs = {"prompt": prompt}
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7,
                 max_tokens=256)  # Modify model_name if you have access to GPT-4

app = FastAPI()


# Define the endpoint for handling queries
@app.post(REFRESH_ENDPOINT)
async def refresh_data():
    try:
        pdf_path = Path(THIS_DIR / "beNFT.pdf")
        # Delete the file
        pdf_path.unlink()
        # Set the directory where the scrapy project is located
        scrapy_project_dir = Path(__file__).parent / "scrapper"

        # Set the command to run
        command = ['scrapy', 'crawl', 'benft']

        # Run the command in the scrapy project directory
        subprocess.check_output(command, cwd=scrapy_project_dir)

        texts = get_info_from_sql(str(scrapy_project_dir / 'articles.sqlite'))

        # Open a text file in write mode
        with open(THIS_DIR / "beNFT.txt", "w", encoding="utf-8") as f:
            # Write the text to the file
            for string in texts:
                f.write(string)

        text_to_pdf(texts, THIS_DIR / "beNFT.pdf")

        file = str(THIS_DIR / "beNFT.pdf")
        loader = PyPDFLoader(file)
        input_text = loader.load_and_split()
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(input_text, embeddings)

        # Save the files `to local disk.
        vector_store.save_local("data_store")

        return {"result": "Database updated"}

    except Exception as e:
        return {"result": str(e)}


# Define the endpoint for handling queries
@app.post(MESSAGE_ENDPOINT)
async def handle_query(request: Message):
    if os.path.exists("data_store"):
        vector_store = FAISS.load_local(
            "data_store",
            OpenAIEmbeddings()
        )
    else:
        file = str(THIS_DIR / "beNFT.pdf")
        loader = PyPDFLoader(file)
        input_text = loader.load_and_split()
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(input_text, embeddings)
        # Save the files `to local disk.
        vector_store.save_local("data_store")

    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs=chain_type_kwargs
    )
    result_text = chain(request.message)
    return {"result": result_text['answer']}
