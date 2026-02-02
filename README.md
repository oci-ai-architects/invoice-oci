# Invoice-OCI

> **Intelligent Invoice Processing on Oracle Cloud Infrastructure**

[![Deploy to OCI](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oci-ai-architects/invoice-oci/releases/latest/download/invoice-oci-stack.zip)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OCI GenAI](https://img.shields.io/badge/OCI-Gemini%202.5%20Flash-C74634)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)

## Overview

Simple OCI port of [invoice-vNext](https://github.com/gruntemannen/invoice-vNext). Same architecture, different cloud.

```
PDF → OCI GenAI (Gemini 2.5 Flash) → JSON → Oracle Fusion AP
```

## Pricing (from [Oracle Price List](https://www.oracle.com/cloud/price-list/))

| Model | Input | Output | Per Invoice* |
|-------|-------|--------|--------------|
| **OCI Gemini 2.5 Flash** | $0.075/1M tokens | $0.30/1M tokens | **~$0.0003** |
| AWS Claude 3.5 Sonnet | $3.00/1M tokens | $15.00/1M tokens | ~$0.012 |

**OCI is ~40x cheaper on input tokens**

*Estimate: ~2,000 input tokens, ~500 output tokens per invoice

### Monthly Cost Estimate

| Volume | AI Cost | Infrastructure | Total |
|--------|---------|----------------|-------|
| 1,000 invoices | $0.30 | ~$25 | **~$25** |
| 10,000 invoices | $3.00 | ~$35 | **~$38** |
| 100,000 invoices | $30.00 | ~$75 | **~$105** |

> Verify current pricing: [oracle.com/cloud/price-list](https://www.oracle.com/cloud/price-list/)

## Quick Start

### Option 1: Deploy to OCI (One-Click)

Click the **Deploy to OCI** button above, then:
1. Select your compartment
2. Configure variables
3. Apply the stack

### Option 2: Manual Deployment

```bash
# Clone
git clone https://github.com/oci-ai-architects/invoice-oci.git
cd invoice-oci

# Configure
cd infrastructure/terraform
cp example.tfvars dev.tfvars
# Edit dev.tfvars with your OCIDs

# Deploy
terraform init && terraform apply -var-file="dev.tfvars"

# Deploy functions
cd ../../functions
fn deploy --app invoice-oci-dev-app --all
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Invoice-OCI                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────┐    ┌─────────────────┐    ┌────────────────┐    │
│  │ Upload │───▶│  OCI GenAI      │───▶│  JSON Result   │    │
│  │ (PDF)  │    │  Gemini 2.5     │    │  (Fusion-ready)│    │
│  └────────┘    │  Flash          │    └────────────────┘    │
│      │         └─────────────────┘            │              │
│      ▼                                        ▼              │
│  ┌────────┐                          ┌────────────────┐     │
│  │ Object │                          │ Oracle Fusion  │     │
│  │Storage │                          │ AP Interface   │     │
│  └────────┘                          └────────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## API Usage

```bash
# Upload invoice
curl -X POST https://<api-gateway>/v1/invoices/upload \
  -F "file=@invoice.pdf"

# Get result
curl https://<api-gateway>/v1/invoices/{id}

# Transform to Fusion format
curl -X POST https://<api-gateway>/v1/invoices/{id}/transform
```

## Why Gemini 2.5 Flash?

| Feature | Gemini 2.5 Flash |
|---------|------------------|
| Multimodal | ✅ Documents, images, audio, video |
| Context | 1M tokens |
| Speed | Fast (optimized for throughput) |
| Cost | $0.075/1M input (40x cheaper than Claude) |

[OCI Gemini 2.5 Flash Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/google-gemini-2-5-flash.htm)

## Alternative: Oracle's Official Solution

For enterprises using Oracle Integration Cloud:

**[oracle-devrel/technology-engineering/ai-email-invoice](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/ai-document-understanding/ai-email-invoice)**

Uses OCI Document Understanding + OIC instead of GenAI, but can be extended with GenAI and provides pre-build connectors to Fusion.

## References

- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Oracle Price List](https://www.oracle.com/cloud/price-list/)
- [OCI Cost Estimator](https://www.oracle.com/cloud/costestimator.html)
- [Original invoice-vNext](https://github.com/gruntemannen/invoice-vNext)

## License

MIT

---

<sub>Community project. Not affiliated with Oracle Corporation.</sub>
