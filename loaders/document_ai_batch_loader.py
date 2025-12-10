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
from logger import get_logger

logger = get_logger(__name__)
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
        """Orchestrate the full Batch Ingestion Flow."""
        
        # 1. Upload
        logger.info(f"Uploading {file_path} to GCS...")
        gcs_uri = self._upload_to_gcs(file_path, original_filename)
        
        # 2. Trigger Batch Check
        logger.info("Submitting Batch Job...")
        operation = self._batch_process(gcs_uri)
        
        # 3. Wait LRO
        logger.info("Waiting for completion (this may take a minute)...")
        operation.result(timeout=300)
        
        # Extract Operation ID from name: projects/.../operations/123456...
        op_id = operation.operation.name.split("/")[-1]
        
        # 4. Download JSONs
        logger.info(f"Downloading Results (Operation: {op_id})...")
        docai_shards = self._get_results(gcs_uri, op_id)
        
        # 5. Visual/Layout Chunking
        logger.info("Structural Chunking...")
        chunks = self._layout_chunking(docai_shards, variant)
        
        # 6. Summarization / Enrichment
        logger.info(f"Summarizing {len(chunks)} chunks...")
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
        """Submits async Batch Process.

        Wraps the API call to surface actionable IAM guidance when running on
        Cloud Run with insufficient permissions on the staging GCS bucket or
        Document AI. This preserves the original behavior locally while
        improving diagnostics in managed environments.
        """
        # Output info
        destination_uri = f"{gcs_input_uri.replace('uploads/', 'processed/')}/"

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

        try:
            return self.docai_client.batch_process_documents(request=request)
        except Exception as e:
            # Common case on Cloud Run: either the Cloud Run Service Account or
            # the Document AI service agent lacks GCS permissions.
            bucket = self.gcs_bucket_name
            guidance = (
                "Document AI batch call failed. Likely IAM on GCS bucket or Document AI.\n"
                f"  - Bucket: gs://{bucket}\n"
                f"  - Project: {self.project_id}\n"
                f"  - Location: {self.location}\n\n"
                "Grant required roles (replace <RUN_SA> and <PROJECT_NUMBER>):\n"
                f"  • Cloud Run SA → bucket: gsutil iam ch serviceAccount:<RUN_SA>:roles/storage.objectAdmin gs://{bucket}\n"
                f"  • DocAI service agent → bucket: gsutil iam ch serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-documentai.iam.gserviceaccount.com:roles/storage.objectAdmin gs://{bucket}\n"
                "  • Cloud Run SA → Document AI: gcloud projects add-iam-policy-binding <PROJECT_ID> \\\n+  --member=serviceAccount:<RUN_SA> --role=roles/documentai.apiUser\n"
            )
            raise RuntimeError(f"batch_process_documents error: {e}\n\n{guidance}")

    def _get_results(self, gcs_input_uri: str, op_id: str) -> List[documentai.Document]:
        """Downloads the JSON output from GCS."""
        # The output path matched the input structure
        # destination_uri was gs://bucket/processed/filename.pdf/
        # DocAI appends an ID to the folder: destination_uri + <id>/...
        
        prefix = gcs_input_uri.replace("gs://", "").split("/", 1)[1]
        prefix = prefix.replace("uploads/", "processed/")
        
        # Append operation ID to target specific run
        prefix = f"{prefix}/{op_id}/"
        
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        try:
            blobs = list(bucket.list_blobs(prefix=prefix))
        except Exception as e:
            guidance = (
                "Unable to list Document AI outputs in GCS.\n"
                f"  - Bucket: gs://{self.gcs_bucket_name}\n"
                f"  - Prefix: {prefix}\n\n"
                f"Ensure Cloud Run service account has roles/storage.objectViewer or objectAdmin on the bucket.\n"
            )
            raise RuntimeError(f"list_blobs error: {e}\n\n{guidance}")
        
        results = []
        for blob in blobs:
            if blob.name.endswith(".json"):
                # logger.debug(f"Found output: {blob.name}")
                json_content = blob.download_as_bytes()
                doc = documentai.Document.from_json(json_content, ignore_unknown_fields=True)
                results.append(doc)
        
        # Sort shards by page number if needed (usually handled by list order, 
        # but DocAI output is often one file unless huge. Multi-file output logic might be needed for huge files)
