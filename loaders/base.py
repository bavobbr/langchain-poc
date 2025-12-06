from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

class BaseLoader(ABC):
    """Abstract base class for PDF ingestion implementations."""
    
    @abstractmethod
    def load_and_chunk(self, file_path: str, variant: str) -> List[Document]:
        """Parses a PDF and returns a list of semantically chunked Documents."""
        pass
