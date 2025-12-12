# Issue #759 Resolution: "Requests Error" with Roocode VSCode Extension

## Problem Summary

Users attempting to use "Gemini-3-Pro-Preview" with the Roocode VSCode extension are encountering "Requests Error" / "Service Unavailable" errors.

## Root Causes

### 1. Invalid Model Name
The model name **"Gemini-3-Pro-Preview"** does not exist. This is causing the API requests to fail.

**Valid model names include:**
- `gemini-2.0-flash` (recommended for most use cases - newest model)
- `gemini-1.5-flash`
- `gemini-1.5-flash-latest`
- `gemini-1.5-pro`
- `gemini-1.5-pro-latest`
- `gemini-2.0-flash-001`

### 2. Deprecated SDK
This repository (`google-gemini/deprecated-generative-ai-python`) is **deprecated** and will reach End-of-Life on **November 30, 2025**.

## Solutions

### Immediate Fix for Roocode Users

If you're using the Roocode VSCode extension:

1. **Update your model configuration in Roocode settings:**
   - Open VSCode Settings (Ctrl/Cmd + ,)
   - Search for "Roocode"
   - Find the model name setting
   - Change `Gemini-3-Pro-Preview` to a valid model name like:
     - `gemini-2.0-flash` (newest, recommended)
     - `gemini-1.5-pro` (more capable for complex tasks)
     - `gemini-1.5-flash` (faster, good for most tasks)

2. **Verify your API key is valid:**
   - Ensure your Google AI API key is correctly configured
   - Get your API key from: https://aistudio.google.com/app/apikey

### Long-term Recommendation: Migrate to New SDK

All users should migrate to the **new [Google Generative AI SDK](https://github.com/googleapis/python-genai)**:

1. **Uninstall the old SDK:**
   ```bash
   pip uninstall google-generativeai
   ```

2. **Install the new SDK:**
   ```bash
   pip install google-genai
   ```

3. **Update your code:**
   
   **Old SDK (deprecated):**
   ```python
   import google.generativeai as genai
   
   genai.configure(api_key="YOUR_API_KEY")
   model = genai.GenerativeModel("gemini-2.0-flash")
   response = model.generate_content("Hello")
   ```
   
   **New SDK (recommended):**
   ```python
   from google import genai
   
   client = genai.Client(api_key="YOUR_API_KEY")
   response = client.models.generate_content(
       model="gemini-2.0-flash",
       contents="Hello"
   )
   ```

4. **Full migration guide:**
   - https://ai.google.dev/gemini-api/docs/migrate

## How to List Available Models

To see all currently available models, use:

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

print("Models that support generateContent:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"  - {m.name}")
```

Or via REST API:
```bash
curl https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY
```

## For Third-Party Tool Developers (Roocode, etc.)

If you're developing tools that integrate with Google's Gemini API:

1. **Implement model name validation** before making API requests
2. **Provide users with a dropdown** of valid model names instead of free-text input
3. **Migrate to the new Google Gen AI SDK** for better long-term support
4. **Handle API errors gracefully** with clear user-facing error messages
5. **Keep model list updated** as new models are released

## Additional Resources

- **New SDK Repository:** https://github.com/googleapis/python-genai
- **Migration Guide:** https://ai.google.dev/gemini-api/docs/migrate
- **Gemini API Documentation:** https://ai.google.dev/gemini-api/docs
- **Community Forum:** https://discuss.ai.google.dev/c/gemini-api/4
- **Get API Key:** https://aistudio.google.com/app/apikey

## Status

- **Issue Type:** Configuration Error (Invalid Model Name)
- **Affected Component:** Third-party VSCode extension (Roocode)
- **SDK Status:** Deprecated (EOL: November 30, 2025)
- **Recommended Action:** Update model name + Migrate to new SDK

---

**Note:** This issue is not a bug in the SDK itself, but rather a configuration issue in the third-party Roocode extension using an invalid model name. Since this SDK is deprecated, users should migrate to the new Google Generative AI SDK for continued support.

