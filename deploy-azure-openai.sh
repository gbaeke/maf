#!/bin/bash

# Azure OpenAI Resource Deployment Script
# This script deploys an Azure OpenAI resource with GPT-4.1 model to Azure
# The resource name is generated deterministically based on resource group and subscription ID

set -e  # Exit on any error

# Configuration
RESOURCE_GROUP="rg-maf"
LOCATION="swedencentral"  # Change if needed - check Azure OpenAI availability in your region
MODEL_DEPLOYMENT_NAME="gpt-41"
MODEL_NAME="gpt-4.1"
MODEL_VERSION="2025-04-14"  # GPT-4.1 version
RESOURCE_SKU_NAME="S0"  # SKU for the Azure OpenAI resource
DEPLOYMENT_SKU_NAME="GlobalStandard"  # SKU for the model deployment (GPT-4.1 requires GlobalStandard)
SKU_CAPACITY=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Azure OpenAI Resource Deployment Script${NC}"
echo "=============================================="
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
print_status "Checking Azure CLI authentication..."
if ! az account show &> /dev/null; then
    print_error "You are not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi

# Get current subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
print_success "Logged in to Azure subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Generate deterministic resource name based on resource group and subscription ID
# Create a hash from resource group and subscription ID, then take first 8 characters
HASH_INPUT="${RESOURCE_GROUP}-${SUBSCRIPTION_ID}"
if command -v sha256sum &> /dev/null; then
    RESOURCE_HASH=$(echo -n "$HASH_INPUT" | sha256sum | cut -c1-8)
elif command -v shasum &> /dev/null; then
    RESOURCE_HASH=$(echo -n "$HASH_INPUT" | shasum -a 256 | cut -c1-8)
else
    # Fallback: use a simple hash based on the string length and characters
    RESOURCE_HASH=$(echo -n "$HASH_INPUT" | od -An -tx1 | tr -d ' \n' | cut -c1-8)
fi
OPENAI_RESOURCE_NAME="oai-${RESOURCE_GROUP#rg-}-${RESOURCE_HASH}"

# Ensure resource name meets Azure requirements (2-64 chars, alphanumeric and hyphens only)
# Remove any invalid characters and ensure it starts with a letter
OPENAI_RESOURCE_NAME=$(echo "$OPENAI_RESOURCE_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
if [[ ! $OPENAI_RESOURCE_NAME =~ ^[a-z] ]]; then
    OPENAI_RESOURCE_NAME="oai-${OPENAI_RESOURCE_NAME}"
fi

print_status "Generated deterministic resource name: $OPENAI_RESOURCE_NAME"
print_status "This name is based on your resource group and subscription ID for consistency"

# Check if resource group exists, create if not
print_status "Checking if resource group '$RESOURCE_GROUP' exists..."
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    print_status "Creating resource group '$RESOURCE_GROUP' in location '$LOCATION'..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    print_success "Resource group '$RESOURCE_GROUP' created successfully"
else
    print_success "Resource group '$RESOURCE_GROUP' already exists"
fi

# Check Azure OpenAI provider registration
print_status "Checking Azure OpenAI provider registration..."
if ! az provider show --namespace Microsoft.CognitiveServices --query "registrationState" -o tsv | grep -q "Registered"; then
    print_status "Registering Microsoft.CognitiveServices provider..."
    az provider register --namespace Microsoft.CognitiveServices
    print_warning "Provider registration may take a few minutes. You might need to wait before deploying."
fi

# Check if Azure OpenAI resource already exists
print_status "Checking if Azure OpenAI resource '$OPENAI_RESOURCE_NAME' already exists..."
if az cognitiveservices account show --name $OPENAI_RESOURCE_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_warning "Azure OpenAI resource '$OPENAI_RESOURCE_NAME' already exists!"
    print_status "Skipping resource creation and proceeding to model deployment check..."
    RESOURCE_EXISTS=true
else
    RESOURCE_EXISTS=false
fi

# Create Azure OpenAI resource (only if it doesn't exist)
if [ "$RESOURCE_EXISTS" = false ]; then
    print_status "Creating Azure OpenAI resource '$OPENAI_RESOURCE_NAME' with custom subdomain enabled..."
    az cognitiveservices account create \
        --name $OPENAI_RESOURCE_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --kind OpenAI \
        --sku $RESOURCE_SKU_NAME \
        --custom-domain $OPENAI_RESOURCE_NAME \
        --yes

    if [ $? -eq 0 ]; then
        print_success "Azure OpenAI resource '$OPENAI_RESOURCE_NAME' created successfully"
    else
        print_error "Failed to create Azure OpenAI resource"
        exit 1
    fi
else
    print_success "Using existing Azure OpenAI resource '$OPENAI_RESOURCE_NAME'"
fi

# Wait a moment for the resource to be fully provisioned (only if resource was just created)
if [ "$RESOURCE_EXISTS" = false ]; then
    print_status "Waiting for resource provisioning to complete..."
    sleep 30
fi

# Check if model deployment already exists
print_status "Checking if model deployment '$MODEL_DEPLOYMENT_NAME' already exists..."
if az cognitiveservices account deployment show --name $OPENAI_RESOURCE_NAME --resource-group $RESOURCE_GROUP --deployment-name $MODEL_DEPLOYMENT_NAME &> /dev/null; then
    print_warning "Model deployment '$MODEL_DEPLOYMENT_NAME' already exists!"
    print_success "Skipping model deployment..."
    DEPLOYMENT_EXISTS=true
else
    DEPLOYMENT_EXISTS=false
fi

# Deploy GPT-4.1 model (only if it doesn't exist)
if [ "$DEPLOYMENT_EXISTS" = false ]; then
    print_status "Deploying GPT-4.1 model as '$MODEL_DEPLOYMENT_NAME'..."
    az cognitiveservices account deployment create \
        --name $OPENAI_RESOURCE_NAME \
        --resource-group $RESOURCE_GROUP \
        --deployment-name $MODEL_DEPLOYMENT_NAME \
        --model-name $MODEL_NAME \
        --model-version $MODEL_VERSION \
        --model-format OpenAI \
        --sku-capacity $SKU_CAPACITY \
        --sku-name $DEPLOYMENT_SKU_NAME

    if [ $? -eq 0 ]; then
        print_success "GPT-4.1 model deployed successfully as '$MODEL_DEPLOYMENT_NAME'"
    else
        print_error "Failed to deploy GPT-4.1 model"
        print_warning "The resource was created but model deployment failed. You can deploy manually in Azure Portal."
    fi
else
    print_success "Using existing model deployment '$MODEL_DEPLOYMENT_NAME'"
fi

# Get resource information
print_status "Retrieving resource information..."
ENDPOINT=$(az cognitiveservices account show --name $OPENAI_RESOURCE_NAME --resource-group $RESOURCE_GROUP --query "properties.endpoint" -o tsv)
API_KEY=$(az cognitiveservices account keys list --name $OPENAI_RESOURCE_NAME --resource-group $RESOURCE_GROUP --query "key1" -o tsv)

# Display deployment information
echo ""
echo "=============================================="
print_success "Deployment completed successfully!"
echo "=============================================="
echo ""
echo -e "${BLUE}📋 Resource Information:${NC}"
echo "  Resource Name:     $OPENAI_RESOURCE_NAME"
echo "  Resource Group:    $RESOURCE_GROUP"
echo "  Location:          $LOCATION"
echo "  Endpoint:          $ENDPOINT"
echo "  Model Deployment:  $MODEL_DEPLOYMENT_NAME"
echo "  Deployment Type:   $DEPLOYMENT_SKU_NAME (Global Standard - supports global routing)"
echo ""
echo -e "${BLUE}🔑 Configuration for .env file:${NC}"
echo "AZURE_OPENAI_ENDPOINT=\"$ENDPOINT\""
echo "AZURE_OPENAI_API_KEY=\"$API_KEY\""
echo "AZURE_OPENAI_API_VERSION=\"2024-12-01-preview\""
echo "AZURE_OPENAI_DEPLOYMENT=\"$MODEL_DEPLOYMENT_NAME\""
echo ""

# Ask if user wants to update .env file
read -p "Do you want to update your .env file with these values? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing .env if it exists
    if [ -f .env ]; then
        cp .env .env.backup
        print_status "Backed up existing .env to .env.backup"
    fi
    
    # Update .env file
    cat > .env << EOF
# Foundry fields
FOUNDRY_API_KEY="3s2TSQTsGjmfAzj15kZzmcBtquLMwawDwUuIzP0aw9X0LqOWywLhJQQJ99BJACfhMk5XJ3w3AAAAACOG36gk"
FOUNDRY_RESOURCE="fndry-course"

# Fields for AI Search
AZURE_SEARCH_KEY=rN5pHurXK494bvaVpb41bxJXgZQGPIgckssKYvvsSmAzSeBTNJ8q
AZURE_SEARCH_ENDPOINT=https://search-genai-mbarq-dev.search.windows.net
AZURE_SEARCH_INDEX=sops

# Azure OpenAI Configuration (Updated by deployment script)
AZURE_OPENAI_ENDPOINT="$ENDPOINT"
AZURE_OPENAI_API_KEY="$API_KEY"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT="$MODEL_DEPLOYMENT_NAME"
EOF
    
    print_success ".env file updated with new Azure OpenAI configuration"
fi

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Test the deployment with: python3 agent.py"
echo "2. Monitor usage in Azure Portal"
echo "3. Set up cost alerts if needed"
echo ""
echo -e "${YELLOW}💰 Cost Warning:${NC} Azure OpenAI resources incur charges. Monitor your usage."
echo -e "${YELLOW}🔒 Security:${NC} Keep your API key secure and rotate it regularly."
echo ""
print_success "Deployment script completed!"