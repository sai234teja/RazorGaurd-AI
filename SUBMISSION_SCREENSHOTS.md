# RazorGuard AI - Recommended Screenshots for Submission

Capture the following 7 screenshots to create a powerful visual narrative for the judges. Do not modify the UI to capture these; use the actual application.

## 1. Main AI Shopping Dashboard
- **What should be visible:** The hero section, the search input box populated with a natural language query (e.g., "I need a laptop for everyday use under ₹80k"), and the modern dark-mode aesthetic.
- **Why it matters:** Establishes the agentic commerce premise—the user is providing a goal, not selecting filters.
- **What should NOT be visible:** Technical debug info or DevTools.
- **Suggested Title:** Conversational Discovery: Goal-Oriented AI Shopping

## 2. Live AI Commerce Pipeline
- **What should be visible:** The glowing SSE "Agent Pipeline" visualization showing active steps (Intent Parser → Normalizer → Ranker) above the product recommendations.
- **Why it matters:** Proves the system is "explainable" (a key Track 01 requirement) and makes the AI's complex backend processing tangible to a non-technical judge.
- **What should NOT be visible:** Raw JSON or unstyled logs.
- **Suggested Title:** Explainable AI: Real-Time Execution Pipeline

## 3. Purchase Guard (LOW RISK / ALLOWED)
- **What should be visible:** The checkout modal showing the "Purchase Guard" section with a green "LOW RISK" score, "ALLOWED" decision, and the checklist of passed server-side validations (amount, currency, provider).
- **Why it matters:** Visually demonstrates the core innovation—the deterministic security boundary gating the payment.
- **What should NOT be visible:** The Razorpay modal (this happens *before* Razorpay).
- **Suggested Title:** Financial Authority: Server-Side Purchase Guard Validation

## 4. Razorpay Test Checkout
- **What should be visible:** The official Razorpay Test Mode checkout UI overlaying the RazorGuard dashboard.
- **Why it matters:** Proves real integration with the sponsor's API and SDK.
- **What should NOT be visible:** Real credit card numbers (use Razorpay test credentials).
- **Suggested Title:** Execution: Seamless Razorpay Integration

## 5. Successful Verified Order
- **What should be visible:** The "Order Success" receipt showing the Razorpay Payment ID and the "Verified" badge.
- **Why it matters:** Demonstrates the closed-loop server-side signature verification process.
- **What should NOT be visible:** The cart UI (it should be hidden/cleared).
- **Suggested Title:** Closed Loop: Cryptographic Server-Side Verification

## 6. My Orders / Order Details
- **What should be visible:** The Order Details screen showing the auditable log of a previous transaction, including the stored Purchase Guard risk report.
- **Why it matters:** Proves the application meets the "Audit Trail" requirement of Track 01 and persists transaction data safely.
- **What should NOT be visible:** Overlapping elements or unformatted JSON.
- **Suggested Title:** Accountability: Persistent Order History & Audit Trail

## 7. Price Tampering BLOCKED
- **What should be visible:** The checkout modal showing a red Purchase Guard block with `PRICE_TAMPERING_DETECTED`, likely alongside a Cart Total that has been maliciously altered to ₹1.
- **Why it matters:** The ultimate proof of the project's security claim. Shows that RazorGuard gracefully handles failure and blocks unauthorized money movement.
- **What should NOT be visible:** The Razorpay checkout (it must be proven that Razorpay was never invoked).
- **Suggested Title:** Graceful Failure: Blocking Fraudulent Transactions
