set -eu

echo "[START function_calling]"
# [START function_calling]

cat > tools.json << EOF
{
  "function_declarations": [
    {
      "name": "enable_lights",
      "description": "Turn on the lighting system."
    },
    {
      "name": "set_light_color",
      "description": "Set the light color. Lights must be enabled for this to work.",
      "parameters": {
        "type": "object",
        "properties": {
          "rgb_hex": {
            "type": "string",
            "description": "The light color as a 6-digit hex string, e.g. ff0000 for red."
          }
        },
        "required": [
          "rgb_hex"
        ]
      }
    },
    {
      "name": "stop_lights",
      "description": "Turn off the lighting system."
    }
  ]
} 
EOF

curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d @<(echo '
  {
    "systemInstruction": {
      "parts": {
        "text": "You are a helpful lighting system bot. You can turn lights on and off, and you can set the color. Do not perform any other tasks."
      }
    },
    "tools": ['$(cat tools.json)'],

    "toolConfig": {
      "functionCallingConfig": {"mode": "auto"}
    },

    "contents": {
      "role": "user",
      "parts": {
        "text": "Turn on the lights please."
      }
    }
  }
') 2>/dev/null |sed -n '/"content"/,/"finishReason"/p'
# [END function_calling]
