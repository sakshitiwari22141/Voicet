# Translation Accuracy Log

This log tracks known issues, user feedback, and improvements related to translation accuracy in the Voicet project.

## [2025-12-27] - Initial Improvements

### Issues Identified
- **Problem**: Individual segment translation.
- **Root Cause**: Whisper outputs short segments that may split sentences. Translating these individually loses context (e.g., gender, tense, subject).
- **Impact**: Inaccurate translations, unnatural phrasing.

### Improvements Implemented
- **Context Batching**: Implemented logic to group segments into larger chunks (up to a character limit) before passing to NLLB-200. This preserves sentence-level context.
- **Model Recommendation**: Documented the use of larger NLLB models (1.3B or 3.3B) for better results on high-resource languages.

### Pending Improvements
- [ ] Punctuation-based batching (grouping specifically by end-of-sentence markers).
- [ ] Custom terminology/glossary support.
- [ ] Language-specific preprocessing rules.

---
*Last Updated: 2025-12-27*
