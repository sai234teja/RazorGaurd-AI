# RazorGuard AI - Demo Script (3–5 Minutes)

## Core Story
*"Any agent can call a payment API. RazorGuard makes sure the agent never gets to decide whether money should move."*

---

### 0:00–0:30 | The Problem
"Hello! AI agents can increasingly shop on behalf of users, but giving an LLM unchecked authority over payments creates a massive trust problem. So, we separated commerce intelligence from financial authority."

### 0:30–1:00 | The Solution & Architecture
"Our architecture is cleanly split. Gemini handles intent understanding and product discovery. The commerce pipeline searches and ranks products. But when money is involved, the request crosses a separate security boundary called Purchase Guard. The AI does not get to decide whether money moves."

### 1:00–2:00 | AI Shopping Experience (Happy Path)
*Action: Type "I need a laptop for everyday use under ₹80,000" in the dashboard.*
"Instead of requiring an exact product query, the agent understands natural-language constraints and ranks products from our catalog. This visualization shows the execution stages from intent parsing through recommendation."
*Action: Add the top laptop to the cart and click Proceed to Protected Checkout.*

### 2:00–2:30 | Purchase Guard + Razorpay Payment
"Now we reach the security boundary. Purchase Guard independently validates the transaction against authoritative server-side data. Only after this validation passes do we create the Razorpay test order."
*Action: Show the LOW RISK / ALLOWED Purchase Guard screen.*
*Action: Complete the Razorpay Test Payment (Netbanking > Any Bank).*

### 2:30–3:15 | The Security Attack Demonstration
"But a successful payment isn't enough. Let's test what happens when the client is compromised."
*Action: Simulate tampering the cart total from the actual price (e.g., ₹84,999) to ₹1 using DevTools or interception.*
"The client is now claiming that this product costs ₹1. Purchase Guard intercepts it and detects the authoritative price mismatch. It blocks it."
*Action: Show PRICE_TAMPERING_DETECTED error.*
"The important part is that Razorpay is never called with this fraudulent transaction."

### 3:15–3:45 | Verification, Order Lifecycle & Audit Trail
*Action: Show successful Order Success screen, then navigate to My Orders -> View Details.*
"For a legitimate payment, the server verifies the Razorpay signature and validates the amount and currency before marking the order paid. The completed order and its security decision are persisted, giving us an auditable record of the transaction."

### 3:45–4:00 | Closing Statement
"So RazorGuard lets AI participate in agentic commerce without giving the AI financial authority. The AI handles commerce intelligence, Purchase Guard handles financial authority, and Razorpay handles the payment. That's how we make agentic commerce trustworthy."
