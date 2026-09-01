---
name: frontend_runtime_qa
description: >-
  Troubleshooting and quality assurance skill for Vanilla JS Single-Page Applications (SPAs) and HTML/CSS/Chart.js frontends in FairPlay Simulator. Use this skill when modifying frontend UI components, debugging unresponsive buttons, diagnosing JavaScript parse/runtime errors, checking object key dot notations, validating window scope bindings, or inspecting browser initialization lifecycles.
---

# Frontend Runtime QA & Debugging Skill

This skill provides a systematic runbook for developing, refactoring, and debugging Vanilla JavaScript Single-Page Applications (SPAs) within FairPlay Simulator without causing silent runtime failures.

## 1. Syntax & Object Literal Guardrails

### Dot-Containing Object Keys
In JavaScript, bare identifiers cannot contain dots.
- ❌ **Forbidden:** `{ OVER_2.5: 1.85 }` -> Fatal `SyntaxError` at script parse time.
- ❌ **Forbidden:** `outcomes.OVER_2.5` -> Runtime `TypeError: Cannot read properties of undefined (reading '5')`.
- ✅ **Required:** `{ "OVER_2.5": 1.85 }` and `outcomes["OVER_2.5"]`.

### Window Function Bindings
When attaching functions to `window` for inline `onclick="..."` HTML triggers:
- ❌ **Forbidden:** Binding names that are not actually declared functions (`window.foo = foo;` where `foo` does not exist). This throws `Uncaught ReferenceError: foo is not defined` and aborts the entire script.
- ✅ **Required:** Verify each function declaration exists before binding to `window`.

## 2. Initialization Lifecycle Isolation

Always wrap asynchronous initialization tasks in defensive error boundaries:
```javascript
async function init() {
    try {
        if (typeof Chart !== "undefined") initChart();
    } catch (e) {
        console.warn("Chart init deferred:", e);
    }

    try {
        await fetchFixtures();
    } catch (e) {
        console.error("fetchFixtures failed:", e);
    }

    try {
        await handleAuthSession();
    } catch (e) {
        console.error("Auth failed:", e);
    }
}
```

## 3. Stale Session Recovery
If an authenticated API call returns `401`, `403`, or `404` (e.g. database reset while browser retains old JWT):
1. Clear `localStorage.removeItem("fp_auth_token")` and `localStorage.removeItem("fp_user")`.
2. Automatically provision a fresh guest session via `autoGuestLogin()`.
3. Never leave the UI stuck with stale balances or unauthenticated state.

## 4. Verification Steps
After making frontend modifications:
1. Verify no syntax errors exist in the inline `<script>` tags.
2. Verify all API endpoints return HTTP 200 with matching response models.
3. Run the full unit test suite: `python -m unittest discover tests -v`.
