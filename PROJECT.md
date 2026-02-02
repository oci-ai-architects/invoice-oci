# Invoice-OCI: Intelligent Invoice Processing on Oracle Cloud

> **Reference:** Adaptation of [gruntemannen/invoice-vNext](https://github.com/gruntemannen/invoice-vNext) for Oracle Cloud Infrastructure

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Codename** | Invoice-OCI |
| **Status** | Architecture Phase |
| **Industry** | Cross-Industry (Finance/AP) |
| **Goal** | Enterprise-grade invoice extraction with native OCI + Fusion integration |

## Technology Decision: Document Understanding vs LLMs

### Option Analysis

| Approach | OCI Service | Pros | Cons | Cost Model |
|----------|-------------|------|------|------------|
| **A: OCI Document Understanding** | Document Understanding | Purpose-built for invoices, pre-trained models, fast, deterministic | Less flexible for edge cases | Per-page pricing |
| **B: OCI GenAI (Multimodal)** | Generative AI Service | Flexible, handles complex layouts, multi-language | Higher cost, latency | Per-token pricing |
| **C: Hybrid (Recommended)** | Both | Best of both worlds | More complex | Combined |

### Recommendation: Option C - Hybrid Architecture

```
PDF → OCI Document Understanding (structured extraction)
         ↓
    Confidence < 85%?
         ↓ YES
    OCI GenAI (validation/correction)
         ↓
    Final JSON → Fusion AP Interface
```

**Why Hybrid?**
1. **OCI Document Understanding** excels at standard invoice layouts (90%+ of invoices)
2. **OCI GenAI** handles edge cases, multi-language validation, and reasoning
3. **Cost-optimized**: Only invoke LLM when needed (~10-15% of documents)

## OCI Services Mapping

### AWS → OCI Migration Map

| AWS Service | OCI Equivalent | Notes |
|-------------|---------------|-------|
| AWS Lambda | **OCI Functions** | Python/Node.js, event-driven |
| Amazon Bedrock (Claude) | **OCI Generative AI Service** | Cohere Command R+, Meta Llama 3.1 |
| - | **OCI Document Understanding** | Purpose-built document AI |
| DynamoDB | **OCI NoSQL Database** | Or Autonomous JSON Database |
| S3 | **OCI Object Storage** | Standard/Archive tiers |
| SQS | **OCI Queue** | Or OCI Streaming for high-volume |
| CloudFront | **OCI CDN** | Or Load Balancer + WAF |
| CloudWatch | **OCI Logging + Monitoring** | Full observability stack |
| AWS CDK | **OCI Resource Manager** | Terraform-based IaC |

### OCI Document Understanding Capabilities

```yaml
Pre-built Models:
  - Invoice Extraction (KEY_VALUE_EXTRACTION)
  - Receipt Processing
  - Table Detection
  - Document Classification

Invoice Fields Extracted:
  - Vendor name, address, tax ID
  - Invoice number, date, due date
  - Line items with descriptions
  - Subtotal, tax, total
  - Currency, payment terms

Output Format: JSON with confidence scores
Languages: 15+ including CJK
```

### OCI Generative AI Options

| Model | Use Case | Multimodal |
|-------|----------|------------|
| Cohere Command R+ | Text reasoning, validation | No |
| Meta Llama 3.1 405B | Complex reasoning | No |
| Meta Llama 3.2 90B Vision | Document understanding | **Yes** |
| Custom Fine-tuned | Domain-specific | Varies |

**For direct PDF → JSON (like Claude approach):** Use **Meta Llama 3.2 Vision** or consider **Bring Your Own Model** with Claude via Bedrock cross-region.

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        OCI Invoice Platform                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐   │
│  │   Web UI    │────▶│   API GW     │────▶│  OCI Functions  │   │
│  │ (Static)    │     │              │     │  (Orchestrator) │   │
│  └─────────────┘     └──────────────┘     └────────┬────────┘   │
│        │                                           │             │
│        │                                           ▼             │
│        │            ┌──────────────────────────────┐             │
│        ▼            │      Processing Pipeline      │             │
│  ┌───────────┐      │  ┌─────────┐   ┌──────────┐  │             │
│  │  Object   │─────▶│  │ Doc AI  │──▶│  GenAI   │  │             │
│  │  Storage  │      │  │ (fast)  │   │ (fallbk) │  │             │
│  └───────────┘      │  └─────────┘   └──────────┘  │             │
│                     └──────────────┬───────────────┘             │
│                                    │                             │
│                                    ▼                             │
│                     ┌──────────────────────────────┐             │
│                     │        Data Layer            │             │
│                     │  ┌─────────┐  ┌───────────┐  │             │
│                     │  │ NoSQL   │  │ Autonomous │ │             │
│                     │  │ (meta)  │  │ JSON (arch)│ │             │
│                     │  └─────────┘  └───────────┘  │             │
│                     └──────────────────────────────┘             │
│                                    │                             │
│                                    ▼                             │
│                     ┌──────────────────────────────┐             │
│                     │    Oracle Fusion Cloud AP    │             │
│                     │   (Native REST Integration)  │             │
│                     └──────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Frontend (OCI Static Hosting)
```yaml
Service: OCI Object Storage (Static Website) + OCI CDN
Features:
  - PWA support (offline capable)
  - Responsive design
  - Drag-and-drop upload
  - Real-time status updates
```

#### 2. API Layer (OCI API Gateway + Functions)
```yaml
Endpoints:
  POST /invoices/upload     → Initiate processing
  GET  /invoices/{id}       → Get extraction results
  GET  /invoices            → List processed invoices
  POST /invoices/{id}/transform → Convert to Fusion format

Security:
  - OCI IAM + IDCS
  - API Key + OAuth2
  - Rate limiting
```

#### 3. Processing Pipeline

```yaml
Stage 1 - Document Understanding:
  Service: OCI Document Understanding
  Input: PDF/Image from Object Storage
  Output: Structured JSON + confidence scores
  Latency: 2-5 seconds

Stage 2 - GenAI Validation (Conditional):
  Trigger: Confidence < 85% OR complex layout
  Service: OCI Generative AI (Llama 3.2 Vision or Cohere)
  Task: Validate/correct/enhance extraction

Stage 3 - Fusion Transform:
  Service: OCI Functions
  Output: AP_INVOICES_INTERFACE format
```

#### 4. Data Layer
```yaml
Hot Storage:
  Service: OCI NoSQL Database
  Use: Metadata, processing status, recent results

Archive Storage:
  Service: OCI Object Storage (Archive tier)
  Use: Original PDFs, historical data

Analytics Ready:
  Service: Autonomous JSON Database (optional)
  Use: Complex queries, reporting, ML features
```

## Cost Estimation (OCI)

### Per 1,000 Invoices/Month

| Component | OCI Service | Est. Cost |
|-----------|-------------|-----------|
| Document Understanding | OCI Document Understanding | $15-20 |
| GenAI (15% fallback) | OCI Generative AI | $5-10 |
| Compute | OCI Functions | $2-5 |
| Storage | Object Storage | $1-2 |
| Database | NoSQL Database | $5-10 |
| Networking | API Gateway + CDN | $2-5 |
| **Total** | | **$30-52/month** |

### Enterprise Volume Pricing

| Volume | Est. Monthly Cost | Per-Invoice |
|--------|-------------------|-------------|
| 1,000 | $30-52 | $0.03-0.05 |
| 10,000 | $200-350 | $0.02-0.035 |
| 100,000 | $1,500-2,500 | $0.015-0.025 |

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] OCI tenancy setup with compartment structure
- [ ] Resource Manager (Terraform) templates
- [ ] Object Storage buckets with lifecycle policies
- [ ] OCI Functions skeleton

### Phase 2: Document AI (Week 3-4)
- [ ] OCI Document Understanding integration
- [ ] Invoice extraction pipeline
- [ ] Confidence scoring logic
- [ ] Error handling and retry logic

### Phase 3: GenAI Enhancement (Week 5-6)
- [ ] OCI Generative AI integration
- [ ] Fallback logic for low-confidence results
- [ ] Multi-language validation
- [ ] Edge case handling

### Phase 4: Fusion Integration (Week 7-8)
- [ ] Oracle Fusion AP Interface mapping
- [ ] REST API integration
- [ ] Error reconciliation
- [ ] End-to-end testing

### Phase 5: Production (Week 9-10)
- [ ] Security hardening
- [ ] Observability setup
- [ ] Performance optimization
- [ ] Documentation and handoff

## GitHub Repository Strategy

### Recommended Organization Structure

```
github.com/oci-ai-architects/
├── invoice-oci/              ← Main application
├── oci-document-ai-patterns/ ← Reusable patterns
├── oci-fusion-integrations/  ← Fusion connectors
└── terraform-oci-serverless/ ← IaC modules
```

### Alternative: Oracle Official Repositories

```
github.com/oracle-samples/           ← Oracle maintained
github.com/oracle-quickstart/        ← Reference architectures
github.com/oracle-devrel/            ← Developer relations
```

### Recommendation

**Create under `oci-ai-architects`** for:
- Community ownership and collaboration
- Quick iteration without Oracle approval process
- Clear "unofficial/community" positioning

**Structure:**
```
oci-ai-architects/invoice-oci/
├── infrastructure/
│   └── terraform/
├── functions/
│   ├── upload-handler/
│   ├── document-processor/
│   ├── genai-validator/
│   └── fusion-transformer/
├── frontend/
│   └── pwa/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── OCI-SETUP.md
│   └── FUSION-INTEGRATION.md
└── examples/
    └── sample-invoices/
```

## Next Steps

1. **Decision Required:** Confirm GitHub org (`oci-ai-architects` vs personal)
2. **Decision Required:** Full OCI-native or hybrid (keep Bedrock option)?
3. **Action:** Create Terraform templates for OCI infrastructure
4. **Action:** Build Document Understanding integration prototype

---

## References

- [OCI Document Understanding](https://docs.oracle.com/en-us/iaas/Content/document-understanding/home.htm)
- [OCI Generative AI Service](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)
- [Oracle Fusion AP Interface](https://docs.oracle.com/en/cloud/saas/financials/24d/oefbf/ap-invoices-interface.html)

---
*Created: 2026-02-02 | Author: FrankX Oracle Work*
