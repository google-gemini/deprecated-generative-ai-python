set -eu

echo "json_controlled_generation"
# [START json_controlled_generation]
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-d '{
    "contents": [{
      "parts":[
        {"text": "List 5 popular cookie recipes"}
        ]
    }],
    "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "recipe_name": {"type":"STRING"},
            }
          }
        }
    }
}' 2> /dev/null | head
# [END json_controlled_generation]

echo "json_no_schema"
# [START json_no_schema]
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-d '{
    "contents": [{
      "parts":[
        {"text": "List a few popular cookie recipes using this JSON schema:

            Recipe = {\"recipe_name\": str}
            Return: list[Recipe]"
        }
      ]
    }],
    "generationConfig": { "responseMimeType": "application/json" }
}' 2> /dev/null | head
# [END json_no_schema]
