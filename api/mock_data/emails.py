MOCK_EMAILS = [
    {
        "id": "email_001",
        "from_address": "thundoss@gmail.com",
        "from_company": "Apex Logistics",
        "subject": "URGENT: Login failures affecting all warehouse managers",
        "body": """Hi Support Team,

We're experiencing critical login failures across all 47 of our warehouse manager accounts since approximately 08:15 AM CST. Our operations team cannot access the dashboard and our shipment processing is completely halted.

This is causing significant business impact — we have 12 active shipments that need to be processed in the next 2 hours or we face penalty fees.

Error message displayed: "Authentication service unavailable - ERR_AUTH_503"

We've already tried:
- Clearing browser cache and cookies
- Using different browsers (Chrome, Firefox, Edge)
- Different network connections

None of these workarounds helped. The issue appears to be on your end.

Please escalate this immediately. Our SLA agreement specifies P0 response within 15 minutes.

Best regards,
Marcus Reid
VP Operations, Apex Logistics
+1 (312) 555-0147""",
    },
    {
        "id": "email_002",
        "from_address": "it-alerts@titanretail.com",
        "from_company": "Titan Retail",
        "subject": "[CRITICAL] Payment gateway down — checkout completely broken",
        "body": """To the Meridian SaaS Support Team,

Our payment integration has been returning 500 errors since 07:45 AM PST. All customer checkout flows are failing and we are losing revenue every minute.

Error trace from our logs:
  MeridianPaymentClient.charge() → HTTP 500
  Request ID: req_8f3a2b9c1d

Affected endpoints:
  - /api/v2/payments/charge
  - /api/v2/payments/refund

This is a SEV-1 incident for us. We need a war room set up immediately.

— Titan Retail IT Team""",
    },
]

MOCK_CONTACTS = {
    "felix.makinda": {
        "name": "Felix Makinda",
        "email": "mogendifelix6@gmail.com",
        "role": "Engineering Manager",
        "slack_handle": "@felix.makinda",
        "jira_username": "felix.makinda",
        "is_oncall": False,
    },
    "denis.gathondu": {
        "name": "Denis Gathondu",
        "email": "thundoss@gmail.com",
        "role": "Senior SRE",
        "slack_handle": "@denis.gathondu",
        "jira_username": "denis.gathondu",
        "is_oncall": True,
    },
    "yaqub.adesola": {
        "name": "Yaqub Adesola",
        "email": "yaqub.adesola@gmail.com",
        "role": "Backend Engineer",
        "slack_handle": "@yaqub.adesola",
        "jira_username": "yaqub.adesola",
        "is_oncall": False,
    },
    "briah.mukhwaya": {
        "name": "Briah Mukhwaya",
        "email": "himora@gmail.com",
        "role": "Backend Engineer",
        "slack_handle": "@briah.mukhwaya",
        "jira_username": "briah.mukhwaya",
        "is_oncall": False,
    },
}

ONCALL_ENGINEER = MOCK_CONTACTS["denis.gathondu"]
