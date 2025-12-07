import re
import time
import json
from typing import List
from google.cloud import documentai
from google.cloud import storage
from langchain_core.documents import Document
from .base import BaseLoader
from .document_ai_common import DocumentAILayoutMixin
from .utils import summarize_text
import config
import os

class DocumentAIBatchLoader(BaseLoader, DocumentAILayoutMixin):
    """Parses PDF using Document AI Batch Processing (Async GCS)."""

    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.DOCAI_LOCATION
        self.processor_id = config.DOCAI_PROCESSOR_ID
        self.gcs_bucket_name = config.GCS_BUCKET_NAME
        
        # Clients
        self.storage_client = storage.Client(project=self.project_id)
        opts = {"api_endpoint": f"{self.location}-documentai.googleapis.com"}
        self.docai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

    def load_and_chunk(self, file_path: str, variant: str, original_filename: str = None) -> List[Document]:
        print(f" -> [DocAI Batch] 1. Uploading {file_path} to GCS...")
        gcs_uri = self._upload_to_gcs(file_path, original_filename)
        
        print(f" -> [DocAI Batch] 2. Submitting Batch Job...")
        operation = self._batch_process(gcs_uri)
        
        print(f" -> [DocAI Batch] 3. Waiting for completion (this may take a minute)...")
        # Wait for operation
        operation.result(timeout=300)
        
        print(f" -> [DocAI Batch] 4. Downloading Results...")
        docai_shards = self._get_results(gcs_uri)
        
        print(f" -> [DocAI Batch] 5. Structural Chunking...")
        chunks = self._layout_chunking(docai_shards, variant)
        
        print(f" -> [DocAI Batch] 6. Summarizing {len(chunks)} chunks...")
        for i, doc in enumerate(chunks):
            # print(f"    - Summarizing chunk {i+1}/{len(chunks)}...") # Optional verbosity
            summary = summarize_text(doc.page_content)
            doc.metadata["summary"] = summary
            doc.metadata["source_file"] = original_filename if original_filename else file_path.split("/")[-1]
            if "page" not in doc.metadata:
                doc.metadata["page"] = "unknown"
            
        return chunks

    def _upload_to_gcs(self, file_path: str, original_filename: str = None) -> str:
        """Uploads file to GCS staging bucket."""
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        
        # Determine blob name: preserve original filename if possible, otherwise use local basename.
        # Use a flat 'uploads/' directory or 'uploads/{original}' logic.
        # To strictly "preserve the filename" as requested, we should use it as the blob basename.
        filename = original_filename if original_filename else os.path.basename(file_path)
        blob_name = f"uploads/{filename}"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        return f"gs://{self.gcs_bucket_name}/{blob_name}"

    def _batch_process(self, gcs_input_uri: str):
        """Submits async Batch Process."""
        # Output info
        destination_uri = f"{gcs_input_uri.replace('uploads/', 'processed/')}/"
        
        # Check permission helper if needed (we assume setup is done)
        
        # API Config
        name = self.docai_client.processor_path(self.project_id, self.location, self.processor_id)
        
        input_config = documentai.BatchDocumentsInputConfig(
            gcs_documents=documentai.GcsDocuments(
                documents=[{"gcs_uri": gcs_input_uri, "mime_type": "application/pdf"}]
            )
        )
        
        output_config = documentai.DocumentOutputConfig(
            gcs_output_config={"gcs_uri": destination_uri}
        )
        
        request = documentai.BatchProcessRequest(
            name=name,
            input_documents=input_config,
            document_output_config=output_config,
        )
        
        return self.docai_client.batch_process_documents(request=request)

    def _get_results(self, gcs_input_uri: str) -> List[documentai.Document]:
        """Downloads the JSON output from GCS."""
        # The output path matches the input structure
        # destination_uri was gs://bucket/processed/filename.pdf/
        # DocAI appends an ID to the folder: destination_uri + <id>/...
        # Simpler approach: List blobs in the parent directory
        
        prefix = gcs_input_uri.replace("gs://", "").split("/", 1)[1]
        prefix = prefix.replace("uploads/", "processed/")
        
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        results = []
        for blob in blobs:
            if blob.name.endswith(".json"):
                print(f"    - Found output: {blob.name}")
                json_content = blob.download_as_string()
                doc = documentai.Document.from_json(json_content, ignore_unknown_fields=True)
                results.append(doc)
        
        # Sort shards by page number if needed (usually handled by list order, 
        # but DocAI output is often one file unless huge. Multi-file output logic might be needed for huge files)
        return results
