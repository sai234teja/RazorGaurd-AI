# RazorGuard AI Commerce Agent — Final Demo Script
**Duration:** 3–5 Minutes

---

## MOMENT 1 — AI BUYING AGENT
**Goal:** Demonstrate how AI bridges natural language with strict catalog constraints.

**Action:**
1. Open the chat interface.
2. Type the query: `"I need a laptop for coding under ₹80,000 with at least 16GB RAM and 512GB storage."`
3. Hit Send.

**What to Show:**
- The system parses the natural-language request into a strict intent payload.
- Hard constraints (Price <= 80,000, RAM >= 16GB, Storage >= 512GB, Category = laptops) are strictly enforced against the catalog database.
- The UI renders the ranked recommendations, explaining *why* the products fit the coding use case.
- Point to the **Judge Mode** diagnostic panel highlighting the extracted constraints.

**Presenter Message:**
> *"The AI understands the shopper's intent, but the catalog remains the source of truth."*

---

## MOMENT 2 — FINANCIAL BOUNDARY
**Goal:** Demonstrate that the AI has zero financial authority and the server protects the transaction.

**Action:**
1. Click the "Buy Now" button on one of the recommended laptops.
2. Proceed through the checkout modal to trigger Razorpay Test Mode.
3. Complete the mock payment.

**What to Show:**
- The checkout modal displays the product.
- The **Purchase Guard** interceptor runs on the server, validating that the requested item exists and re-fetching the *authoritative* price from the database.
- A secure Razorpay Order is created strictly using the server-calculated amount.
- The payment verification succeeds, generating a cryptographic audit event.
- Point to the **Judge Mode** panel confirming the signature verification.

**Presenter Line:**
> *"The AI recommends; the server authorizes."*

**(Optional: Tampering Scenario if time permits)**
**Action:** Use browser DevTools to change the price in the frontend before hitting "Buy Now".
**Explanation:** 
> *"Even if the client sends a manipulated total, the server recalculates the authoritative amount and rejects the mismatch before an unsafe Razorpay order is created."*

---

## MOMENT 3 — MERCHANT LOST SALE
**Goal:** Show how unfulfilled queries generate actionable merchant intelligence.

**Action:**
1. Type the query: `"I need a laptop with 32GB RAM and 1TB storage under ₹45,000."`
2. Hit Send.

**What to Show:**
- The system returns **0 exact matches** because the hard constraints (price and specs) contradict the existing catalog.
- The UI displays the *closest alternatives* clearly separated from exact matches (e.g., a 32GB laptop for ₹90,000).
- The system logs a **Merchant Lost Sale Intelligence** audit event.
- Show the Judge Mode panel flagging a "catalog gap" or missed opportunity.

**Presenter Line:**
> *"A failed shopping request doesn't just become a dead end. RazorGuard turns it into merchant intelligence."*

---

## DEMO RECOVERY PLAN
If unexpected issues arise during the live presentation, follow these recovery steps gracefully:

- **AI Provider is Slow / Timeout:** "As you can see, we're waiting on the LLM API to respond with the intent payload. In production, this latency is hidden with skeleton loaders, but the architecture ensures the UI never hangs permanently." (Wait up to 10s, then hit refresh and resend).
- **Payment Modal Fails to Load:** "It appears the Razorpay test script is blocked by a network rule or extension. The architecture, however, has already enforced Purchase Guard on our backend to ensure a safe order payload was generated."
- **Browser Refresh Occurs Accidentally:** "Let's just jump right back in—our application is stateless, so we can immediately re-run the intent."
- **A Product Link is Unavailable:** "Notice how this button says 'Product link unavailable.' Our system intentionally disables broken or unverified links to protect the user experience rather than blindly trusting flawed data."

**Golden Rule:** The demo must never depend on making exaggerated claims. If a glitch occurs, narrate *why* the guardrails keep the system safe.
