# Example Terraform Variables for Invoice-OCI
# Copy this file to dev.tfvars or prod.tfvars and fill in your values

# Required: Your OCI tenancy OCID
tenancy_ocid = "ocid1.tenancy.oc1..your-tenancy-ocid"

# Required: The compartment where resources will be created
compartment_ocid = "ocid1.compartment.oc1..your-compartment-ocid"

# Optional: OCI region (default: eu-frankfurt-1)
region = "eu-frankfurt-1"

# Optional: Project name prefix (default: invoice-oci)
project_name = "invoice-oci"

# Optional: Environment name (default: dev)
environment = "dev"
