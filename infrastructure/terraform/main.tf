# Invoice-OCI Infrastructure
# Oracle Cloud Infrastructure - Serverless Invoice Processing
#
# DISCLAIMER: Unofficial community project. Not affiliated with Oracle Corporation.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.30.0"
    }
  }
}

# ============================================================================
# Variables
# ============================================================================

variable "tenancy_ocid" {
  description = "OCI Tenancy OCID"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
  default     = "eu-frankfurt-1"
}

variable "compartment_ocid" {
  description = "Compartment OCID for Invoice-OCI resources"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "invoice-oci"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.region
}

# ============================================================================
# Local Values
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
    "ManagedBy"   = "Terraform"
    "Application" = "Invoice Processing"
  }
}

# ============================================================================
# Object Storage - PDF Upload and Results
# ============================================================================

resource "oci_objectstorage_bucket" "invoices_upload" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "${local.name_prefix}-invoices-upload"
  access_type    = "NoPublicAccess"

  versioning = "Enabled"

  freeform_tags = local.common_tags

  # Lifecycle rule: Archive after 30 days, delete after 1 year
  # (Configured via separate resource below)
}

resource "oci_objectstorage_bucket" "invoices_results" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "${local.name_prefix}-invoices-results"
  access_type    = "NoPublicAccess"

  freeform_tags = local.common_tags
}

resource "oci_objectstorage_bucket" "static_website" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "${local.name_prefix}-website"
  access_type    = "ObjectRead"  # Public read for static hosting

  freeform_tags = local.common_tags
}

data "oci_objectstorage_namespace" "this" {
  compartment_id = var.tenancy_ocid
}

# ============================================================================
# OCI Functions - Serverless Compute
# ============================================================================

resource "oci_functions_application" "invoice_app" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-app"
  subnet_ids     = [oci_core_subnet.functions_subnet.id]

  config = {
    "UPLOAD_BUCKET"        = oci_objectstorage_bucket.invoices_upload.name
    "RESULTS_BUCKET"       = oci_objectstorage_bucket.invoices_results.name
    "NOSQL_TABLE"          = oci_nosql_table.invoice_metadata.name
    "DU_CONFIDENCE_THRESHOLD" = "0.85"
  }

  freeform_tags = local.common_tags
}

# Function definitions (deployed via fn CLI or OCI DevOps)
# - upload-handler: Handles file uploads, triggers processing
# - document-processor: OCI Document Understanding extraction
# - genai-validator: OCI GenAI fallback for low-confidence results
# - fusion-transformer: Converts to Oracle Fusion AP format

# ============================================================================
# NoSQL Database - Metadata and Results
# ============================================================================

resource "oci_nosql_table" "invoice_metadata" {
  compartment_id = var.compartment_ocid
  name           = "${local.name_prefix}-metadata"

  ddl_statement = <<-EOT
    CREATE TABLE IF NOT EXISTS "${local.name_prefix}-metadata" (
      invoice_id STRING,
      upload_timestamp TIMESTAMP,
      processing_status STRING,
      du_confidence NUMBER,
      genai_used BOOLEAN,
      vendor_name STRING,
      invoice_number STRING,
      invoice_date STRING,
      total_amount NUMBER,
      currency STRING,
      extraction_result JSON,
      fusion_payload JSON,
      PRIMARY KEY(invoice_id)
    )
  EOT

  table_limits {
    max_read_units     = 50
    max_write_units    = 50
    max_storage_in_gbs = 10
  }

  freeform_tags = local.common_tags
}

# ============================================================================
# API Gateway
# ============================================================================

resource "oci_apigateway_gateway" "invoice_api" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-api"
  endpoint_type  = "PUBLIC"
  subnet_id      = oci_core_subnet.api_subnet.id

  freeform_tags = local.common_tags
}

resource "oci_apigateway_deployment" "invoice_api_v1" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.invoice_api.id
  display_name   = "${local.name_prefix}-api-v1"
  path_prefix    = "/v1"

  specification {
    # CORS configuration
    request_policies {
      cors {
        allowed_origins = ["*"]  # Restrict in production
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        allowed_headers = ["*"]
      }
    }

    # POST /invoices/upload
    routes {
      path    = "/invoices/upload"
      methods = ["POST"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = "" # Set after function deployment
      }
    }

    # GET /invoices/{id}
    routes {
      path    = "/invoices/{invoiceId}"
      methods = ["GET"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = "" # Set after function deployment
      }
    }

    # GET /invoices (list)
    routes {
      path    = "/invoices"
      methods = ["GET"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = "" # Set after function deployment
      }
    }

    # POST /invoices/{id}/transform
    routes {
      path    = "/invoices/{invoiceId}/transform"
      methods = ["POST"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = "" # Set after function deployment
      }
    }
  }

  freeform_tags = local.common_tags
}

# ============================================================================
# Networking - VCN for Functions
# ============================================================================

resource "oci_core_vcn" "invoice_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "invoiceoci"

  freeform_tags = local.common_tags
}

resource "oci_core_subnet" "functions_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.invoice_vcn.id
  display_name   = "${local.name_prefix}-functions-subnet"
  cidr_block     = "10.0.1.0/24"

  prohibit_public_ip_on_vnic = true

  freeform_tags = local.common_tags
}

resource "oci_core_subnet" "api_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.invoice_vcn.id
  display_name   = "${local.name_prefix}-api-subnet"
  cidr_block     = "10.0.2.0/24"

  prohibit_public_ip_on_vnic = false  # Public API Gateway

  freeform_tags = local.common_tags
}

# Internet Gateway for public access
resource "oci_core_internet_gateway" "invoice_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.invoice_vcn.id
  display_name   = "${local.name_prefix}-igw"
  enabled        = true

  freeform_tags = local.common_tags
}

# NAT Gateway for Functions (outbound)
resource "oci_core_nat_gateway" "invoice_nat" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.invoice_vcn.id
  display_name   = "${local.name_prefix}-nat"

  freeform_tags = local.common_tags
}

# Service Gateway for OCI Services
resource "oci_core_service_gateway" "invoice_sgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.invoice_vcn.id
  display_name   = "${local.name_prefix}-sgw"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  freeform_tags = local.common_tags
}

data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

# ============================================================================
# Queue Service - Processing Pipeline
# ============================================================================

resource "oci_queue_queue" "invoice_processing" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-processing-queue"

  dead_letter_queue_delivery_count = 3
  retention_in_seconds            = 604800  # 7 days
  visibility_in_seconds           = 300     # 5 minutes

  freeform_tags = local.common_tags
}

resource "oci_queue_queue" "invoice_dlq" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-dlq"

  retention_in_seconds  = 1209600  # 14 days
  visibility_in_seconds = 300

  freeform_tags = local.common_tags
}

# ============================================================================
# Logging and Monitoring
# ============================================================================

resource "oci_logging_log_group" "invoice_logs" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-logs"

  freeform_tags = local.common_tags
}

resource "oci_logging_log" "function_logs" {
  display_name = "${local.name_prefix}-function-logs"
  log_group_id = oci_logging_log_group.invoice_logs.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.invoice_app.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
  }

  is_enabled = true

  freeform_tags = local.common_tags
}

# ============================================================================
# IAM Policies
# ============================================================================

resource "oci_identity_policy" "functions_policy" {
  compartment_id = var.compartment_ocid
  name           = "${local.name_prefix}-functions-policy"
  description    = "Policy for Invoice-OCI Functions"

  statements = [
    # Allow functions to access Object Storage
    "Allow dynamic-group ${local.name_prefix}-functions-dg to manage objects in compartment id ${var.compartment_ocid}",

    # Allow functions to use Document Understanding
    "Allow dynamic-group ${local.name_prefix}-functions-dg to use ai-document-jobs in compartment id ${var.compartment_ocid}",

    # Allow functions to use Generative AI
    "Allow dynamic-group ${local.name_prefix}-functions-dg to use generative-ai-inference-family in compartment id ${var.compartment_ocid}",

    # Allow functions to access NoSQL
    "Allow dynamic-group ${local.name_prefix}-functions-dg to use nosql-tables in compartment id ${var.compartment_ocid}",

    # Allow functions to use Queue
    "Allow dynamic-group ${local.name_prefix}-functions-dg to use queues in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = local.common_tags
}

resource "oci_identity_dynamic_group" "functions_dg" {
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-functions-dg"
  description    = "Dynamic group for Invoice-OCI Functions"

  matching_rule = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = local.common_tags
}

# ============================================================================
# Outputs
# ============================================================================

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = oci_apigateway_gateway.invoice_api.hostname
}

output "upload_bucket" {
  description = "Object Storage bucket for PDF uploads"
  value       = oci_objectstorage_bucket.invoices_upload.name
}

output "results_bucket" {
  description = "Object Storage bucket for extraction results"
  value       = oci_objectstorage_bucket.invoices_results.name
}

output "nosql_table" {
  description = "NoSQL table for invoice metadata"
  value       = oci_nosql_table.invoice_metadata.name
}

output "processing_queue" {
  description = "Queue OCID for invoice processing"
  value       = oci_queue_queue.invoice_processing.id
}

output "functions_application" {
  description = "Functions application OCID"
  value       = oci_functions_application.invoice_app.id
}
