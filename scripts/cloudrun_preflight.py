"""Cloud Run IAM preflight for Document AI Batch ingestion.

Run this inside the deployed service (or locally with ADC) to verify:
 - Which project and service account are in use
 - GCS access to the staging bucket (list-only)
 - Document AI processor access (get_processor)

It prints clear remediation steps if permissions are missing.
"""

import os
import sys
from typing import Optional
from google.cloud import storage, documentai

import config


def _detect_env() -> dict:
    """Detects runtime context and returns a small metadata dict."""
    env = {
        "k_service": os.getenv("K_SERVICE"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", config.PROJECT_ID),
        "region": os.getenv("GCP_REGION", config.REGION),
        "bucket": config.GCS_BUCKET_NAME,
        "docai_location": config.DOCAI_LOCATION,
        "docai_processor_id": config.DOCAI_PROCESSOR_ID,
    }
    # Best-effort SA email via metadata server if available; otherwise None
    env["service_account_email"] = _metadata_service_account_email()
    return env


def _metadata_service_account_email() -> Optional[str]:
    """Queries metadata server for SA email (works on Cloud Run)."""
    import urllib.request

    url = (
        "http://metadata.google.internal/computeMetadata/v1/instance/"
        "service-accounts/default/email"
    )
    req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:  # nosec - metadata internal
            return resp.read().decode("utf-8").strip()
    except Exception:
        return None


def check_gcs_list(bucket_name: str, project_id: str) -> None:
    print(f"GCS: listing gs://{bucket_name} (project={project_id}) ...")
    client = storage.Client(project=project_id)
    try:
        blobs = list(client.list_blobs(bucket_name, max_results=1))
        if blobs:
            print(f"  ✅ Listed objects (sample): {blobs[0].name}")
        else:
            print("  ✅ Listed bucket (no objects found)")
    except Exception as e:
        print("  ❌ GCS list failed:")
        print(f"     {e}\n")
        print("  Remediation:")
        print(
            "   • Grant your Cloud Run service account storage.objectAdmin (or objectViewer) on the bucket.\n"
            "     Example:\n"
            f"     gsutil iam ch serviceAccount:<RUN_SA_EMAIL>:roles/storage.objectAdmin gs://{bucket_name}\n"
        )


def check_docai_get_processor(project_id: str, location: str, processor_id: str) -> None:
    print(
        f"Document AI: get_processor(project={project_id}, location={location}, processor={processor_id}) ..."
    )
    opts = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(project_id, location, processor_id)
    try:
        _ = client.get_processor(name=name)
        print("  ✅ Processor access OK")
    except Exception as e:
        print("  ❌ Document AI access failed:")
        print(f"     {e}\n")
        print("  Remediation:")
        print(
            "   • Grant your Cloud Run service account Document AI API User (or Processor Invoker on the resource).\n"
            "     Example:\n"
            "     gcloud projects add-iam-policy-binding <PROJECT_ID> \\\n+       --member=serviceAccount:<RUN_SA_EMAIL> --role=roles/documentai.apiUser\n"
        )


def main() -> int:
    env = _detect_env()
    print("--- Cloud Run Preflight ---")
    print(f"Project ID   : {env['project_id']}")
    print(f"Region       : {env['region']}")
    print(f"K_SERVICE    : {env['k_service'] or '(not set)'}")
    print(f"Service Acct : {env['service_account_email'] or '(unknown)'}")
    print(f"Bucket       : {env['bucket']}")
    print(
        f"DocAI        : location={env['docai_location']}, processor={env['docai_processor_id']}"
    )
    print()

    check_gcs_list(env["bucket"], env["project_id"])
    print()
    check_docai_get_processor(env["project_id"], env["docai_location"], env["docai_processor_id"])
    print()

    print(
        "Note: Document AI's service agent also needs storage.objectAdmin on the bucket to read inputs and write outputs:\n"
        "  service-<PROJECT_NUMBER>@gcp-sa-documentai.iam.gserviceaccount.com\n"
        "  gsutil iam ch serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-documentai.iam.gserviceaccount.com:roles/storage.objectAdmin gs://"
        + env["bucket"]
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

