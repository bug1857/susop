# SustainOCPM: Risk Mitigation Plan

This document details the mitigation and fallback protocols for the top nine implementation risks.

---

## 1. Risk Matrix

| Risk Category | Impact | Likelihood | Mitigation Strategy | Fallback Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **Quota Limits** | High | High | Implement local caching for frequent lookup queries; batch API requests. | Failover to local open-source models (e.g., Llama 3) if external API limits are exceeded. |
| **Ambiguous Requirements** | Medium | Medium | Align requirements directly with the Indo-Swiss grant evaluation and SEBI BRSR specifications. | Revert ambiguous calculations to match raw SEBI BRSR compliance templates. |
| **Hardcoded Analytics** | Medium | Medium | Drive carbon calculation algorithms through database-stored configuration matrices. | Inject configuration overrides dynamically via JSON environment variables. |
| **AI Hallucinations** | High | High | Restrict LLM responses using rigorous pgvector RAG grounding and Natural Language constraints. | Return pre-formulated warning messages and direct links to source PDFs when AI confidence drops. |
| **Data Privacy** | High | Low | Enforce strict PostgreSQL Row-Level Security (RLS) and encrypt supplier files. | Instantly isolate any compromised tenant and reset security gateways. |
| **Scalability** | High | Medium | Decouple telemetry ingestion from graph generation using asynchronous queue buffers. | Run graph discovery algorithms in scheduled batches rather than in real-time. |
| **Documentation Drift** | Low | Medium | Enforce strict master architecture index validation checks during CI/CD cycles. | Generate auto-generated API routing tables directly from the codebase. |
| **UX Complexity** | Medium | High | Follow the Executive-First UI principles: render summarized metrics by default. | Provide a standard tabular raw data view toggle to bypass advanced visualization errors. |
| **Insufficient Test Coverage**| Medium | Medium | Set a mandatory 85% unit test coverage threshold in the build pipeline. | Require manual developer sign-off for critical production releases. |
