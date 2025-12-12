# Issue #759 Resolution: Gemini-3-Pro-Preview Error

## 🎯 Quick Answer

The model name **"Gemini-3-Pro-Preview" does not exist**. Use `gemini-2.0-flash` instead.

## 📚 Documentation Files

This directory contains complete resolution documentation for Issue #759:

1. **[ISSUE_759_SUMMARY.md](./ISSUE_759_SUMMARY.md)** - Start here!
   - Executive summary
   - Quick fix guide
   - All resources in one place

2. **[ROOCODE_FIX_GUIDE.md](./ROOCODE_FIX_GUIDE.md)** - For Roocode users
   - Step-by-step fix instructions
   - Troubleshooting tips
   - Valid model names reference

3. **[ISSUE_759_RESOLUTION.md](./ISSUE_759_RESOLUTION.md)** - Technical details
   - Root cause analysis
   - Migration guide to new SDK
   - For developers integrating Gemini API

4. **[verify_models.py](./verify_models.py)** - Verification tool
   - Test your API key
   - List available models
   - Verify connectivity

## ⚡ Quick Fix

### For Roocode Users (VSCode Extension)

1. Open VSCode Settings: `Ctrl+,` or `Cmd+,`
2. Search: "Roocode"
3. Find model name setting
4. Change to: `gemini-2.0-flash`
5. Save and reload VSCode

### Valid Model Names

✅ Use these:
- `gemini-2.0-flash` (recommended)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

❌ Don't use:
- `Gemini-3-Pro-Preview` (doesn't exist!)

## 🔧 Test Your Setup

```bash
# Set your API key
export GEMINI_API_KEY="your-api-key"

# Run verification script
python verify_models.py
```

## ⚠️ Important Notice

This SDK is **deprecated** and will reach End-of-Life on **November 30, 2025**.

**Migrate to new SDK:**
- Repository: https://github.com/googleapis/python-genai
- Migration Guide: https://ai.google.dev/gemini-api/docs/migrate

## 📖 Additional Resources

- **Get API Key:** https://aistudio.google.com/app/apikey
- **Documentation:** https://ai.google.dev/gemini-api/docs
- **Community Forum:** https://discuss.ai.google.dev/c/gemini-api/4

## 🤝 Contributing

Found this helpful? Have suggestions? Please contribute to the new SDK:
- https://github.com/googleapis/python-genai

---

**Issue:** #759  
**Status:** ✅ Resolved  
**Type:** Configuration Error (Invalid Model Name)  
**Date:** December 12, 2024

