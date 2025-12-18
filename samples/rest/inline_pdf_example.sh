#!/bin/bash
# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This example demonstrates how to use inline PDF data with the generative API

# Set default values for environment variables if they don't exist
MEDIA_DIR="${MEDIA_DIR:-$(dirname "$0")/../../third_party}"

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
  B64FLAGS="-b 0"
else
  B64FLAGS="--wrap=0"
fi

echo "[START text_gen_multimodal_two_pdf_inline]"
# Use temporary files to hold the base64 encoded pdf data
PDF_PATH_1=${MEDIA_DIR}/test.pdf
PDF_PATH_2=${MEDIA_DIR}/test.pdf

TEMP_1_B64=$(mktemp)
trap 'rm -f "$TEMP_1_B64"' EXIT
base64 $B64FLAGS $PDF_PATH_1 > "$TEMP_1_B64"

TEMP_2_B64=$(mktemp)
trap 'rm -f "$TEMP_2_B64"' EXIT
base64 $B64FLAGS $PDF_PATH_2 > "$TEMP_2_B64"

# Use a temporary file to hold the JSON payload
TEMP_JSON=$(mktemp)
trap 'rm -f "$TEMP_JSON"' EXIT

cat > "$TEMP_JSON" << EOF
{
  "contents": [{
    "role": "user",
    "parts":[
      {"text": "Extract the pet names, type and ages from these documents."},
      {
        "inlineData": {
          "mimeType":"application/pdf",
          "data": "$(cat "$TEMP_1_B64")"
        }
      },
      {
        "inlineData": {
          "mimeType":"application/pdf",
          "data": "$(cat "$TEMP_2_B64")"
        }
      }
    ]
  }],
  "systemInstruction": {
    "parts": [
      {"text": "Extract the pet names and ages from these documents and return them in the following JSON format:

                Pet = {\"name\": str, \"type\": str, \"age\": int}
                Return: list[Pet]"
      }
    ]
  },
  "generationConfig": {
    "temperature": 0.2,
    "topP": 0.95,
    "topK": 40,
    "maxOutputTokens": 1000,
    "responseMimeType": "application/json"
  }
}
EOF

curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GOOGLE_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d "@$TEMP_JSON" 2> /dev/null
