#!/bin/bash
# Docker Registry Setup Script
# Configure credentials and push Netflix API images to multiple registries

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check Docker installation
check_docker() {
    print_header "Checking Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    print_success "Docker is installed: $(docker --version)"
}

# Setup Docker Hub
setup_docker_hub() {
    print_header "Docker Hub Setup"
    
    read -p "Enter Docker Hub username: " DOCKER_USERNAME
    read -sp "Enter Docker Hub password: " DOCKER_PASSWORD
    echo
    read -p "Enter repository name (e.g., yourusername/netflix-api): " DOCKER_HUB_REPO
    
    export DOCKER_USERNAME
    export DOCKER_PASSWORD
    export DOCKER_HUB_REPO
    
    # Test login
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    
    print_success "Docker Hub authenticated"
}

# Setup AWS ECR
setup_ecr() {
    print_header "AWS ECR Setup"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        print_warning "Install with: pip install awscli"
        return 1
    fi
    
    read -p "Enter AWS Account ID: " AWS_ACCOUNT_ID
    read -p "Enter AWS Region (default: us-east-1): " AWS_REGION
    AWS_REGION=${AWS_REGION:-us-east-1}
    
    export AWS_ACCOUNT_ID
    export AWS_REGION
    
    # Create ECR repository if it doesn't exist
    echo "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name netflix-api \
        --region "$AWS_REGION" \
        || print_warning "Repository may already exist"
    
    # Get login token
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    print_success "AWS ECR authenticated"
}

# Setup Google Cloud Registry
setup_gcr() {
    print_header "Google Cloud Registry Setup"
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed"
        print_warning "Install from: https://cloud.google.com/sdk/docs/install"
        return 1
    fi
    
    read -p "Enter GCP Project ID: " GCP_PROJECT_ID
    read -p "Enter GCR Region (default: gcr.io): " GCR_REGION
    GCR_REGION=${GCR_REGION:-gcr.io}
    
    export GCP_PROJECT_ID
    export GCR_REGION
    
    # Configure Docker
    gcloud auth configure-docker "$GCR_REGION"
    
    print_success "Google Cloud Registry authenticated"
}

# Setup Azure Container Registry
setup_acr() {
    print_header "Azure Container Registry Setup"
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed"
        print_warning "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        return 1
    fi
    
    read -p "Enter Azure Registry Name: " AZURE_REGISTRY_NAME
    read -p "Enter Azure Resource Group: " AZURE_RESOURCE_GROUP
    
    export AZURE_REGISTRY_NAME
    export AZURE_RESOURCE_GROUP
    
    # Create ACR if it doesn't exist
    echo "Creating Azure Container Registry..."
    az acr create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_REGISTRY_NAME" \
        --sku Basic \
        || print_warning "Registry may already exist"
    
    # Login
    az acr login --name "$AZURE_REGISTRY_NAME"
    
    # Get credentials
    CREDENTIALS=$(az acr credential show \
        --name "$AZURE_REGISTRY_NAME" \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --query "passwords[0].value" \
        -o tsv)
    
    export AZURE_REGISTRY_USER="$AZURE_REGISTRY_NAME"
    export AZURE_REGISTRY_PASSWORD="$CREDENTIALS"
    
    print_success "Azure Container Registry authenticated"
}

# Save credentials
save_credentials() {
    print_header "Saving Credentials"
    
    read -p "Save credentials to .env file? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > .env.docker << EOF
# Docker Registry Credentials
DOCKER_USERNAME=${DOCKER_USERNAME}
DOCKER_PASSWORD=${DOCKER_PASSWORD}
DOCKER_HUB_REPO=${DOCKER_HUB_REPO}

# AWS ECR
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
AWS_REGION=${AWS_REGION}

# Google Cloud Registry
GCP_PROJECT_ID=${GCP_PROJECT_ID}
GCR_REGION=${GCR_REGION}

# Azure Container Registry
AZURE_REGISTRY_NAME=${AZURE_REGISTRY_NAME}
AZURE_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP}
AZURE_REGISTRY_USER=${AZURE_REGISTRY_USER}
AZURE_REGISTRY_PASSWORD=${AZURE_REGISTRY_PASSWORD}
EOF
        
        chmod 600 .env.docker
        print_success "Credentials saved to .env.docker"
        print_warning "Keep this file secure and add to .gitignore"
    fi
}

# Push images
push_images() {
    print_header "Pushing Docker Images"
    
    read -p "Enter image version (default: latest): " VERSION
    VERSION=${VERSION:-latest}
    
    python scripts/docker_push.py \
        --all-registries \
        --version "$VERSION"
}

# Main menu
show_menu() {
    echo
    print_header "Netflix API - Docker Registry Setup"
    echo "1. Setup Docker Hub"
    echo "2. Setup AWS ECR"
    echo "3. Setup Google Cloud Registry"
    echo "4. Setup Azure Container Registry"
    echo "5. Setup All Registries"
    echo "6. Push Images to All Registries"
    echo "7. Save Credentials"
    echo "8. Exit"
    echo
    read -p "Select option (1-8): " option
}

# Main loop
main() {
    check_docker
    
    while true; do
        show_menu
        
        case $option in
            1)
                setup_docker_hub
                ;;
            2)
                setup_ecr
                ;;
            3)
                setup_gcr
                ;;
            4)
                setup_acr
                ;;
            5)
                setup_docker_hub
                setup_ecr
                setup_gcr
                setup_acr
                ;;
            6)
                push_images
                ;;
            7)
                save_credentials
                ;;
            8)
                print_success "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
    done
}

main
