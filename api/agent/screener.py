"""
LLM pre-screening step.
Runs a fast GPT-4o-mini call to classify whether an incoming email
represents a genuine production incident before triggering the full agent.
"""

import os

from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)

SCREENER_PROMPT = """\
You are an incident classification assistant for Meridian SaaS, a B2B SaaS platform.

Your job is to read an incoming email and decide whether it represents a genuine production incident that requires an immediate automated response.

A GENUINE INCIDENT is one or more of:
- A customer reporting that a core feature is broken, unavailable, or returning errors
- A customer reporting data loss, security concern, or compliance issue
- An automated alert from a monitoring system (PagerDuty, Datadog, etc.)
- An internal engineer reporting a production outage

NOT an incident:
- Sales inquiries, billing questions, feature requests
- General support questions that don't indicate a service outage
- Spam, marketing, newsletters
- Meeting invites, HR communications

Return ONLY valid JSON, no markdown, no explanation:
{
  "is_incident": true or false,
  "confidence": 0.0 to 1.0,
  "severity": "P0" | "P1" | "P2" | null,
  "affected_service": "short description or null",
  "reasoning": "one sentence explaining your decision"
}

Severity guide:
- P0: Complete outage, all users affected, revenue impact, data loss
- P1: Major feature broken, significant subset of users affected
- P2: Minor degradation, workaround exists, low user impact
"""


async def screen_email(
    subject: str,
    body: str,
    from_address: str,
    from_company: str = "",
    confidence_threshold: float = 0.70,
) -> dict:
    """
    Screen an email for incident classification.
    Returns the full screening result dict including is_incident, confidence,
    severity, affected_service, and reasoning.
    """
    email_text = f"From: {from_address}"
    if from_company:
        email_text += f" ({from_company})"
    email_text += f"\nSubject: {subject}\n\n{body[:2000]}"  # cap at 2000 chars

    response = await client.chat.completions.create(
        model=os.getenv("SCREENER_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SCREENER_PROMPT},
            {"role": "user", "content": email_text},
        ],
        temperature=0,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    import json

    raw = response.choices[0].message.content or "{}"
    result = json.loads(raw)

    # Enforce threshold
    confidence = float(result.get("confidence", 0))
    result["passes_threshold"] = (
        result.get("is_incident", False) and confidence >= confidence_threshold
    )
    result["threshold_used"] = confidence_threshold

    return result
