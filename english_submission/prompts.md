# Prompts Used

## Summarization Prompt

**Role:** You are a careful NLP analyst preparing a concise report for the Student Services Office manager.

**Task:** Summarize the campus shuttle tracking app feedback in the input dataset. Identify the overall pattern, top themes, user impacts, positive feedback, high-priority risks, missing or ambiguous information, and practical next steps.

**Context:** The dataset contains 12 raw comments from app reviews, help-desk emails, surveys, and chat transcripts. Some records contain several issues, mixed sentiment, or user speculation.

**Input data:** Use records R01–R12 in the “Raw Dataset” section below.

**Output format:** Follow the exact Markdown structure below. Include at least three rows in the Top Themes table and cite record IDs for every theme, positive point, and risk.

```text
# Campus Shuttle App Feedback Summary
## 1. One-Sentence Overview
## 2. Top Themes
| Theme | Evidence IDs | User Impact | Recommended Action |
|---|---|---|---|
## 3. Positive Feedback
## 4. High-Priority Risks
## 5. Missing or Ambiguous Information
## 6. Recommended Next Steps
```

**Rules:**
- Use only information explicitly present in the raw notes.
- Do not invent names, causes, technical explanations, dates, policies, or solutions.
- Treat user speculation as speculation, not as an established cause.
- Support every substantive claim with one or more record IDs.
- State uncertainty and missing information explicitly.
- Recommend investigation or verification rather than asserting an unsupported fix.
- Keep the result concise, manager-facing, and scannable in under two minutes.

## Extraction Prompt

**Role:** You are a careful NLP information-extraction analyst.

**Task:** Convert every input record into one structured JSON object and calculate dataset-level insights.

**Context:** The data describe student feedback about a pilot campus shuttle tracking app. A record may mention multiple concerns; select the primary evidence-supported issue category. Apply urgency consistently: high for stated safety, accessibility, payment, or service-access consequences; medium for unresolved functional or readability problems; low for enhancement requests without a stated immediate harm.

**Input data:** Use records R01–R12 in the “Raw Dataset” section below.

**Output format:** Return only one parseable JSON object with top-level keys `records` and `dataset_level_insights`. Include all 12 records. Each record must have these keys in this order: `id`, `date`, `source`, `issue_category`, `sentiment`, `urgency`, `user_need`, `requested_action`, `evidence_quote`, `needs_follow_up`, and `missing_information`. The dataset-level object must contain `most_common_issue_categories`, `highest_priority_record_ids`, and `overall_sentiment`.

**Controlled vocabulary:**
- `source`: `App review`, `Help-desk email`, `Survey response`, or `Chat transcript`
- `issue_category`: `timing_accuracy`, `payment_refund`, `accessibility`, `app_bug`, `safety`, `privacy`, `feature_request`, `positive_feedback`, or `unclear`
- `sentiment`: `positive`, `mixed`, `negative`, or `unclear`
- `urgency`: `low`, `medium`, or `high`
- `overall_sentiment`: `positive`, `mixed`, `negative`, or `unclear`

**Rules:**
- Use only information in the input; never invent missing details or technical causes.
- Copy a short, exact supporting quote from each raw note.
- Use JSON `null` when a requested action or other value is unsupported.
- Put unresolved or absent details in `missing_information`; use an empty array only when no material detail is missing.
- Set `needs_follow_up` to true for unresolved problems or requests and false only for pure positive feedback.
- Do not convert R08’s speculation about untranslated names into a fact.
- Use double quotes for all keys and strings, no comments, no trailing commas, and no Markdown code fence.
- Before returning, verify parseability, IDs R01–R12 exactly once, controlled labels, and evidence support.

## Raw Dataset

- **R01 — App review — 2026-04-12:** “The bus arrival time is usually okay in the morning, but after 6 pm it is off by 15–20 minutes. I missed my lab section twice because the app said the shuttle was 3 minutes away.”
- **R02 — Help-desk email — 2026-04-13:** “I was charged twice for the same monthly student shuttle pass. One charge says pending and one posted. Please refund the duplicate charge. I attached a screenshot, but I do not know which transaction ID you need.”
- **R03 — Survey response — 2026-04-14:** “The app is useful, but the color contrast is hard to read outside. The green text on gray background is almost invisible in sunlight.”
- **R04 — Chat transcript — 2026-04-15:** “Driver was friendly and helped me with my bag. The tracker froze at 7:42 for about ten minutes, then jumped to arrived. No crash message, just frozen.”
- **R05 — App review — 2026-04-15:** “I like the notification when the shuttle is nearby. Can you add an option to notify me 10 minutes before arrival instead of only 2 minutes?”
- **R06 — Help-desk email — 2026-04-16:** “The wheelchair-accessible shuttle icon is not reliable. It showed accessible at North Gate, but the shuttle that arrived did not have a working ramp. I had to wait for the next one.”
- **R07 — Survey response — 2026-04-16:** “It asks for location permission all the time. I understand location is needed while using the app, but why does it ask in the background? Please explain what data are stored.”
- **R08 — Chat transcript — 2026-04-17:** “My route disappeared after I changed my phone language to Spanish. When I switched back to English, the route came back. Maybe the route names are not translated?”
- **R09 — App review — 2026-04-18:** “The shuttle is late at night near the dorms. The app still says on time, but students are waiting outside for a long time. This feels unsafe after dark.”
- **R10 — Survey response — 2026-04-18:** “Overall much better than the old PDF schedule. I can see live buses and stop names. The only confusing part is that ‘Arriving’ sometimes means at the previous stop, not my stop.”
- **R11 — Help-desk email — 2026-04-19:** “I bought a visitor day pass for my parent, but the QR code never loaded. We tried Wi-Fi and cellular. The payment went through, but the app just showed a spinning circle.”
- **R12 — App review — 2026-04-20:** “Please add a simple text message option. Some students do not want to install another app just to know if the shuttle is delayed.”
