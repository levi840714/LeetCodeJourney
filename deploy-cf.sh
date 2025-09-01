#!/bin/bash

# Google Cloud Functions Deployment Script for LeetCode Journey
# This script deploys the LeetCode tracking service to Google Cloud Functions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 LeetCode Journey - Cloud Functions Deployment Script${NC}"
echo "=========================================================="

# Check if required tools are installed
check_requirements() {
    echo -e "${BLUE}📋 Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ Google Cloud CLI not found. Please install it first.${NC}"
        echo "   Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found. Please install Python 3.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements satisfied${NC}"
}

# Prompt for configuration
get_configuration() {
    echo -e "\n${BLUE}⚙️  Configuration Setup${NC}"
    
    # Project ID
    echo -n "Enter your Google Cloud Project ID: "
    read PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Project ID is required${NC}"
        exit 1
    fi
    
    # Function name
    echo -n "Enter Cloud Function name (default: leetcode-journey): "
    read FUNCTION_NAME
    FUNCTION_NAME=${FUNCTION_NAME:-leetcode-journey}
    
    # Region
    echo -n "Enter deployment region (default: asia-east1): "
    read REGION
    REGION=${REGION:-asia-east1}
    
    # Google Sheet name
    echo -n "Enter your Google Sheet name: "
    read SHEET_NAME
    if [ -z "$SHEET_NAME" ]; then
        echo -e "${RED}❌ Google Sheet name is required${NC}"
        exit 1
    fi
    
    # Service account JSON
    echo -n "Enter path to service account JSON file (default: ./credentials.json): "
    read CREDENTIALS_FILE
    CREDENTIALS_FILE=${CREDENTIALS_FILE:-./credentials.json}
    
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        echo -e "${RED}❌ Service account file not found: $CREDENTIALS_FILE${NC}"
        exit 1
    fi
    
    echo -e "\n${GREEN}📝 Configuration:${NC}"
    echo "   Project ID: $PROJECT_ID"
    echo "   Function Name: $FUNCTION_NAME"
    echo "   Region: $REGION"
    echo "   Google Sheet: $SHEET_NAME"
    echo "   Service Account: $CREDENTIALS_FILE"
}

# Setup Google Cloud project
setup_gcloud() {
    echo -e "\n${BLUE}🔧 Setting up Google Cloud...${NC}"
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    echo "Enabling required APIs..."
    gcloud services enable cloudfunctions.googleapis.com
    gcloud services enable sheets.googleapis.com
    gcloud services enable drive.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    
    # Setup IAM permissions for Cloud Functions
    echo "Setting up IAM permissions..."
    # Check if service account exists, create if needed
    if ! gcloud iam service-accounts describe cfunction@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
        echo "Creating Cloud Functions service account..."
        gcloud iam service-accounts create cfunction \
            --display-name="Cloud Functions Service Account"
    fi
    
    # Add necessary IAM roles
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:cfunction@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/cloudfunctions.serviceAgent" --quiet
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:cfunction@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/storage.objectViewer" --quiet
    
    echo "Waiting for IAM changes to propagate..."
    sleep 10
    
    echo -e "${GREEN}✅ Google Cloud setup complete${NC}"
}

# Create environment file for Cloud Functions
create_env_file() {
    echo -e "\n${BLUE}📝 Creating environment configuration...${NC}"
    
    # Read service account JSON and encode as base64
    SERVICE_ACCOUNT_JSON=$(cat $CREDENTIALS_FILE | base64 -w 0)
    
    # Create .env.yaml for Cloud Functions
    cat > .env.yaml << EOF
GOOGLE_SHEET_NAME: "$SHEET_NAME"
GOOGLE_SERVICE_ACCOUNT_JSON: "$SERVICE_ACCOUNT_JSON"
EOF
    
    echo -e "${GREEN}✅ Environment configuration created${NC}"
}

# Deploy the function
deploy_function() {
    echo -e "\n${BLUE}🚀 Deploying Cloud Function...${NC}"
    
    # Copy requirements for Cloud Functions
    cp requirements-cf.txt requirements.txt
    
    # Deploy the function
    gcloud functions deploy $FUNCTION_NAME \
        --runtime python311 \
        --trigger-http \
        --allow-unauthenticated \
        --entry-point leetcode_journey \
        --source . \
        --env-vars-file .env.yaml \
        --region $REGION \
        --memory 256MB \
        --timeout 60s \
        --max-instances 10
    
    # Get the function URL
    FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(httpsTrigger.url)")
    
    echo -e "\n${GREEN}🎉 Deployment successful!${NC}"
    echo -e "${GREEN}📡 Function URL: $FUNCTION_URL${NC}"
    echo -e "${YELLOW}⚠️  Update your Chrome extension popup.js with this URL${NC}"
}

# Update Chrome extension configuration
update_chrome_extension() {
    echo -e "\n${BLUE}🔧 Chrome extension configuration info...${NC}"
    
    echo -e "${GREEN}✅ Chrome extension supports dynamic configuration${NC}"
    echo -e "${YELLOW}📝 To configure the extension:${NC}"
    echo "   1. Open the extension popup on any LeetCode problem page"
    echo "   2. Click the '⚙️ Settings' link at the bottom"
    echo "   3. Select 'Cloud Functions' and paste your function URL:"
    echo "      $FUNCTION_URL"
    echo "   4. Click 'Save Settings'"
    echo ""
    echo -e "${BLUE}💡 The extension will automatically detect the best available endpoint${NC}"
}

# Test the deployed function
test_function() {
    echo -e "\n${BLUE}🧪 Testing deployed function...${NC}"
    
    # Create test payload
    TEST_PAYLOAD='{
        "problem_number": "1",
        "name": "Two Sum",
        "difficulty": "Easy",
        "url": "https://leetcode.com/problems/two-sum/",
        "topic": "Array, Hash Table",
        "notes": "Test deployment from Cloud Functions"
    }'
    
    # Test the function
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$TEST_PAYLOAD" \
        "$FUNCTION_URL/log")
    
    if echo "$RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✅ Function test successful!${NC}"
        echo "Response: $RESPONSE"
    else
        echo -e "${YELLOW}⚠️  Function deployed but test failed. Response:${NC}"
        echo "$RESPONSE"
    fi
}

# Cleanup
cleanup() {
    echo -e "\n${BLUE}🧹 Cleaning up temporary files...${NC}"
    
    # Remove temporary files
    rm -f .env.yaml
    rm -f requirements.txt
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main execution
main() {
    check_requirements
    get_configuration
    
    echo -e "\n${YELLOW}🚨 Ready to deploy. Continue? (y/N)${NC}"
    read -r CONFIRM
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    setup_gcloud
    create_env_file
    deploy_function
    update_chrome_extension
    test_function
    cleanup
    
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo "=========================================================="
    echo -e "${GREEN}📡 Your Cloud Function URL: $FUNCTION_URL${NC}"
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "   1. Update your Chrome extension with the new URL"
    echo "   2. Test the extension on a LeetCode problem page"
    echo "   3. Check your Google Sheet for the logged data"
    echo ""
    echo -e "${BLUE}🔗 Useful commands:${NC}"
    echo "   View logs:    gcloud functions logs read $FUNCTION_NAME --region=$REGION"
    echo "   Delete:       gcloud functions delete $FUNCTION_NAME --region=$REGION"
    echo "   Redeploy:     ./deploy-cf.sh"
}

# Run main function
main "$@"