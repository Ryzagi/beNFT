import os
from pathlib import Path
import sqlite3
from fastapi import FastAPI
from langchain.document_loaders import PyPDFLoader
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

from data import Message

MESSAGE_ENDPOINT = "/api/message"
model_name_embeddings = "text-embedding-ada-002"

# Create datastore
if os.path.exists("data_store"):
    vector_store = FAISS.load_local(
        "data_store",
        OpenAIEmbeddings()
    )
else:
    file = "BeNFT.pdf"
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
                 max_tokens=512)  # Modify model_name if you have access to GPT-4
chain = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs=chain_type_kwargs
)

app = FastAPI()


# Define the endpoint for handling queries
@app.post(MESSAGE_ENDPOINT)
async def handle_query(request: Message):
    result_text = chain(request.message)
    return {"result": result_text['answer']}
