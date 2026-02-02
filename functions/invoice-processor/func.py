"""
OCI GenAI Invoice Processor - Gemini 2.5 Flash

Simple, direct PDF → JSON extraction using Gemini 2.5 Flash multimodal.
This mirrors the invoice-vNext approach (Claude on Bedrock) but uses OCI GenAI.

ARCHITECTURE DECISION: Simple single-model approach
- Original invoice-vNext: PDF → Claude 3.5 Sonnet → JSON
- This version: PDF → Gemini 2.5 Flash → JSON
- Same simplicity, different cloud provider
"""

import base64
import io
import json
import logging
import os
from datetime import datetime

import oci
from fdk import response

# Configuration
GENAI_ENDPOINT = os.environ.get(
    "GENAI_ENDPOINT",
    "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
)
# Gemini 2.5 Flash - multimodal, fast, cost-effective
MODEL_ID = os.environ.get("GENAI_MODEL_ID", "google.gemini-2.5-flash")
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")
COMPARTMENT_OCID = os.environ.get("COMPARTMENT_OCID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_signer():
    """Get OCI signer using resource principal (for Functions)."""
    return oci.auth.signers.get_resource_principals_signer()


def get_document_base64(namespace: str, bucket: str, object_name: str) -> tuple[str, str]:
    """
    Download document from Object Storage and encode as base64.

    Returns:
        tuple: (base64_content, mime_type)
    """
    signer = get_signer()
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    obj = os_client.get_object(namespace, bucket, object_name)
    content = obj.data.content

    # Determine MIME type
    if object_name.lower().endswith('.pdf'):
        mime_type = "application/pdf"
    elif object_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        mime_type = f"image/{object_name.split('.')[-1].lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"
    else:
        mime_type = "application/octet-stream"

    return base64.b64encode(content).decode('utf-8'), mime_type


def extract_invoice_with_gemini(document_base64: str, mime_type: str) -> dict:
    """
    Extract invoice data using OCI GenAI Gemini 2.5 Flash.

    This is a direct equivalent of the Claude 3.5 Sonnet approach in invoice-vNext.
    Gemini 2.5 Flash supports multimodal input (documents, images, etc.)
    """
    signer = get_signer()

    # Initialize GenAI Inference client
    genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config={},
        signer=signer,
        service_endpoint=GENAI_ENDPOINT
    )

    # Extraction prompt - same structure as invoice-vNext
    extraction_prompt = """You are an expert invoice data extraction assistant.

Analyze this invoice document and extract ALL relevant information into a structured JSON format.

REQUIRED OUTPUT SCHEMA:
{
    "vendor": {
        "name": "string - company name on invoice",
        "address": "string - full address",
        "tax_id": "string or null - VAT/Tax ID if present",
        "phone": "string or null",
        "email": "string or null"
    },
    "invoice_details": {
        "number": "string - invoice number",
        "date": "string - YYYY-MM-DD format",
        "due_date": "string or null - YYYY-MM-DD format",
        "po_number": "string or null - purchase order if present",
        "payment_terms": "string or null - e.g., 'Net 30'"
    },
    "bill_to": {
        "name": "string - customer name",
        "address": "string or null"
    },
    "line_items": [
        {
            "description": "string",
            "quantity": number,
            "unit_price": number,
            "amount": number
        }
    ],
    "totals": {
        "subtotal": number,
        "tax_rate": "string or null - e.g., '19%'",
        "tax_amount": number,
        "total": number,
        "currency": "string - 3-letter code like USD, EUR, GBP"
    },
    "metadata": {
        "language": "string - detected document language",
        "confidence": "HIGH" or "MEDIUM" or "LOW",
        "notes": "string or null - any special observations"
    }
}

IMPORTANT:
- Extract ALL visible information
- Use null for fields not found in the document
- Numbers should be actual numbers, not strings
- Dates should be in YYYY-MM-DD format
- Currency should be 3-letter ISO code

Return ONLY the JSON object, no additional text or markdown formatting."""

    # Build the chat request with multimodal content
    chat_request = oci.generative_ai_inference.models.GenericChatRequest(
        api_format="GENERIC",
        messages=[
            oci.generative_ai_inference.models.UserMessage(
                content=[
                    oci.generative_ai_inference.models.TextContent(
                        type="TEXT",
                        text=extraction_prompt
                    ),
                    # Document as inline data
                    oci.generative_ai_inference.models.ImageContent(
                        type="IMAGE",
                        image_url=oci.generative_ai_inference.models.ImageUrl(
                            url=f"data:{mime_type};base64,{document_base64}"
                        )
                    )
                ]
            )
        ],
        max_tokens=4096,
        temperature=0.1,  # Low temperature for deterministic extraction
        top_p=0.95
    )

    chat_details = oci.generative_ai_inference.models.ChatDetails(
        compartment_id=COMPARTMENT_OCID,
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=MODEL_ID
        ),
        chat_request=chat_request
    )

    # Make the inference call
    logger.info(f"Calling Gemini 2.5 Flash for invoice extraction")
    chat_response = genai_client.chat(chat_details)

    # Extract text from response
    response_text = chat_response.data.chat_response.choices[0].message.content[0].text

    # Parse JSON from response
    try:
        # Try direct parse
        invoice_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if json_match:
            invoice_data = json.loads(json_match.group(1))
        else:
            raise ValueError(f"Could not parse response as JSON: {response_text[:200]}")

    return invoice_data


def handler(ctx, data: io.BytesIO = None):
    """
    Main function handler for invoice extraction.

    Simple flow: PDF → Gemini 2.5 Flash → JSON

    Expects event payload with:
    - namespace: Object Storage namespace
    - bucket: Upload bucket name
    - object_name: PDF/image file name
    - invoice_id: Unique invoice identifier
    """
    try:
        body = json.loads(data.getvalue())

        namespace = body["namespace"]
        bucket = body["bucket"]
        object_name = body["object_name"]
        invoice_id = body["invoice_id"]

        logger.info(f"Processing invoice: {invoice_id} ({object_name})")

        # Step 1: Get document as base64
        document_base64, mime_type = get_document_base64(namespace, bucket, object_name)
        logger.info(f"Document loaded: {mime_type}")

        # Step 2: Extract with Gemini 2.5 Flash (single call, like Claude)
        invoice_data = extract_invoice_with_gemini(document_base64, mime_type)
        logger.info(f"Extraction complete: confidence={invoice_data.get('metadata', {}).get('confidence', 'N/A')}")

        # Build result
        result = {
            "invoice_id": invoice_id,
            "status": "EXTRACTED",
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "extraction_model": MODEL_ID,
            "invoice_data": invoice_data
        }

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
                "status": "FAILED",
                "invoice_id": body.get("invoice_id", "unknown") if body else "unknown"
            }),
            headers={"Content-Type": "application/json"},
            status_code=500
        )
