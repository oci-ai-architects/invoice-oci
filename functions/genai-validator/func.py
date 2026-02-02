"""
OCI Generative AI - Invoice Validation Function

This function validates and corrects low-confidence invoice extractions
using OCI GenAI with Llama 3.2 Vision multimodal capabilities.
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
GENAI_ENDPOINT = os.environ.get("GENAI_ENDPOINT", "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com")
MODEL_ID = os.environ.get("GENAI_MODEL_ID", "meta.llama-3.2-90b-vision-instruct")
UPLOAD_BUCKET = os.environ.get("UPLOAD_BUCKET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_signer():
    """Get OCI signer using resource principal (for Functions)."""
    return oci.auth.signers.get_resource_principals_signer()


def get_document_base64(namespace: str, bucket: str, object_name: str) -> str:
    """Download document from Object Storage and encode as base64."""
    signer = get_signer()
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    obj = os_client.get_object(namespace, bucket, object_name)
    return base64.b64encode(obj.data.content).decode('utf-8')


def validate_with_genai(document_base64: str, du_extraction: dict) -> dict:
    """
    Use OCI GenAI Llama 3.2 Vision to validate and correct invoice extraction.

    Args:
        document_base64: Base64-encoded PDF/image
        du_extraction: Previous extraction from Document Understanding

    Returns:
        dict: Validated/corrected invoice data
    """
    signer = get_signer()

    # Initialize GenAI Inference client
    genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config={},
        signer=signer,
        service_endpoint=GENAI_ENDPOINT
    )

    # Construct the validation prompt
    prompt = f"""You are an expert invoice data extraction and validation assistant.

I have extracted the following invoice data using OCR/Document AI, but the confidence
is low on some fields. Please review the attached invoice document and:

1. Verify each extracted field against what you see in the document
2. Correct any errors you find
3. Fill in any missing fields you can identify
4. Return the validated data in the exact JSON schema provided

PREVIOUS EXTRACTION (may contain errors):
```json
{json.dumps(du_extraction, indent=2)}
```

REQUIRED OUTPUT SCHEMA:
{{
    "vendor": {{
        "name": "string",
        "address": "string",
        "tax_id": "string or null"
    }},
    "invoice_details": {{
        "number": "string",
        "date": "YYYY-MM-DD",
        "due_date": "YYYY-MM-DD or null",
        "po_number": "string or null"
    }},
    "line_items": [
        {{
            "description": "string",
            "quantity": number,
            "unit_price": number,
            "amount": number
        }}
    ],
    "totals": {{
        "subtotal": number,
        "tax": number,
        "total": number,
        "currency": "string (3-letter code)"
    }},
    "corrections_made": ["list of fields that were corrected"],
    "confidence": "HIGH" or "MEDIUM" or "LOW"
}}

Return ONLY the JSON object, no additional text."""

    # Create chat request with vision capability
    chat_request = oci.generative_ai_inference.models.GenericChatRequest(
        api_format="GENERIC",
        messages=[
            oci.generative_ai_inference.models.UserMessage(
                content=[
                    oci.generative_ai_inference.models.TextContent(
                        type="TEXT",
                        text=prompt
                    ),
                    oci.generative_ai_inference.models.ImageContent(
                        type="IMAGE",
                        image_url=oci.generative_ai_inference.models.ImageUrl(
                            url=f"data:application/pdf;base64,{document_base64}"
                        )
                    )
                ]
            )
        ],
        max_tokens=4096,
        temperature=0.1,  # Low temperature for deterministic extraction
        top_p=0.9
    )

    chat_details = oci.generative_ai_inference.models.ChatDetails(
        compartment_id=os.environ.get("COMPARTMENT_OCID"),
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=MODEL_ID
        ),
        chat_request=chat_request
    )

    # Make the inference call
    chat_response = genai_client.chat(chat_details)

    # Parse the response
    response_text = chat_response.data.chat_response.choices[0].message.content[0].text

    # Extract JSON from response
    try:
        # Try to parse directly
        validated_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if json_match:
            validated_data = json.loads(json_match.group(1))
        else:
            raise ValueError("Could not parse GenAI response as JSON")

    return validated_data


def merge_results(du_extraction: dict, genai_validation: dict) -> dict:
    """
    Merge Document Understanding results with GenAI validation.

    Prioritizes GenAI corrections while maintaining audit trail.
    """
    merged = {
        "extraction_timestamp": datetime.utcnow().isoformat(),
        "extraction_method": "HYBRID_DU_GENAI",
        "vendor": genai_validation.get("vendor", du_extraction.get("vendor", {})),
        "invoice_details": genai_validation.get("invoice_details", du_extraction.get("invoice_details", {})),
        "line_items": genai_validation.get("line_items", du_extraction.get("line_items", [])),
        "totals": genai_validation.get("totals", du_extraction.get("totals", {})),
        "validation": {
            "genai_used": True,
            "corrections_made": genai_validation.get("corrections_made", []),
            "genai_confidence": genai_validation.get("confidence", "MEDIUM"),
            "original_du_confidence": du_extraction.get("overall_confidence", 0)
        }
    }

    return merged


def handler(ctx, data: io.BytesIO = None):
    """
    Main function handler for GenAI invoice validation.

    Expects event payload with:
    - namespace: Object Storage namespace
    - bucket: Upload bucket name
    - object_name: PDF file name
    - invoice_id: Unique invoice identifier
    - du_extraction: Previous Document Understanding results
    """
    try:
        body = json.loads(data.getvalue())

        namespace = body["namespace"]
        bucket = body["bucket"]
        object_name = body["object_name"]
        invoice_id = body["invoice_id"]
        du_extraction = body["du_extraction"]

        logger.info(f"GenAI validation for invoice: {invoice_id}")

        # Step 1: Get document as base64
        document_base64 = get_document_base64(namespace, bucket, object_name)

        # Step 2: Validate with GenAI
        genai_validation = validate_with_genai(
            document_base64,
            du_extraction.get("invoice_data", {})
        )

        # Step 3: Merge results
        merged_result = merge_results(
            du_extraction.get("invoice_data", {}),
            genai_validation
        )

        # Step 4: Calculate final confidence
        corrections_count = len(genai_validation.get("corrections_made", []))
        genai_confidence = genai_validation.get("confidence", "MEDIUM")

        if genai_confidence == "HIGH" and corrections_count <= 2:
            final_confidence = 0.95
        elif genai_confidence == "MEDIUM" or corrections_count <= 5:
            final_confidence = 0.85
        else:
            final_confidence = 0.70

        result = {
            "invoice_id": invoice_id,
            "status": "VALIDATED",
            "final_confidence": final_confidence,
            "genai_corrections": corrections_count,
            "invoice_data": merged_result
        }

        logger.info(f"Validation complete: {corrections_count} corrections, confidence {final_confidence:.2%}")

        return response.Response(
            ctx,
            response_data=json.dumps(result),
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"Error in GenAI validation: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "error": str(e),
                "status": "VALIDATION_FAILED",
                "invoice_id": body.get("invoice_id", "unknown")
            }),
            headers={"Content-Type": "application/json"},
            status_code=500
        )
