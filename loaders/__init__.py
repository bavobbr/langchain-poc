from .base import BaseLoader
from .unstructured_loader import UnstructuredLoader
from .document_ai_online_loader import DocumentAIOnlineLoader
from .document_ai_batch_loader import DocumentAIBatchLoader
import logging
import config

logger = logging.getLogger(__name__)

def get_document_ai_loader():
    """Factory to return the configured Document AI loader."""
    if config.DOCAI_INGESTION_MODE == "batch":
        logger.info(" [Factory] returning Batch Loader (Async/GCS)")
        return DocumentAIBatchLoader()
    else:
        logger.info(" [Factory] returning Online Loader (Sync/Sharded)")
        return DocumentAIOnlineLoader()

__all__ = ["BaseLoader", "UnstructuredLoader", "get_document_ai_loader"]
