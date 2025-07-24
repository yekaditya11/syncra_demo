import json
from sheet_insights.config import client
from pathlib import Path
import os
import time


INSIGHT_PROMPT = """
You are a senior data analyst. Based on the following markdown table content, generate exactly five concise insights as a raw JSON array of strings.
You must be fully accurate with dates, figures, and trends — no assumptions or extrapolations.

Instructions:
- The table contains monthly data in left-to-right order from January to June. Use exact month names from the table when describing trends or numbers.
- Do NOT infer trends beyond June, and do NOT confuse column positions or assume patterns.
- Each insight must highlight patterns, trends, gaps, or performance observations strictly from the actual data.
- Use clear, factual, and precise language — avoid vague phrases like "the data shows" or "it can be seen".
- Do NOT include object wrappers or labels like "insight"; only return a plain JSON array of 5 strings.

Only return the JSON array — no markdown, no formatting, no explanations.

Example output:
[
  "80% of suppliers achieved on-time delivery in Q1, but only 60% in Q2, indicating a downward trend.",
  "One supplier reported a significantly higher defect rate, accounting for 45% of all defects.",
  "Turnaround times were consistent for most suppliers, averaging 2.3 hours.",
  "Safety incidents were concentrated in March, with 4 out of 5 occurring that month.",
  "Three suppliers have missing data for production volumes, limiting performance evaluation."
]
"""


def get_insights(markdown_text: str, sheet_name: str = ""):
    """Generate insights for a single sheet with optimized processing"""
    try:
        start_time = time.time()

        # Optimize the prompt for faster processing
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a helpful data analyst. Respond quickly and concisely."},
                {"role": "user", "content": INSIGHT_PROMPT + f"\n```\n{markdown_text}\n```"}
            ],
            temperature=0.0,
            max_tokens=800,  # Reduced from 1000 for faster processing
            timeout=30  # Add timeout to prevent hanging
        )

        api_time = time.time() - start_time
        print(f"⚡ API call for '{sheet_name}' took {api_time:.2f}s")

        reply = response.choices[0].message.content.strip()
        return json.loads(reply)

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error for '{sheet_name}': {e}")
        with open(f"{sheet_name}_raw_output.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        return None
    except Exception as e:
        print(f"❌ Error generating insights for '{sheet_name}': {e}")
        return None
