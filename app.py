import os
import subprocess
from pathlib import Path
import glob

import uvicorn
from fastapi import FastAPI, UploadFile
from langchain.document_loaders import PyPDFLoader, PyPDFDirectoryLoader
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from data import Message
from sql import get_info_from_sql, delete_all_from_sql
from utils import text_to_pdf
import time
import json

REFRESH_ENDPOINT = "/api/refresh_data"
MESSAGE_ENDPOINT = "/api/message"
PDF_UPLOAD_ENDPOINT = "/api/pdf/upload"
PDF_LIST_ENDPOINT = "/api/pdf/list"
PDF_DOWNLOAD_ENDPOING = "/api/pdf/download"
PDF_DELETE_ENDPOINT = "/api/pdf/delete"

model_name_embeddings = "text-embedding-ada-002"
THIS_DIR = Path(__file__).parent
pdf_storage_dir = "pdf_store"
# Create storage for PDFs
if os.path.exists(pdf_storage_dir):
    print("Pdf storage exists")
else:
    os.mkdir(pdf_storage_dir)
    print("Pdf doesn't storage exist\ncreating")

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

system_template = """You are BeAI Support Assistant from BeNFT Solutions. Use the following pieces of context to 
answer the users question. Don't mention the source file path in any way. Do not answer questions that are not 
related to BeNFT topics. Keep it on the topic of BeNFT very strictly. Your knowledge is limited to topics related to 
BeNFT, blockchain, smart contracts, and AI. If you don't know the answer, just say that "I don't know", don't try to 
make up an answer. Answer only about BENFT related questions. If question is not related to BeNFT, just say that "I'm 
sorry, but that topic is not related to BeNFT, blockchain, smart contracts, or AI. My knowledge is limited to those 
topics, so I won't be able to provide a relevant answer. Is there anything else related to BeNFT or the 
aforementioned topics that I can help you with?". ---------------- {summaries} """
messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}")
]
prompt = ChatPromptTemplate.from_messages(messages)

chain_type_kwargs = {"prompt": prompt}
llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0.7,
                 max_tokens=256)  # Modify model_name if you have access to GPT-4

app = FastAPI()


# Define the endpoint for handling queries
@app.post(REFRESH_ENDPOINT)
async def refresh_data():
    try:
        pdf_path = Path(THIS_DIR / "beNFT.pdf")
        if pdf_path.exists():
            # Delete the file
            pdf_path.unlink()
        # Set the directory where the scrapy project is located
        scrapy_project_dir = Path(__file__).parent / "scrapper"
        # Delete the database
        delete_all_from_sql(str(scrapy_project_dir / 'articles.sqlite'))

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

        '''file = str(THIS_DIR / "beNFT.pdf")
        loader = PyPDFLoader(file)
        input_text = loader.load_and_split()
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(input_text, embeddings)'''
        pdf_files = glob.glob(os.path.join(pdf_storage_dir, '*.pdf'))
        pdf_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        newest_files = pdf_files[:10]
        files_used = ""
        #input_text = None
        #loader = PyPDFLoader(newest_files)
        if os.path.exists(pdf_storage_dir + "/tmp"):
            #print("Pdf storage exists")
            #os.rmdir
            files = glob.glob(os.path.join(pdf_storage_dir+"/tmp", '*'))
            for f in files:
                os.remove(f)
        else:
            os.mkdir(pdf_storage_dir + "/tmp")

        for file in newest_files:
            source_path = os.path.abspath(file)  # Get the absolute path of the file
            destination_path = os.path.join(pdf_storage_dir + "/tmp", os.path.basename(file))  # Create the destination path in the tmp directory
            files_used += file + " "
            # Read the contents of the source file
            with open(source_path, "rb") as source_file:
                # Create the destination file and write the contents
                with open(destination_path, "wb") as destination_file:
                    destination_file.write(source_file.read())
        loader = PyPDFDirectoryLoader(pdf_storage_dir + "/tmp")
        input_text =  loader.load()
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(input_text, embeddings)
        # Save the files to local disk.
        vector_store.save_local("data_store")

        return {"result": "Database updated\n" + str(files_used)}

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

@app.get(PDF_LIST_ENDPOINT)
async def get_pdf_list():
    if not os.path.isdir(pdf_storage_dir):
        return {"error": "Invalid directory path"}

    files = os.listdir(pdf_storage_dir)
    content = []

    for file_name in files:
        content.append(file_name)

    return json.dumps(content)

@app.post(PDF_UPLOAD_ENDPOINT)
async def upload_pdf(file: UploadFile = UploadFile(...)):
    # Save the uploaded PDF file
    print("Uploading of " + file.filename)
    #text_output = "./storage/txt/output.txt"
    with open(pdf_storage_dir + "/" + file.filename, "wb") as f:
        f.write(await file.read())

@app.post(PDF_DELETE_ENDPOINT)
async def delete_pdf(file_name: str):
    # Save the uploaded PDF file
    print("deleting of " + file.filename)
    try:
        os.remove(pdf_storage_dir + "/" +file_name)
        return {"message": f"File '{file_name}' deleted successfully."}
    except FileNotFoundError:
        return {"message": f"File '{file_name}' not found."}
    except Exception as e:
        return {"message": f"An error occurred while deleting the file: {str(e)}"}

@app.get("/update_file_timestamp")
async def update_file_timestamp(filename: str):
    # Specify the directory where the file is located

    # Check if the file exists in the directory
    file_path = os.path.join(pdf_storage_dir, filename)
    if os.path.isfile(file_path):
        # Get the current timestamp
        current_time = time.time()

        # Update the file's modified timestamp
        os.utime(file_path, (current_time, current_time))

        return {"message": f"File '{filename}' timestamp updated."}
    else:
        return {"message": f"File '{filename}' not found."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)