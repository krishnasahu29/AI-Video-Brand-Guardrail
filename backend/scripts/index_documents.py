from pypdf._utils import logger_warning
from langchain_openai import AzureOpenAIEmbeddings
import os
import glob
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

# Document loaders and splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Azure Components
from langchain_openai import AzureChatOpenAI
from langchain_community.vectorstores import AzureSearch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('indexer')

def index_documents():
    '''
    Reads the PDFs, chunks them and uploads them to Azure AI Search
    '''

    # Define paths, we look for data folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, '../../backend/data', )

    #Check on the environment variables
    logger.info("="*60)
    logger.info("Environment Configuration Check: ")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT',)}")
    logger.info(f"EMBEDDING_DEPLOYMENT: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT',)}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME',)}")
    logger.info("="*60)

    # Validate required environment variables    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_SEARCH_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    logger.info("All required environment variables are set.")


    # Initialize the embedding model: turns text into vectors

    try:
        logger.info("Initializing Azure OpenAI Embeddings...")
        embedding_client = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

        logger.info("Successfully initialized Azure OpenAI Embeddings.")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI Embeddings: {e}")
        return False

    # Prepare the Azure Search Connection
    try:
        logger.info("Initializing Azure Search connection...")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=index_name,
            embedding_function=embedding_client.embed_query
        )
        logger.info(f"✓ Vector store initialized for index: {index_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search: {e}")
        return False

    # Find PDF files
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger_warning(f"No PDFs found in the {data_folder}. Please add files")

    logger.info(f"Found {len(pdf_files)} PDF files to process : {[os.path.basename(f) for f in pdf_files]}")

    all_splits = []

    # Process each pdf
    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading : {os.path.basename(pdf_path)}...")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            # Chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )

            splits = text_splitter.split_documents(raw_docs)

            for split in splits:
                split.metadata['source'] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Split into {len(splits)} chunks.")

        except Exception as e:
            logger.error(f"Failed to process {pdf_path} : {e}")

    #Uploading to Azure AI Search
    if not all_splits:
        logger.warning("No splits generated. Skipping upload.")
        return False

    logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search...")
    try:
        vector_store.add_documents(all_splits)
        logger.info('='*60)
        logger.info(f"Successfully uploaded {len(all_splits)} chunks to Azure Search.")
        logger.info('='*60)
        return True
    except Exception as e:
        logger.error(f"Failed to upload to Azure Search: {e}")
        return False

if __name__ == "__main__":
    index_documents()

