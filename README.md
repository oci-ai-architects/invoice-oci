# Invoice-OCI

> **Simple Invoice Processing on Oracle Cloud Infrastructure**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OCI GenAI](https://img.shields.io/badge/OCI-Gemini%202.5%20Flash-orange)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)

**DISCLAIMER:** Unofficial community project. Not affiliated with Oracle Corporation.

## Overview

Direct OCI port of [gruntemannen/invoice-vNext](https://github.com/gruntemannen/invoice-vNext). Same simple architecture, different cloud.

```
Original (AWS):              This Version (OCI):
PDF → Claude 3.5 Sonnet      PDF → Gemini 2.5 Flash
         ↓                            ↓
       JSON                         JSON
```

**Why Gemini 2.5 Flash?** It's OCI's closest equivalent to Claude - multimodal (documents, images, audio, video), fast, cost-effective.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Invoice-OCI (Simple)                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │  Upload  │───▶│ OCI GenAI   │───▶│  JSON Result     │  │
│  │  (PDF)   │    │ Gemini 2.5  │    │  (Fusion-ready)  │  │
│  │          │    │   Flash     │    │                  │  │
│  └──────────┘    └─────────────┘    └──────────────────┘  │
│       │                                      │             │
│       ▼                                      ▼             │
│  ┌──────────┐                        ┌──────────────────┐  │
│  │  Object  │                        │   NoSQL / AJD    │  │
│  │  Storage │                        │   (metadata)     │  │
│  └──────────┘                        └──────────────────┘  │
│                                              │             │
│                                              ▼             │
│                                      ┌──────────────────┐  │
│                                      │  Oracle Fusion   │  │
│                                      │  AP Interface    │  │
│                                      └──────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**That's it.** One AI call. No hybrid complexity. Just like the original.

## Cost Comparison

| Service | Input (1M tokens) | Output (1M tokens) | Source |
|---------|-------------------|--------------------| -------|
| AWS Bedrock Claude 3.5 Sonnet | $3.00 | $15.00 | [AWS](https://aws.amazon.com/bedrock/pricing/) |
| OCI GenAI Gemini 2.5 Flash | ~$0.30 | ~$2.50 | [Google](https://ai.google.dev/gemini-api/docs/pricing)* |

*OCI pricing may include markup - verify at [oracle.com/cloud/price-list](https://www.oracle.com/cloud/price-list/)

**Potential savings: ~10x on input, ~6x on output**

## Quick Start

### Prerequisites

- OCI Tenancy with Generative AI enabled
- Gemini 2.5 Flash access (available in US Midwest, US West, Japan, India)
- OCI CLI configured

### Deploy

```bash
# 1. Infrastructure
cd infrastructure/terraform
cp example.tfvars dev.tfvars
# Edit dev.tfvars with your OCIDs
terraform init && terraform apply -var-file="dev.tfvars"

# 2. Functions
cd functions
fn deploy --app invoice-oci-dev-app --all
```

### Test

```bash
# Upload invoice
oci os object put -bn invoice-oci-dev-invoices-upload -f sample.pdf

# Trigger extraction (via API Gateway or direct function invoke)
fn invoke invoice-oci-dev-app invoice-processor < payload.json
```

## Project Structure

```
invoice-oci/
├── functions/
│   ├── invoice-processor/    # Main extraction (Gemini 2.5 Flash)
│   └── fusion-transformer/   # Fusion AP format converter
├── infrastructure/
│   └── terraform/            # OCI IaC
└── docs/
```

## Alternative: Oracle's Official Solution

Oracle has an official invoice processing pattern using OCI Document Understanding + OIC:

**[oracle-devrel/technology-engineering/ai/ai-document-understanding/ai-email-invoice](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/ai-document-understanding/ai-email-invoice)**

Consider this if:
- You're already using Oracle Integration Cloud (OIC)
- You want traditional ML instead of LLM
- You need Oracle-supported solution

## References

- [Original invoice-vNext](https://github.com/gruntemannen/invoice-vNext) - AWS/Claude version
- [OCI Gemini 2.5 Flash Docs](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)
- [Oracle Price List](https://www.oracle.com/cloud/price-list/) - Verify current pricing
- [Oracle's Official Invoice Solution](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/ai-document-understanding/ai-email-invoice)

## License

MIT - See [LICENSE](LICENSE)

---

*Part of [oci-ai-architects](https://github.com/oci-ai-architects) community*
