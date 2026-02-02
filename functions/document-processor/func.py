"""
OCI Document Understanding - Invoice Extraction Function

This function processes PDF invoices using OCI Document Understanding
and triggers GenAI fallback for low-confidence results.
"""

import io
import json
import logging
import os
from datetime import datetime

import oci
from fdk import response

# Configuration
CONFIDENCE_THRESHOLD = float(os.environ.get("DU_CONFIDENCE_THRESHOLD", "0.85"))
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET")
NOSQL_TABLE = os.environ.get("NOSQL_TABLE")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_signer():
    """Get OCI signer using resource principal (for Functions)."""
    return oci.auth.signers.get_resource_principals_signer()


def extract_invoice_with_du(namespace: str, bucket: str, object_name: str) -> dict:
    """
    Extract invoice data using OCI Document Understanding.

    Args:
        namespace: Object Storage namespace
        bucket: Bucket containing the PDF
        object_name: PDF object name

    Returns:
        dict: Extraction results with confidence scores
    """
    signer = get_signer()

    # Initialize Document Understanding client
    du_client = oci.ai_document.AIServiceDocumentClient(config={}, signer=signer)

    # Create processor job for invoice extraction
    create_processor_job_details = oci.ai_document.models.CreateProcessorJobDetails(
        input_location=oci.ai_document.models.ObjectLocation(
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=object_name
        ),
        output_location=oci.ai_document.models.OutputLocation(
            namespace_name=namespace,
            bucket_name=RESULTS_BUCKET,
            prefix=f"du-results/{object_name.replace('.pdf', '')}/"
        ),
        processor_config=oci.ai_document.models.GeneralProcessorConfig(
            processor_type="GENERAL",
            features=[
                oci.ai_document.models.DocumentFeature(
                    feature_type="KEY_VALUE_EXTRACTION"
                ),
                oci.ai_document.models.DocumentFeature(
                    feature_type="TABLE_EXTRACTION"
                ),
                oci.ai_document.models.DocumentFeature(
                    feature_type="DOCUMENT_CLASSIFICATION"
                )
            ]
        )
    )

    # Submit job
    job_response = du_client.create_processor_job(create_processor_job_details)
    job_id = job_response.data.id
    logger.info(f"Document Understanding job created: {job_id}")

    # Wait for completion
    get_job_response = oci.wait_until(
        du_client,
        du_client.get_processor_job(job_id),
        'lifecycle_state',
        'SUCCEEDED',
        max_wait_seconds=300
    )

    # Read results from Object Storage
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    # List result objects
    result_objects = os_client.list_objects(
        namespace,
        RESULTS_BUCKET,
        prefix=f"du-results/{object_name.replace('.pdf', '')}/"
    ).data.objects

    # Parse JSON result
    for obj in result_objects:
        if obj.name.endswith('.json'):
            result_data = os_client.get_object(
                namespace,
                RESULTS_BUCKET,
                obj.name
            ).data.content.decode('utf-8')
            return json.loads(result_data)

    raise Exception("No results found from Document Understanding")


def calculate_overall_confidence(du_result: dict) -> float:
    """Calculate overall confidence from DU extraction results."""
    confidences = []

    # Extract confidence scores from key-value pairs
    if "pages" in du_result:
        for page in du_result["pages"]:
            if "documentFields" in page:
                for field in page["documentFields"]:
                    if "confidence" in field:
                        confidences.append(field["confidence"])

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


def transform_du_to_invoice_schema(du_result: dict) -> dict:
    """
    Transform OCI Document Understanding output to standard invoice schema.

    Maps DU field names to our internal schema used for Fusion transformation.
    """
    invoice_data = {
        "extraction_timestamp": datetime.utcnow().isoformat(),
        "extraction_method": "OCI_DOCUMENT_UNDERSTANDING",
        "vendor": {},
        "invoice_details": {},
        "line_items": [],
        "totals": {},
        "confidence_scores": {}
    }

    field_mapping = {
        "VendorName": ("vendor", "name"),
        "VendorAddress": ("vendor", "address"),
        "VendorTaxId": ("vendor", "tax_id"),
        "InvoiceNumber": ("invoice_details", "number"),
        "InvoiceDate": ("invoice_details", "date"),
        "DueDate": ("invoice_details", "due_date"),
        "PurchaseOrder": ("invoice_details", "po_number"),
        "SubTotal": ("totals", "subtotal"),
        "Tax": ("totals", "tax"),
        "Total": ("totals", "total"),
        "Currency": ("totals", "currency")
    }

    if "pages" in du_result:
        for page in du_result["pages"]:
            if "documentFields" in page:
                for field in page["documentFields"]:
                    field_type = field.get("fieldType", {}).get("name", "")
                    field_value = field.get("fieldValue", {})
                    confidence = field.get("confidence", 0)

                    # Extract text value
                    if "text" in field_value:
                        value = field_value["text"]
                    elif "value" in field_value:
                        value = field_value["value"]
                    else:
                        continue

                    # Map to our schema
                    if field_type in field_mapping:
                        section, key = field_mapping[field_type]
                        invoice_data[section][key] = value
                        invoice_data["confidence_scores"][f"{section}.{key}"] = confidence

            # Extract table data for line items
            if "tables" in page:
                for table in page["tables"]:
                    for row in table.get("rows", []):
                        if row.get("rowType") != "header":
                            line_item = {
                                "cells": [
                                    cell.get("text", "")
                                    for cell in row.get("cells", [])
                                ]
                            }
                            invoice_data["line_items"].append(line_item)

    return invoice_data


def handler(ctx, data: io.BytesIO = None):
    """
    Main function handler for invoice extraction.

    Expects event payload with:
    - namespace: Object Storage namespace
    - bucket: Upload bucket name
    - object_name: PDF file name
    - invoice_id: Unique invoice identifier
    """
    try:
        body = json.loads(data.getvalue())

        namespace = body["namespace"]
        bucket = body["bucket"]
        object_name = body["object_name"]
        invoice_id = body["invoice_id"]

        logger.info(f"Processing invoice: {invoice_id}")

        # Step 1: Extract with OCI Document Understanding
        du_result = extract_invoice_with_du(namespace, bucket, object_name)

        # Step 2: Calculate confidence
        overall_confidence = calculate_overall_confidence(du_result)
        logger.info(f"Extraction confidence: {overall_confidence:.2%}")

        # Step 3: Transform to standard schema
        invoice_data = transform_du_to_invoice_schema(du_result)
        invoice_data["overall_confidence"] = overall_confidence

        # Step 4: Determine if GenAI fallback needed
        needs_genai_validation = overall_confidence < CONFIDENCE_THRESHOLD

        result = {
            "invoice_id": invoice_id,
            "status": "EXTRACTED",
            "overall_confidence": overall_confidence,
            "needs_genai_validation": needs_genai_validation,
            "invoice_data": invoice_data,
            "raw_du_result": du_result
        }

        if needs_genai_validation:
            logger.info(f"Low confidence ({overall_confidence:.2%}), flagging for GenAI validation")
            result["status"] = "NEEDS_VALIDATION"

        return response.Response(
            ctx,
            response_data=json.dumps(result),
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "error": str(e),
                "status": "FAILED"
            }),
            headers={"Content-Type": "application/json"},
            status_code=500
        )
