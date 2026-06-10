---
name: patch-review
description: Review code patches for security vulnerabilities like path traversal and workspace boundary escapes.
---

## When To Use
Use this skill when asked to review a pending patch diff, identify security risks, and submit a structured review response.

## Procedure
1. Call `read_diff` to retrieve the pending patch diff.
2. If necessary, call `read_patch_file` to review context files.
3. Analyze the patch for security vulnerabilities, especially verifying path handling:
   - Check if files are read/written using raw/user-controlled paths without safety limits.
   - Look for path traversal risks where paths can escape workspace boundaries.
4. If path handling is unsafe:
   - Select `"request_changes"` as the verdict.
   - Formulate comments that identify the `"path traversal"` risk.
   - Recommend resolving paths using `"workspace.resolve"`.
   - Request adding a regression `"test"`.
5. Call `submit_review` to record the verdict and comments.

## Checklist
- **Verdict**: Must be `"request_changes"` if path traversal is found.
- **Vulnerability**: Comments must explicitly mention `"path traversal"` or `"workspace"` boundaries.
- **Remediation**: Comments must explicitly recommend `"workspace.resolve"`.
- **Testing**: Comments must explicitly request a regression `"test"`.
