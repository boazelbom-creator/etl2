#!/bin/bash

# =============================================================================
# AWS Lambda Deployment Script
# Facebook Posts to RAG Chunks ETL Pipeline
# =============================================================================

set -e  # Exit on any error

# Configuration - Update these values for your environment
FUNCTION_NAME="facebook-chunks-etl"
REGION="us-east-1"
RUNTIME="python3.12"
HANDLER="lambda_function.lambda_handler"
MEMORY_SIZE=1024
TIMEOUT=600
DESCRIPTION="ETL pipeline: Facebook posts to RAG chunks"

# Optional: IAM Role ARN (required for creating new function)
# ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "AWS Lambda Deployment Script"
echo "Facebook Chunks ETL - Python 3.12"
echo "============================================================"
echo ""

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run 'aws configure' to set up your credentials"
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI configured${NC}"
echo ""

# Step 1: Create deployment package
echo "Step 1: Creating deployment package..."
echo "----------------------------------------"

# Clean previous builds
echo "Cleaning up previous builds..."
rm -rf package
rm -f lambda-deployment.zip

# Create package directory
mkdir -p package

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t package/ --quiet

# Copy source code
echo "Copying source code..."
cp -r src package/
cp lambda_function.py package/

# Copy config if exists (optional - Lambda should use env vars)
if [ -d "config" ]; then
    cp -r config package/
fi

# Create zip file
echo "Creating deployment zip..."
cd package
zip -r ../lambda-deployment.zip . -q
cd ..

ZIP_SIZE=$(du -h lambda-deployment.zip | cut -f1)
echo -e "${GREEN}✓ Deployment package created: lambda-deployment.zip (${ZIP_SIZE})${NC}"
echo ""

# Step 2: Check if Lambda function exists
echo "Step 2: Checking Lambda function status..."
echo "----------------------------------------"

FUNCTION_EXISTS=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>&1 || true)

if echo "$FUNCTION_EXISTS" | grep -q "ResourceNotFoundException"; then
    echo -e "${YELLOW}Function '$FUNCTION_NAME' does not exist${NC}"

    # Check if ROLE_ARN is set
    if [ -z "$ROLE_ARN" ]; then
        echo ""
        echo -e "${RED}Error: ROLE_ARN is required to create a new Lambda function${NC}"
        echo ""
        echo "To create the function, either:"
        echo "1. Set ROLE_ARN in this script (line 18)"
        echo "2. Or create the function manually in AWS Console, then run this script to update"
        echo ""
        echo "Example ROLE_ARN: arn:aws:iam::123456789012:role/lambda-execution-role"
        echo ""
        echo "The role needs these permissions:"
        echo "  - AWSLambdaBasicExecutionRole (for CloudWatch logs)"
        echo "  - AWSLambdaVPCAccessExecutionRole (if using VPC)"
        echo "  - Any custom permissions for your database"
        exit 1
    fi

    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --memory-size "$MEMORY_SIZE" \
        --timeout "$TIMEOUT" \
        --description "$DESCRIPTION" \
        --zip-file fileb://lambda-deployment.zip \
        --region "$REGION" \
        --output text > /dev/null

    echo -e "${GREEN}✓ Lambda function created successfully${NC}"
else
    echo -e "${GREEN}✓ Function '$FUNCTION_NAME' exists - updating...${NC}"

    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-deployment.zip \
        --region "$REGION" \
        --output text > /dev/null

    echo -e "${GREEN}✓ Function code updated${NC}"

    # Wait for update to complete
    echo "Waiting for update to complete..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"

    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --handler "$HANDLER" \
        --memory-size "$MEMORY_SIZE" \
        --timeout "$TIMEOUT" \
        --description "$DESCRIPTION" \
        --region "$REGION" \
        --output text > /dev/null

    echo -e "${GREEN}✓ Function configuration updated${NC}"
fi

echo ""
echo "============================================================"
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo "============================================================"
echo ""
echo "Function: $FUNCTION_NAME"
echo "Region:   $REGION"
echo "Runtime:  $RUNTIME"
echo "Memory:   ${MEMORY_SIZE}MB"
echo "Timeout:  ${TIMEOUT}s"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in AWS Console or via CLI:"
echo "   aws lambda update-function-configuration \\"
echo "     --function-name $FUNCTION_NAME \\"
echo "     --environment \"Variables={DB_HOST=your-host,DB_NAME=your-db,DB_USER=your-user,DB_PASSWORD=your-pass,DB_PORT=5432,CHUNK_SIZE=700,BATCH_COMMIT_SIZE=1000}\""
echo ""
echo "2. If using VPC, configure VPC settings in AWS Console"
echo ""
echo "3. Test the function:"
echo "   aws lambda invoke --function-name $FUNCTION_NAME --region $REGION output.json"
echo ""
echo "============================================================"
