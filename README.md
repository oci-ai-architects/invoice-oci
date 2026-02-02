# Invoice-OCI

> **Intelligent Invoice Processing on Oracle Cloud Infrastructure**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OCI](https://img.shields.io/badge/OCI-Document%20AI-red)](https://docs.oracle.com/en-us/iaas/Content/document-understanding/home.htm)
[![OCI GenAI](https://img.shields.io/badge/OCI-Generative%20AI-orange)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

**DISCLAIMER:** This is an unofficial community project. Not affiliated with, endorsed by, or sponsored by Oracle Corporation. Oracle, OCI, and related marks are trademarks of Oracle Corporation.

## Overview

Enterprise-grade invoice extraction system built on Oracle Cloud Infrastructure, featuring a hybrid AI approach combining **OCI Document Understanding** for fast, deterministic extraction with **OCI Generative AI (Llama 3.2 Vision)** for complex edge cases.

Adapted from [gruntemannen/invoice-vNext](https://github.com/gruntemannen/invoice-vNext) (AWS/Bedrock) for OCI-native deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Invoice-OCI Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌─────────────┐    ┌────────────────────────┐  │
│  │  Web UI  │───▶│ API Gateway │───▶│    OCI Functions       │  │
│  │  (PWA)   │    │             │    │    (Orchestrator)      │  │
│  └──────────┘    └─────────────┘    └───────────┬────────────┘  │
│       │                                         │                │
│       ▼                                         ▼                │
│  ┌──────────┐              ┌─────────────────────────────────┐  │
│  │  Object  │─────────────▶│      Hybrid AI Pipeline         │  │
│  │ Storage  │              │  ┌─────────────────────────────┐│  │
│  └──────────┘              │  │ OCI Document Understanding  ││  │
│                            │  │ (Primary - 90% of docs)     ││  │
│                            │  └──────────────┬──────────────┘│  │
│                            │                 │ confidence    │  │
│                            │                 │  < 85%        │  │
│                            │                 ▼               │  │
│                            │  ┌─────────────────────────────┐│  │
│                            │  │ OCI GenAI Llama 3.2 Vision  ││  │
│                            │  │ (Fallback - 10% edge cases) ││  │
│                            │  └─────────────────────────────┘│  │
│                            └─────────────────────────────────┘  │
│                                         │                        │
│                                         ▼                        │
│                            ┌──────────────────────┐             │
│                            │   OCI NoSQL / AJD    │             │
│                            └──────────────────────┘             │
│                                         │                        │
│                                         ▼                        │
│                            ┌──────────────────────┐             │
│                            │  Oracle Fusion AP    │             │
│                            │  (Native REST API)   │             │
│                            └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Hybrid AI Extraction**: OCI Document Understanding + GenAI Llama 3.2 Vision
- **Serverless Architecture**: OCI Functions for cost-efficient scaling
- **Oracle Fusion Ready**: Native AP_INVOICES_INTERFACE format output
- **Multi-Language Support**: 15+ languages including CJK
- **Confidence Scoring**: Automatic quality assessment per field
- **Progressive Web App**: Installable offline-capable frontend

## Technology Stack

| Component | OCI Service |
|-----------|-------------|
| Compute | OCI Functions |
| Document AI | OCI Document Understanding |
| Generative AI | OCI GenAI (Llama 3.2 Vision) |
| Storage | OCI Object Storage |
| Database | OCI NoSQL Database |
| API | OCI API Gateway |
| Queuing | OCI Queue |
| IaC | OCI Resource Manager (Terraform) |

## Cost Estimate

| Volume | Monthly Cost | Per-Invoice |
|--------|-------------|-------------|
| 1,000 | ~$30-50 | $0.03-0.05 |
| 10,000 | ~$200-350 | $0.02-0.035 |
| 100,000 | ~$1,500-2,500 | $0.015-0.025 |

## Quick Start

### Prerequisites

- OCI Tenancy with Document Understanding and Generative AI enabled
- OCI CLI configured
- Terraform >= 1.5.0
- Node.js >= 18 (for functions)

### Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="dev.tfvars"
terraform apply -var-file="dev.tfvars"
```

### Deploy Functions

```bash
cd functions
fn deploy --app invoice-oci-dev-app --all
```

## Project Structure

```
invoice-oci/
├── infrastructure/
│   └── terraform/           # OCI Resource Manager templates
├── functions/
│   ├── upload-handler/      # File upload orchestration
│   ├── document-processor/  # OCI Document Understanding
│   ├── genai-validator/     # OCI GenAI fallback
│   └── fusion-transformer/  # Fusion AP format converter
├── frontend/
│   └── pwa/                 # Progressive Web App
├── docs/
│   ├── ARCHITECTURE.md
│   ├── OCI-SETUP.md
│   └── FUSION-INTEGRATION.md
└── examples/
    └── sample-invoices/
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [OCI Setup Guide](docs/OCI-SETUP.md)
- [Fusion Integration](docs/FUSION-INTEGRATION.md)
- [Technology Decision](OCI-TECHNOLOGY-DECISION.md)

## Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## License

MIT License - See [LICENSE](LICENSE) for details.

## References

- [OCI Document Understanding](https://docs.oracle.com/en-us/iaas/Content/document-understanding/home.htm)
- [OCI Generative AI Service](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Original invoice-vNext](https://github.com/gruntemannen/invoice-vNext)

---

*Part of the [oci-ai-architects](https://github.com/oci-ai-architects) community*
