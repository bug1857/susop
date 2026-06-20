import json

STRUCTURED_CONTRACT = """You are an Enterprise Sustainability Intelligence Copilot.
You MUST output your response EXACTLY following this structure (use these exact headings):

1. Executive Summary
(2-3 sentences, metric-first overview)

2. Root Causes
(bullet list, max 4, cite exact IDs/routes if applicable)

3. Business Impact
(quantified, include ESG score impact)

4. Recommended Actions
(numbered, with expected reduction %)

5. Expected Improvement
(specific KPI projections)

6. Confidence Level
(High/Medium/Low with percentage, e.g., "High (92%)")

Data Context:
{payload}
"""

class PromptRegistry:
    @staticmethod
    def get_prompt(request_type: str, payload: dict, quality_mode: str = "balanced") -> str:
        payload_str = json.dumps(payload, indent=2)
        base = STRUCTURED_CONTRACT.format(payload=payload_str)
        
        # Append Quality-specific instructions
        if quality_mode == "fast":
            base += "\n[Quality Instruction: fast mode. Output directly and concisely without extended reasoning. Limit response size to < 1024 tokens.]"
        elif quality_mode == "expert":
            base += "\n[Quality Instruction: expert mode. You MUST answer all 6 sections. Cite exact database IDs, keys, and metrics from the context payload. Maximum reasoning depth requested.]"
        else:
            base += "\n[Quality Instruction: balanced mode. Standard response template.]"
            
        return base
