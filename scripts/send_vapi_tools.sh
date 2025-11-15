#!/bin/bash
# Send each tool from vapi_tools_config.json to VAPI API
#
# Usage:
#   bash scripts/send_vapi_tools.sh

VAPI_API_KEY="13c20c0e-acd5-4ccc-a617-0bcf1e95a6de"
VAPI_BASE_URL="https://api.vapi.ai"
CONFIG_FILE="vapi_tools_config.json"

echo "============================================================"
echo "Sending VAPI Tools from JSON Config"
echo "============================================================"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found. Installing or using Python alternative..."
    USE_PYTHON=true
else
    USE_PYTHON=false
fi

# Function to send tool using Python (if jq not available)
send_tool_python() {
    local tool_index=$1
    python3 << EOF
import json
import sys
import subprocess

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

tool = config['tools'][$tool_index]
tool_name = tool['function']['name']

print(f"Sending tool: {tool_name}...")

# Convert to JSON string
tool_json = json.dumps(tool)

# Send via curl
cmd = [
    'curl', '-X', 'POST', '$VAPI_BASE_URL/tool',
    '-H', f'Authorization: Bearer $VAPI_API_KEY',
    '-H', 'Content-Type: application/json',
    '-d', tool_json,
    '-s', '-w', '\nHTTP Status: %{http_code}\n'
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"Error: {result.stderr}", file=sys.stderr)
EOF
}

# Function to send tool using jq
send_tool_jq() {
    local tool_index=$1
    local tool_json=$(jq -c ".tools[$tool_index]" "$CONFIG_FILE")
    local tool_name=$(jq -r ".tools[$tool_index].function.name" "$CONFIG_FILE")
    
    echo "Sending tool: $tool_name..."
    
    curl -X POST "$VAPI_BASE_URL/tool" \
      -H "Authorization: Bearer $VAPI_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$tool_json" \
      -w "\nHTTP Status: %{http_code}\n" \
      -s
    
    echo ""
}

# Send all 4 tools
for i in {0..3}; do
    echo "Tool $((i+1))/4:"
    if [ "$USE_PYTHON" = true ]; then
        send_tool_python $i
    else
        send_tool_jq $i
    fi
    echo ""
done

echo "============================================================"
echo "✅ All tools sent!"
echo "============================================================"
echo ""
echo "Verify in VAPI dashboard: https://dashboard.vapi.ai"
echo ""

