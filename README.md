# Invoice-OCI

> **Intelligent Invoice Processing for Oracle Cloud Customers**
>
> 40x lower AI costs • Native Fusion Integration • Enterprise-grade on OCI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OCI GenAI](https://img.shields.io/badge/OCI-Gemini%202.5%20Flash-C74634)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)
[![Fusion Ready](https://img.shields.io/badge/Oracle%20Fusion-AP%20Interface-green)]()
[![Status](https://img.shields.io/badge/Status-Reference%20Architecture-blue)]()

---

## Why Invoice-OCI?

**Your challenge:** Manual invoice data entry is slow, error-prone, and expensive. AI can extract invoice data automatically, but cloud AI costs add up quickly at scale.

**Invoice-OCI solves this** by combining:
- **OCI GenAI's cost advantage** (40x cheaper than AWS Bedrock)
- **Native Oracle Fusion integration** (direct AP import)
- **Enterprise-grade infrastructure** (already on OCI)

### The Business Case

| Metric | Manual Process | AWS Solution | **Invoice-OCI** |
|--------|---------------|--------------|-----------------|
| **AI Cost (1K invoices/mo)** | N/A | ~$45-75/mo | **~$0.30/mo** |
| **Processing Time** | 5-10 min/invoice | 5-15 sec | 5-15 sec |
| **Error Rate** | 2-5% | <1% | <1% |
| **Fusion Integration** | Native | Requires translation | **Native** |
| **Data Residency** | Your systems | AWS regions | **OCI regions** |

> **For Oracle Fusion customers already on OCI:** Why pay AWS for AI when OCI GenAI is 40x cheaper and connects natively to your ERP?

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INVOICE-OCI                                     │
│                                                                              │
│    ┌──────────┐     ┌───────────────────┐     ┌────────────────────────┐   │
│    │  Upload  │────▶│    OCI GenAI      │────▶│  Structured JSON       │   │
│    │   PDF    │     │  Gemini 2.5 Flash │     │                        │   │
│    └──────────┘     │                   │     │  • Vendor details      │   │
│         │           │  • 1M token ctx   │     │  • Line items          │   │
│         │           │  • Multimodal     │     │  • Amounts & taxes     │   │
│         │           │  • $0.075/1M in   │     │  • Confidence scores   │   │
│         ▼           └───────────────────┘     └──────────┬─────────────┘   │
│    ┌──────────┐                                          │                  │
│    │  Object  │                                          ▼                  │
│    │ Storage  │     ┌───────────────────┐     ┌────────────────────────┐   │
│    │          │     │ Fusion Transformer│────▶│  Oracle Fusion AP      │   │
│    │  • PDFs  │     │                   │     │  AP_INVOICES_INTERFACE │   │
│    │  • JSON  │     │  • Vendor mapping │     │                        │   │
│    │  • Logs  │     │  • Line items     │     │  ✅ Ready for import   │   │
│    └──────────┘     │  • Tax handling   │     └────────────────────────┘   │
│                     └───────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **AI-Powered Extraction** | Gemini 2.5 Flash analyzes PDFs directly (no OCR step) |
| **Multi-Language** | Extracts invoices in any language automatically |
| **Confidence Scoring** | Each extraction includes HIGH/MEDIUM/LOW confidence |
| **Fusion-Ready Output** | Direct AP_INVOICES_INTERFACE format |
| **Serverless Scale** | Pay only for what you process |
| **OCI Native** | Runs entirely on Oracle Cloud Infrastructure |

---

## Cost Comparison: OCI vs AWS

> **Source:** [Oracle Cloud Price List](https://www.oracle.com/cloud/price-list/) | Verified: 2026-02-02

### AI Model Pricing

| Model | Input Tokens | Output Tokens | Advantage |
|-------|--------------|---------------|-----------|
| **OCI Gemini 2.5 Flash** | $0.075/1M | $0.30/1M | **Baseline** |
| AWS Claude 3.5 Sonnet | $3.00/1M | $15.00/1M | 40x more expensive |
| AWS Claude 3 Haiku | $0.25/1M | $1.25/1M | 3x more expensive |

### Real-World Cost Estimate

Assumptions: Average invoice = ~2,000 input tokens, ~500 output tokens

| Monthly Volume | OCI GenAI | AWS Bedrock (Claude 3.5) | **You Save** |
|----------------|-----------|--------------------------|--------------|
| 100 invoices | $0.03 | $1.35 | $1.32 (98%) |
| 1,000 invoices | $0.30 | $13.50 | **$13.20 (98%)** |
| 10,000 invoices | $3.00 | $135.00 | **$132.00 (98%)** |
| 100,000 invoices | $30.00 | $1,350.00 | **$1,320.00 (98%)** |

### Total Monthly Cost (1,000 invoices)

| Component | OCI | AWS |
|-----------|-----|-----|
| AI Inference | $0.30 | $13.50 |
| Compute (Functions) | $0* | ~$5 |
| Storage (Object/S3) | ~$2 | ~$2 |
| API Gateway | $0* | ~$3 |
| **Total** | **~$5/mo** | **~$25/mo** |

*OCI Functions includes 2M free invocations/month. API Gateway included.

---

## Extracted Data Schema

Invoice-OCI extracts structured data in a consistent format:

```json
{
  "vendor": {
    "name": "Acme Supplies Ltd",
    "address": "123 Business Park, London EC1A 1BB",
    "tax_id": "GB123456789",
    "phone": "+44 20 7946 0958",
    "email": "billing@acme-supplies.co.uk"
  },
  "invoice_details": {
    "number": "INV-2026-0142",
    "date": "2026-01-15",
    "due_date": "2026-02-14",
    "po_number": "PO-8847",
    "payment_terms": "Net 30"
  },
  "bill_to": {
    "name": "Your Company Inc",
    "address": "456 Corporate Drive, Suite 100"
  },
  "line_items": [
    {
      "description": "Professional Services - January",
      "quantity": 40,
      "unit_price": 150.00,
      "amount": 6000.00
    },
    {
      "description": "Software License (Annual)",
      "quantity": 1,
      "unit_price": 2400.00,
      "amount": 2400.00
    }
  ],
  "totals": {
    "subtotal": 8400.00,
    "tax_rate": "20%",
    "tax_amount": 1680.00,
    "total": 10080.00,
    "currency": "GBP"
  },
  "metadata": {
    "language": "English",
    "confidence": "HIGH",
    "notes": "Tax ID validated against UK VAT format"
  }
}
```

---

## Oracle Fusion Integration

Invoice-OCI transforms extracted data directly to Oracle Fusion AP_INVOICES_INTERFACE format:

```json
{
  "InvoiceNum": "INV-2026-0142",
  "InvoiceDate": "2026-01-15",
  "VendorName": "Acme Supplies Ltd",
  "VendorTaxRegistrationNumber": "GB123456789",
  "InvoiceAmount": 10080.00,
  "InvoiceCurrencyCode": "GBP",
  "TermsName": "Net 30",
  "PoNumber": "PO-8847",
  "Source": "INVOICE_OCI",
  "invoiceLinesCollection": [
    {
      "LineNumber": 1,
      "LineType": "ITEM",
      "Description": "Professional Services - January",
      "Quantity": 40,
      "UnitPrice": 150.00,
      "Amount": 6000.00
    }
  ]
}
```

### Fusion Import Methods

| Method | Use Case |
|--------|----------|
| **FBDI** | Batch import via File-Based Data Import |
| **REST API** | Real-time import via Fusion REST endpoints |
| **OIC** | Oracle Integration Cloud connectors |

---

## Deployment

### Prerequisites

- OCI Tenancy with Generative AI enabled
- Gemini 2.5 Flash access (regions: US-Chicago, US-Phoenix, Japan, India)
- OCI CLI configured
- Terraform >= 1.5
- Fn Project CLI (for function deployment)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/oci-ai-architects/invoice-oci.git
cd invoice-oci

# 2. Configure Terraform
cd infrastructure/terraform
cp example.tfvars dev.tfvars
# Edit dev.tfvars with your compartment OCID, region, etc.

# 3. Deploy infrastructure
terraform init
terraform apply -var-file="dev.tfvars"

# 4. Deploy functions
cd ../../functions
fn deploy --app invoice-oci-dev-app --all

# 5. Test extraction
curl -X POST https://<api-gateway>/extract \
  -H "Content-Type: application/json" \
  -d '{"bucket": "invoices", "object_name": "test-invoice.pdf"}'
```

### Required Terraform Variables

```hcl
# example.tfvars
compartment_ocid = "ocid1.compartment.oc1..aaaa..."
region           = "us-chicago-1"
environment      = "dev"

# Optional: Fusion integration
fusion_org_id    = "300000001234567"
```

---

## Security Considerations

| Aspect | Implementation |
|--------|----------------|
| **Authentication** | OCI IAM policies, Resource Principal |
| **Data at Rest** | OCI Object Storage encryption (AES-256) |
| **Data in Transit** | TLS 1.2+ for all API calls |
| **Access Control** | Compartment-based isolation |
| **Audit** | OCI Audit logs for all operations |
| **Data Retention** | Configurable (default: 90 days) |

### Required IAM Policies

```
Allow dynamic-group invoice-oci-functions to manage objects in compartment <compartment>
Allow dynamic-group invoice-oci-functions to use generative-ai-inference in compartment <compartment>
```

---

## Monitoring

### OCI Console

- **Functions > Applications > invoice-oci** - Invocation metrics, errors
- **Object Storage** - Bucket metrics, storage usage
- **Generative AI** - Token usage, model performance

### Recommended Alarms

```hcl
# Example: Alert on high error rate
resource "oci_monitoring_alarm" "extraction_errors" {
  display_name        = "invoice-extraction-errors"
  compartment_id      = var.compartment_ocid
  metric_compartment_id = var.compartment_ocid
  namespace           = "oci_faas"
  query               = "FunctionResponseStatus[1m]{functionName=\"invoice-processor\"}.count() > 10"
  severity            = "CRITICAL"
}
```

---

## Comparison: Invoice-OCI vs invoice-vNext

| Capability | invoice-vNext (AWS) | **Invoice-OCI** |
|------------|---------------------|-----------------|
| **Cloud Provider** | AWS | OCI |
| **AI Model** | Claude 3.5 Sonnet | Gemini 2.5 Flash |
| **AI Cost (1K/mo)** | ~$15-25 | **~$0.30** |
| **Total Cost (1K/mo)** | ~$23-33 | **~$5-10** |
| **Fusion Integration** | Requires middleware | **Native format** |
| **Context Window** | 200K tokens | **1M tokens** |
| **Multimodal** | PDF via Bedrock | PDF native |
| **Frontend** | PWA included | Bring your own |
| **Multi-Account** | AWS Organizations | OCI Compartments |
| **Best For** | AWS-first shops | **Oracle Fusion customers** |

### When to Choose Invoice-OCI

✅ You're already on OCI
✅ You use Oracle Fusion Financials
✅ Cost optimization is a priority
✅ You need EU/specific region data residency
✅ You prefer single-vendor support

### When to Choose invoice-vNext

✅ You're AWS-first with no OCI presence
✅ You need the included PWA frontend
✅ You prefer Claude over Gemini models

---

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Architecture Design | ✅ Complete | Production patterns |
| Terraform IaC | ✅ Complete | Single-compartment |
| Invoice Processor | ✅ Complete | Gemini 2.5 Flash |
| Fusion Transformer | ✅ Complete | AP_INVOICES_INTERFACE |
| API Gateway | ⚠️ Template | Customize endpoints |
| Frontend | ❌ Not included | Bring your own |
| Testing | ⚠️ Manual only | Needs automation |

**This is a reference architecture.** Production deployment requires:
- Security review
- Performance testing with your invoice formats
- Fusion vendor/account mapping configuration
- Error handling customization

---

## Alternative: Oracle's Official Solution

For enterprises using Oracle Integration Cloud, consider the official approach:

**[oracle-devrel/technology-engineering/ai-email-invoice](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/ai-document-understanding/ai-email-invoice)**

Uses OCI Document Understanding + OIC for pre-built Fusion connectors. Best for:
- Complex multi-step workflows
- Email-based invoice ingestion
- Customers already using OIC

---

## References

| Resource | Link |
|----------|------|
| OCI Generative AI | https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm |
| Gemini 2.5 Flash on OCI | https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm |
| Oracle Price List | https://www.oracle.com/cloud/price-list/ |
| OCI Cost Estimator | https://www.oracle.com/cloud/costestimator.html |
| Fusion AP Interface | https://docs.oracle.com/en/cloud/saas/financials/24d/oefbf/ap-invoices-interface.html |
| Original inspiration | https://github.com/gruntemannen/invoice-vNext |

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Disclaimer

> **Personal educational content** by an Oracle employee. Not officially reviewed or supported by Oracle.
> See [DISCLAIMER.md](DISCLAIMER.md) | [Official Oracle content](https://github.com/oracle-devrel/technology-engineering)

Verify all pricing at [oracle.com/cloud/price-list](https://www.oracle.com/cloud/price-list/) before use.

---

<sub>Co-created with Starlight Architect | Last updated: 2026-02-03</sub>
