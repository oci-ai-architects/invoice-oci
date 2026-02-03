# Invoice-OCI

> **Invoice Extraction on Oracle Cloud Infrastructure**
>
> An OCI-native adaptation of [invoice-vNext](https://github.com/gruntemannen/invoice-vNext) for Oracle Fusion customers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OCI GenAI](https://img.shields.io/badge/OCI-Generative%20AI-C74634)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
[![Fusion Ready](https://img.shields.io/badge/Oracle%20Fusion-AP%20Interface-green)]()

---

## About

Invoice-OCI brings the invoice extraction pattern from [gruntemannen/invoice-vNext](https://github.com/gruntemannen/invoice-vNext) to Oracle Cloud Infrastructure, using OCI Generative AI and native Oracle Fusion AP integration.

**For customers already on Oracle Cloud:** This reference architecture shows how to implement AI-powered invoice extraction without leaving your existing cloud environment.

---

## Architecture

```
PDF Upload → OCI Object Storage → OCI GenAI (Gemini 2.5) → JSON → Oracle Fusion AP
```

| Component | Technology |
|-----------|------------|
| Storage | OCI Object Storage |
| AI Extraction | OCI Generative AI (Gemini 2.5 Flash) |
| Compute | OCI Functions (serverless) |
| Output Format | Oracle Fusion AP_INVOICES_INTERFACE |
| Infrastructure | Terraform |

---

## Key Features

- **AI-Powered Extraction** - Gemini 2.5 Flash analyzes PDFs directly (multimodal, no OCR step)
- **Multi-Language Support** - Extracts invoices in any language
- **Confidence Scoring** - Each extraction includes HIGH/MEDIUM/LOW confidence
- **Fusion-Ready Output** - Direct AP_INVOICES_INTERFACE format for Oracle Fusion Payables
- **Serverless** - Pay only for what you process
- **OCI Native** - Runs entirely on Oracle Cloud Infrastructure

---

## OCI GenAI Pricing

> **Source:** [Oracle Cloud Price List](https://www.oracle.com/cloud/price-list/) | Verified: 2026-02-03

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Gemini 2.5 Flash | $0.075 | $0.30 |
| Gemini 2.5 Flash-Lite | $0.0375 | $0.15 |
| Gemini 2.5 Pro | $0.075-0.30* | $0.30-1.20* |

*Pro pricing varies by context length. See [price list](https://www.oracle.com/cloud/price-list/) for details.

---

## Extracted Data Format

```json
{
  "vendor": {
    "name": "Acme Supplies Ltd",
    "address": "123 Business Park, London",
    "tax_id": "GB123456789"
  },
  "invoice_details": {
    "number": "INV-2026-0142",
    "date": "2026-01-15",
    "due_date": "2026-02-14",
    "po_number": "PO-8847"
  },
  "line_items": [...],
  "totals": {
    "subtotal": 8400.00,
    "tax_amount": 1680.00,
    "total": 10080.00,
    "currency": "GBP"
  },
  "metadata": {
    "confidence": "HIGH"
  }
}
```

---

## Oracle Fusion Integration

Output transforms directly to AP_INVOICES_INTERFACE format:

```json
{
  "InvoiceNum": "INV-2026-0142",
  "InvoiceDate": "2026-01-15",
  "VendorName": "Acme Supplies Ltd",
  "InvoiceAmount": 10080.00,
  "InvoiceCurrencyCode": "GBP",
  "Source": "INVOICE_OCI",
  "invoiceLinesCollection": [...]
}
```

Import via FBDI, REST API, or Oracle Integration Cloud.

---

## Deployment

### Prerequisites

- OCI Tenancy with Generative AI enabled
- OCI CLI configured
- Terraform >= 1.5
- Fn Project CLI

### Quick Start

```bash
git clone https://github.com/oci-ai-architects/invoice-oci.git
cd invoice-oci/infrastructure/terraform
cp example.tfvars dev.tfvars
# Edit dev.tfvars with your OCIDs

terraform init && terraform apply -var-file="dev.tfvars"

cd ../../functions
fn deploy --app invoice-oci-app --all
```

---

## Project Status

| Component | Status |
|-----------|--------|
| Architecture | ✅ Designed |
| Terraform | ✅ Written |
| Functions | ✅ Written |
| Testing | ⚠️ Reference only |

**This is a reference architecture.** Production deployment requires security review and testing with your specific invoice formats.

---

## Credits

This project adapts the excellent work from [gruntemannen/invoice-vNext](https://github.com/gruntemannen/invoice-vNext) for Oracle Cloud Infrastructure.

---

## References

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Oracle Cloud Price List](https://www.oracle.com/cloud/price-list/)
- [Fusion AP Interface](https://docs.oracle.com/en/cloud/saas/financials/24d/oefbf/ap-invoices-interface.html)
- [Original: invoice-vNext](https://github.com/gruntemannen/invoice-vNext)

---

## License

MIT - See [LICENSE](LICENSE)

---

> Personal educational content by an Oracle employee. Not officially reviewed or supported by Oracle.
> See [DISCLAIMER.md](DISCLAIMER.md)
