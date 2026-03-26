"""
Index compliance PDFs into ChromaDB using Vertex AI Embeddings.

CHANGES:
- VertexAIEmbeddings instead of AzureOpenAIEmbeddings
- ChromaDB instead of Azure AI Search
- Simpler: no Azure Search API key needed
"""
import os
import glob
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import Chroma

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("indexer")


def index_docs():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, "../../backend/data")

    # Initialize Vertex AI Embeddings
    embeddings = VertexAIEmbeddings(
        model_name=os.getenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005"),
        project=os.getenv("GCP_PROJECT_ID"),
    )

    # Find PDFs
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {data_folder}")
        return

    logger.info(f"Found {len(pdf_files)} PDFs")

    all_splits = []
    for pdf_path in pdf_files:
        loader = PyPDFLoader(pdf_path)
        raw_docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        splits = text_splitter.split_documents(raw_docs)

        for split in splits:
            split.metadata["source"] = os.path.basename(pdf_path)

        all_splits.extend(splits)
        logger.info(f"  -> {os.path.basename(pdf_path)}: {len(splits)} chunks")

    # Store in ChromaDB
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    Chroma.from_documents(
        documents=all_splits,
        embedding=embeddings,
        persist_directory=persist_dir,
    )

    logger.info(f"✅ Indexed {len(all_splits)} chunks into ChromaDB at {persist_dir}")


if __name__ == "__main__":
    index_docs()
