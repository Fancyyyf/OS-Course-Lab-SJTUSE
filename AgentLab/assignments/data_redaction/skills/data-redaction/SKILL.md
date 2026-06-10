---
name: data-redaction
description: Redact sensitive information from IT support tickets while preserving troubleshooting context.
---

## When To Use
Use this skill when you need to redact sensitive data from a support ticket and submit the sanitized version.

## Procedure
1. Call `read_ticket` with the target `ticket_id` to retrieve the ticket's raw content.
2. Identify and replace all sensitive data fields with placeholders (e.g., `[EMAIL]`, `[PHONE]`, `[STUDENT_ID]`, `[TOKEN]`, `[IP]`).
3. Retain the operational support context (e.g., "password reset" and "MFA enrollment").
4. Call `validate_redaction` with the draft redacted content.
5. Fix any identified issues and re-run validation until no issues remain.
6. Call `submit_redacted_ticket` to finalize the submission.

## Checklist
- **Email**: Replaced with a placeholder.
- **Phone**: Replaced with a placeholder.
- **Student ID**: Replaced with a placeholder.
- **Access Token**: Replaced with a placeholder.
- **Internal IP**: Replaced with a placeholder.
- **Keywords**: Exact phrases `"password reset"` and `"MFA enrollment"` must be preserved.
- **Validation**: Call `validate_redaction` before calling `submit_redacted_ticket`.
