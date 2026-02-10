# AWS Bedrock Configuration Guide

Complete guide to set up AWS Bedrock for LLM inference with Meta Llama and Anthropic Claude models.

## Table of Contents
1. [Overview](#overview)
2. [Create AWS Account](#create-aws-account)
3. [Create IAM User](#create-iam-user)
4. [Enable Bedrock Models](#enable-bedrock-models)
5. [Configure Jetson](#configure-jetson)
6. [Test Connection](#test-connection)
7. [Model Selection](#model-selection)
8. [Cost Estimation](#cost-estimation)
9. [Troubleshooting](#troubleshooting)

---

## Overview

**AWS Bedrock** provides:
- Foundation models via API (no infrastructure to manage)
- Pay-per-token pricing
- Models: Llama 3 8B, Llama 3.1 70B, Claude 3.5 Sonnet, etc.
- Low latency (1-3 seconds for responses)

**Why Bedrock for Jetson?**
- Jetson Xavier cannot run large LLMs locally (70B models need 140GB+ VRAM)
- Cloud inference offloads compute
- Access to latest models
- Cost-effective for personal projects (~$0.01-0.10 per conversation)

---

## Create AWS Account

### 1. Sign Up for AWS

```
Go to: https://aws.amazon.com/
Click: "Create an AWS Account"

Required:
- Email address
- Credit card (for billing)
- Phone number (verification)

Note: Free tier available for some services
Bedrock is NOT free tier, but cheap for testing
```

### 2. Verify Account

```
- Check email for verification link
- Complete phone verification
- Wait for account activation (~5-10 minutes)
```

---

## Create IAM User

### 1. Access IAM Console

```bash
# Login to AWS Console
# Go to: https://console.aws.amazon.com/iam/

# Or search for "IAM" in AWS Console search bar
```

### 2. Create New User

**Steps:**
1. Click "Users" → "Add users"
2. Username: `bedrock-user` (or your preferred name)
3. Select: "Provide user access to the AWS Management Console" (optional)
4. Select: "I want to create an IAM user" (not Identity Center user)
5. Click "Next"

### 3. Set Permissions

**Option 1: Attach Policy Directly (Recommended for Testing)**
```
- Select: "Attach policies directly"
- Search: "AmazonBedrockFullAccess"
- Check the box
- Click "Next"
```

**Option 2: Create Custom Policy (Production)**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/meta.llama3-8b-instruct-v1:0",
                "arn:aws:bedrock:*::foundation-model/us.meta.llama3-1-70b-instruct-v1:0",
                "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            ]
        }
    ]
}
```

Save as policy name: `BedrockInvokeOnly`

### 4. Create Access Key

**After user is created:**
1. Click on username: `bedrock-user`
2. Go to "Security credentials" tab
3. Scroll to "Access keys"
4. Click "Create access key"
5. Select use case: "Command Line Interface (CLI)"
6. Check: "I understand the above recommendation"
7. Click "Next" → Add description (optional) → "Create access key"

**Important:**
```
Access Key ID: AKIAXXXXXXXXXXXXXXXX
Secret Access Key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

⚠️ SAVE THESE IMMEDIATELY - Secret only shown once!
⚠️ DO NOT commit to Git or share publicly
```

---

## Enable Bedrock Models

### 1. Request Model Access

```bash
# Go to AWS Bedrock Console
# https://console.aws.amazon.com/bedrock/

# Region: Select "US East (N. Virginia) us-east-1"
# This region has best model availability

# Navigate to: "Model access" (left sidebar)
# Click: "Modify model access"
```

### 2. Enable Required Models

**Select these models:**
- ✅ **Meta Llama 3 8B Instruct** (`meta.llama3-8b-instruct-v1:0`)
  - Fast, low cost, good for chat mode
  
- ✅ **Meta Llama 3.1 70B Instruct** (`us.meta.llama3-1-70b-instruct-v1:0`)
  - Best quality, quiz mode recommended
  - Uses inference profile (cross-region)
  
- ✅ **Anthropic Claude 3.5 Sonnet** (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`)
  - Alternative LLM, excellent reasoning
  - Uses inference profile

**Click: "Save changes"**

**Wait for approval:**
```
Status will change from "Access requested" to "Access granted"
Usually instant for Meta models
Claude may take a few minutes
```

### 3. Verify Access

```bash
# Install AWS CLI if not done (see SETUP.md)
aws bedrock list-foundation-models --region us-east-1 | grep -E "llama|claude"

# Expected output:
# "modelId": "meta.llama3-8b-instruct-v1:0"
# "modelId": "meta.llama3-1-70b-instruct-v1:0"
# "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

---

## Configure Jetson

### 1. Install AWS CLI (if not done)

```bash
# Should already be installed from SETUP.md
aws --version
# Expected: aws-cli/2.x.x

# If not installed:
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. Configure Credentials

```bash
# Run AWS configure
aws configure

# Prompts:
AWS Access Key ID [None]: AKIAXXXXXXXXXXXXXXXX
AWS Secret Access Key [None]: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Default region name [None]: us-east-1
Default output format [None]: json
```

**This creates:**
- `~/.aws/credentials` - Access keys (DO NOT commit to Git)
- `~/.aws/config` - Region and settings

### 3. Verify Configuration

```bash
# Check files exist
ls -la ~/.aws/
# Expected: credentials, config

# Test connection
aws bedrock list-foundation-models --region us-east-1

# Expected: JSON list of available models
```

### 4. Set Up Boto3 (Python SDK)

```bash
# Already installed from requirements.txt
python3 -c "import boto3; print('boto3 version:', boto3.__version__)"
# Expected: boto3 version: 1.37.38
```

**Test Bedrock from Python:**
```python
import boto3

# Create client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Test invoke
import json
response = bedrock.invoke_model(
    modelId='meta.llama3-8b-instruct-v1:0',
    body=json.dumps({
        "prompt": "What is 2+2?",
        "max_gen_len": 50,
        "temperature": 0.5
    })
)

result = json.loads(response['body'].read())
print(result['generation'])
# Expected: "4" or "The answer is 4"
```

---

## Test Connection

### 1. Full Integration Test

```bash
cd /mnt/nvme/adrian/ChatBotRobot/src

# Test with chat mode (no audio)
python3 voice_chat_riva_aws.py --duration 5 --mode chat --llm llama

# Speak into microphone
# Expected:
# 1. ASR transcribes your speech
# 2. Bedrock LLM responds
# 3. TTS speaks response
# 4. Loop continues
```

### 2. Test Each Model

```bash
# Test Llama 8B
python3 -c "
import boto3, json
client = boto3.client('bedrock-runtime', region_name='us-east-1')
resp = client.invoke_model(
    modelId='meta.llama3-8b-instruct-v1:0',
    body=json.dumps({'prompt': 'Say hello', 'max_gen_len': 20})
)
print('Llama 8B:', json.loads(resp['body'].read())['generation'])
"

# Test Llama 70B
python3 -c "
import boto3, json
client = boto3.client('bedrock-runtime', region_name='us-east-1')
resp = client.invoke_model(
    modelId='us.meta.llama3-1-70b-instruct-v1:0',
    body=json.dumps({'prompt': 'Say hello', 'max_gen_len': 20})
)
print('Llama 70B:', json.loads(resp['body'].read())['generation'])
"

# Test Claude
python3 -c "
import boto3, json
client = boto3.client('bedrock-runtime', region_name='us-east-1')
resp = client.invoke_model(
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 50,
        'messages': [{'role': 'user', 'content': 'Say hello'}]
    })
)
print('Claude:', json.loads(resp['body'].read())['content'][0]['text'])
"
```

---

## Model Selection

### Comparison Table

| Model | ID | Speed | Quality | Cost | Best For |
|-------|----|----|---------|------|----------|
| **Llama 3 8B** | `meta.llama3-8b-instruct-v1:0` | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 💰 Cheap | Chat, simple Q&A |
| **Llama 3.1 70B** | `us.meta.llama3-1-70b-instruct-v1:0` | ⚡⚡ Medium | ⭐⭐⭐⭐⭐ Excellent | 💰💰 Moderate | Quiz, complex reasoning |
| **Claude 3.5 Sonnet** | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | ⚡ Slower | ⭐⭐⭐⭐⭐ Excellent | 💰💰💰 Expensive | Creative tasks, long context |

### Recommended Usage

**Chat Mode:**
```bash
# Best: Llama 8B (fast, responsive)
python3 voice_chat_riva_aws.py --mode chat --llm llama
```

**Madagascar Quiz Mode:**
```bash
# Best: Llama 70B (accurate, smart)
python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --rag
```

**Creative Tasks:**
```bash
# Best: Claude (best reasoning)
python3 voice_chat_riva_aws.py --mode chat --llm claude
```

### Inference Profiles

**What are they?**
- Cross-region routing for better availability
- Models like Llama 70B and Claude use them
- Prefix: `us.` (e.g., `us.meta.llama3-1-70b-instruct-v1:0`)

**Why use them?**
- Higher throughput
- Better quota limits
- Automatic failover

---

## Cost Estimation

### Pricing (as of 2024)

**Llama 3 8B:**
- Input: $0.00030 per 1K tokens
- Output: $0.00060 per 1K tokens

**Llama 3.1 70B:**
- Input: $0.00099 per 1K tokens
- Output: $0.00132 per 1K tokens

**Claude 3.5 Sonnet:**
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens

### Example Costs

**Chat conversation (10 turns):**
- Llama 8B: ~$0.01-0.02
- Llama 70B: ~$0.03-0.05
- Claude: ~$0.10-0.15

**Quiz session (10 questions):**
- Llama 70B with RAG: ~$0.05-0.08
- Includes longer prompts (RAG context)

**Monthly usage (1 hour/day):**
- Llama 8B: ~$5-10/month
- Llama 70B: ~$15-25/month
- Claude: ~$50-75/month

**Free tier:** AWS Bedrock does NOT have a free tier, but costs are low for testing.

---

## Troubleshooting

### AccessDeniedException

**Error:** `An error occurred (AccessDeniedException) when calling the InvokeModel operation`

**Solution:**
```bash
# Check IAM permissions
aws iam list-attached-user-policies --user-name bedrock-user

# Should show: AmazonBedrockFullAccess

# If missing, attach policy:
aws iam attach-user-policy \
    --user-name bedrock-user \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### ValidationException

**Error:** `An error occurred (ValidationException) when calling the InvokeModel operation: The provided model identifier is invalid`

**Solution:**
```bash
# Check model ID spelling
# Correct IDs:
# - meta.llama3-8b-instruct-v1:0
# - us.meta.llama3-1-70b-instruct-v1:0
# - us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Verify model access
aws bedrock list-foundation-models --region us-east-1 | grep <model-id>
```

### ThrottlingException

**Error:** `An error occurred (ThrottlingException) when calling the InvokeModel operation: Too many requests`

**Solutions:**
1. Add cooldown in code (already implemented: 1.5s Llama, 3s Claude)
2. Request quota increase:
   ```
   Go to: AWS Service Quotas Console
   Service: Amazon Bedrock
   Quota: Invocations per minute
   Request increase
   ```

### ModelNotReadyException

**Error:** Model not ready or access not granted

**Solution:**
```bash
# Check model access status
# Go to: https://console.aws.amazon.com/bedrock/
# Navigate: Model access
# Status should be: "Access granted" (green)

# If "Access requested" (yellow): Wait a few minutes
# If "Access denied" (red): Not available in your region/account
```

### Region Errors

**Error:** Model not found in region

**Solution:**
```bash
# Always use us-east-1 for best model availability
aws configure set region us-east-1

# Or in code:
boto3.client('bedrock-runtime', region_name='us-east-1')
```

### Credential Errors

**Error:** Unable to locate credentials

**Solution:**
```bash
# Check credentials file
cat ~/.aws/credentials
# Should contain:
# [default]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...

# If missing, run:
aws configure
```

---

## Security Best Practices

### 1. Never Commit Credentials

```bash
# Ensure .gitignore includes:
.aws/
credentials
config
*.pem
*.key

# Check before committing:
git status
# Should NOT show .aws/ files
```

### 2. Use IAM Roles (Production)

For production deployments:
- Create IAM role instead of user
- Attach role to EC2/IoT device
- No credentials needed on device

### 3. Rotate Access Keys

```bash
# Every 90 days:
# 1. Create new access key
# 2. Update ~/.aws/credentials
# 3. Test
# 4. Delete old access key
```

### 4. Monitor Usage

```bash
# Enable CloudWatch billing alerts
# Go to: AWS Billing Console → Preferences
# Enable: "Receive Billing Alerts"

# Create alert:
# Metric: EstimatedCharges
# Threshold: $10 (or your preferred limit)
```

---

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Boto3 Bedrock Guide](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html)
- [Meta Llama on Bedrock](https://aws.amazon.com/bedrock/llama/)
- [Claude on Bedrock](https://aws.amazon.com/bedrock/claude/)

---

**Next:** [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) - Set up RAG system
