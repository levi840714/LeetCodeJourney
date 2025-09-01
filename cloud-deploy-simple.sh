#!/bin/bash

# Simple Cloud Functions Deployment Script
# Quick deployment with minimal prompts

set -e

echo "🚀 LeetCode Journey - Simple Cloud Functions Deployment"
echo "======================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first."
    exit 1
fi

# Get basic configuration
echo "Enter your Google Cloud Project ID:"
read PROJECT_ID

echo "Enter your Google Sheet name:"
read SHEET_NAME

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable sheets.googleapis.com

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

# Read service account and create env file
if [ -f "credentials.json" ]; then
    SERVICE_ACCOUNT_JSON=$(cat credentials.json | base64 -w 0)
    cat > .env.yaml << EOF
GOOGLE_SHEET_NAME: "$SHEET_NAME"
GOOGLE_SERVICE_ACCOUNT_JSON: "$SERVICE_ACCOUNT_JSON"
EOF
else
    echo "❌ credentials.json not found"
    exit 1
fi

# Copy requirements
cp requirements-cf.txt requirements.txt

# Deploy
echo "🚀 Deploying function..."
gcloud functions deploy leetcode-journey \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point leetcode_journey \
    --source . \
    --env-vars-file .env.yaml \
    --region asia-east1 \
    --memory 256MB \
    --timeout 60s

# Get URL
FUNCTION_URL=$(gcloud functions describe leetcode-journey --region=asia-east1 --format="value(httpsTrigger.url)")

echo ""
echo "✅ Deployment complete!"
echo "📡 Function URL: $FUNCTION_URL"
echo ""
echo "📝 To configure the Chrome extension:"
echo "   1. Open extension on any LeetCode problem page"
echo "   2. Click '⚙️ Settings' at the bottom"
echo "   3. Select 'Cloud Functions' and paste: $FUNCTION_URL"
echo "   4. Click 'Save Settings'"

# Cleanup
rm -f .env.yaml requirements.txt