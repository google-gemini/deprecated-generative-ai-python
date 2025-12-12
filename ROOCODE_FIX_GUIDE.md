# Quick Fix Guide for Roocode Users

## Problem

Getting "Requests Error" or "Service Unavailable" when using Gemini with Roocode in VSCode.

## Root Cause

The model name **"Gemini-3-Pro-Preview"** does not exist. This is not a valid Google Gemini model name.

## Solution (2 minutes)

### Step 1: Open Roocode Settings

1. Open VSCode Settings: `Ctrl+,` (Windows/Linux) or `Cmd+,` (Mac)
2. Type "Roocode" in the search box
3. Look for the model/API configuration section

### Step 2: Update Model Name

Change the model name from:
```
❌ Gemini-3-Pro-Preview
```

To one of these **valid** model names:
```
✅ gemini-2.0-flash          (recommended - newest & fast)
✅ gemini-1.5-pro            (more capable for complex tasks)
✅ gemini-1.5-flash          (fast & efficient)
```

### Step 3: Verify API Key

Make sure your Google AI API key is correctly set:

- **Get your API key:** https://aistudio.google.com/app/apikey
- **In Roocode settings:** Look for "API Key" field
- **Format:** Should be a long string like `AIzaSy...`

### Step 4: Restart

1. Save settings
2. Reload VSCode window: `Ctrl+Shift+P` → "Reload Window"
3. Try using Roocode again

## Still Not Working?

### Check 1: API Key Validity

Run this command to test your API key:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash?key=YOUR_API_KEY"
```

If you get an error, your API key might be invalid or expired.

### Check 2: Network Connection

Make sure you can reach Google's API:
```bash
ping generativelanguage.googleapis.com
```

### Check 3: Roocode Version

- Update Roocode to the latest version
- Check Roocode's GitHub issues: https://github.com/roocode/roocode (or their official repo)

## Model Name Reference

| Model Name | Best For | Speed |
|------------|----------|-------|
| `gemini-2.0-flash` | Most use cases, newest | ⚡⚡⚡ Very Fast |
| `gemini-1.5-flash` | General tasks | ⚡⚡⚡ Very Fast |
| `gemini-1.5-pro` | Complex reasoning, analysis | ⚡⚡ Fast |
| `gemini-1.5-flash-latest` | Auto-updates to latest flash | ⚡⚡⚡ Very Fast |
| `gemini-1.5-pro-latest` | Auto-updates to latest pro | ⚡⚡ Fast |

### ❌ Invalid Model Names (Will Cause Errors)

- `Gemini-3-Pro-Preview` ← **This doesn't exist!**
- `gemini-3.0`
- `gemini-pro` (old naming, use `gemini-1.5-pro` instead)
- `gpt-4` (that's OpenAI, not Google)

## Need More Help?

- **Gemini API Documentation:** https://ai.google.dev/gemini-api/docs
- **Community Forum:** https://discuss.ai.google.dev/c/gemini-api/4
- **Get API Key:** https://aistudio.google.com/app/apikey
- **Report Roocode Issues:** Contact Roocode support directly

## For Developers

If you're developing a tool like Roocode that integrates with Gemini:

1. **Validate model names** before making API calls
2. **Provide a dropdown** with valid model names (not free text)
3. **Handle errors gracefully** with clear messages
4. **Use the new SDK:** https://github.com/googleapis/python-genai

Example valid model check:
```python
VALID_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest"
]

if user_selected_model not in VALID_MODELS:
    # Fetch from API to get current list
    models = fetch_available_models()
    # Show error with valid options
```

---

**Last Updated:** December 2024  
**Issue Reference:** #759 in google-gemini/deprecated-generative-ai-python

