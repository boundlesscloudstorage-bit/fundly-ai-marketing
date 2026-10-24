"""In-memory mock records. No persistence or external services are used."""

OVERVIEW = {
    "brand_id": "fundly",
    "brand_name": "Fundly",
    "period": "October 2026",
    "metrics": [
        {"label": "Active campaigns", "value": "03", "change": "+1 this month"},
        {"label": "Scheduled content", "value": "12", "change": "Across 3 channels"},
        {"label": "Engagement rate", "value": "6.8%", "change": "+1.2% vs last month"},
        {"label": "Estimated reach", "value": "24.6k", "change": "+18% this month"},
    ],
}

CAMPAIGNS = [
    {"id": "camp-001", "brand_id": "fundly", "name": "A little more room to grow", "channel": "Instagram · Awareness", "status": "In progress", "progress": 72, "target_date": "2026-10-28"},
    {"id": "camp-002", "brand_id": "fundly", "name": "Make payday feel lighter", "channel": "LinkedIn · Education", "status": "In progress", "progress": 48, "target_date": "2026-10-30"},
    {"id": "camp-003", "brand_id": "fundly", "name": "Your next chapter starts here", "channel": "Email · Consideration", "status": "Planning", "progress": 26, "target_date": "2026-11-04"},
]

CONTENT = [
    {"id": "post-001", "brand_id": "fundly", "channel": "Instagram", "title": "Small steps. Big plans.", "body": "Big plans don’t need big leaps. Sometimes it’s one small step, a little breathing room, and the confidence to keep going. Wherever you’re headed, we’re rooting for you. 🌱", "status": "Scheduled", "scheduled_for": "2026-10-24T09:30:00-06:00"},
    {"id": "post-002", "brand_id": "fundly", "channel": "LinkedIn", "title": "A fresh start, on your terms", "body": "Financial confidence is built in everyday choices that move you closer to what matters.", "status": "Scheduled", "scheduled_for": "2026-10-27T12:00:00-06:00"},
    {"id": "draft-001", "brand_id": "fundly", "channel": "Instagram", "title": "Your goals, your pace", "body": "Your goals, your pace. A sample AI-generated marketing draft for inspiration.", "status": "Draft", "scheduled_for": "2026-10-29T10:15:00-06:00"},
]
