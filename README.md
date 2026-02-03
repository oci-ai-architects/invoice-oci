# Invoice-OCI

> **Intelligent Invoice Processing on Oracle Cloud Infrastructure**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OCI GenAI](https://img.shields.io/badge/OCI-Gemini%202.5%20Flash-C74634)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)
[![Status](https://img.shields.io/badge/Status-Reference%20Architecture-blue)]()

## Overview

OCI-native invoice extraction adapted from [invoice-vNext](https://github.com/gruntemannen/invoice-vNext).

```
PDF → OCI GenAI (Gemini 2.5 Flash) → JSON → Oracle Fusion AP
```


## Pricing

> **Source:** [Oracle Cloud Price List](https://www.oracle.com/cloud/price-list/)
> **Verified:** 2026-02-02

### USD Pricing

| Model | Input | Output |
|-------|-------|--------|
| **OCI Gemini 2.5 Flash** | $0.075/1M tokens | $0.30/1M tokens |
| AWS Claude 3.5 Sonnet | $3.00/1M tokens | $15.00/1M tokens |

**OCI is ~40x cheaper on input tokens**

### EUR Pricing

> EUR requires manual verification via currency selector on [price list](https://www.oracle.com/cloud/price-list/)

| Model | Input (Est.) | Output (Est.) |
|-------|--------------|---------------|
| OCI Gemini 2.5 Flash | ~€0.07/1M tokens | ~€0.28/1M tokens |

### Per-Invoice Cost

| Volume | AI Cost | Est. Total |
|--------|---------|------------|
| 1,000/month | ~$0.30 | ~$25/month |
| 10,000/month | ~$3.00 | ~$40/month |

## Deployment

### Prerequisites

- OCI Tenancy with Generative AI enabled
- Gemini 2.5 Flash access (US-Chicago, US-Phoenix, Frankfurt)
- OCI CLI configured
- Terraform >= 1.5

### Steps

```bash
# Clone
git clone https://github.com/oci-ai-architects/invoice-oci.git
cd invoice-oci

# Configure
cd infrastructure/terraform
cp example.tfvars dev.tfvars
# Edit dev.tfvars with your OCIDs

# Deploy infrastructure
terraform init
terraform apply -var-file="dev.tfvars"

# Deploy functions (requires fn CLI)
cd ../../functions
fn deploy --app invoice-oci-dev-app --all
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Invoice-OCI                            │
├──────────────────────────────────────────────────────────────┤
│  ┌────────┐    ┌─────────────────┐    ┌────────────────┐    │
│  │ Upload │───▶│  OCI GenAI      │───▶│  JSON Result   │    │
│  │ (PDF)  │    │  Gemini 2.5     │    │                │    │
│  └────────┘    │  Flash          │    └────────────────┘    │
│      │         └─────────────────┘            │              │
│      ▼                                        ▼              │
│  Object Storage                      Oracle Fusion AP        │
└──────────────────────────────────────────────────────────────┘
```

## Why Gemini 2.5 Flash?

| Feature | Value |
|---------|-------|
| Multimodal | Documents, images, audio, video |
| Context | 1M tokens |
| Cost | $0.075/1M input (40x cheaper than Claude) |

## Alternative: Oracle's Official Solution

For enterprises using Oracle Integration Cloud:

[oracle-devrel/technology-engineering/ai-email-invoice](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/ai-document-understanding/ai-email-invoice)

Uses OCI Document Understanding + OIC instead of GenAI, but can be extended with GenAI and provides pre-build connectors to Fusion.


## Status

| Component | Status |
|-----------|--------|
| Architecture | ✅ Designed |
| Terraform | ✅ Written |
| Functions | ✅ Written |
| Testing | ⚠️ Not tested on OCI |
| Production | ❌ Not production-ready |

**This is a reference architecture, not production code.**

## References

- [OCI Generative AI Docs](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Gemini 2.5 Flash](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)
- [Oracle Price List](https://www.oracle.com/cloud/price-list/)
- [OCI Cost Estimator](https://www.oracle.com/cloud/costestimator.html)

## License

MIT

---

<sub>Community reference architecture. Not affiliated with Oracle Corporation. Verify all pricing before use.</sub>
