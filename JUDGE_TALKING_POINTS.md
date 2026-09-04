# Judge Q&A and Talking Points

## The Core Identity & Final One-Liner
**"Any agent can call a payment API. RazorGuard makes sure the agent never gets to decide whether money should move."**

**What is the core innovation?**
**"The separation of AI decision-making from financial authority. The AI can recommend and orchestrate commerce, but Purchase Guard independently validates the transaction before Razorpay ever receives the order."**

---

## The 5 Golden Q&As (Memorize These)

**1. Why is this an AI agent?**
> "Because the user doesn't have to specify an exact product. The system understands natural-language intent, normalizes constraints, searches the catalog and ranks products to fulfill the user's goal."

**2. What does the AI control?**
> "Intent understanding, discovery and product ranking. It does not have financial authority."

**3. How do you prevent price manipulation?**
> "The frontend price isn't trusted. The server retrieves the authoritative catalog price and recalculates the transaction before Razorpay order creation."

**4. What happens if someone changes ₹84,999 to ₹1?**
> "Purchase Guard detects the authoritative price mismatch, records `PRICE_TAMPERING_DETECTED`, blocks the transaction, and Razorpay order creation never occurs."

**5. What's your core innovation?**
> **"Separating non-deterministic AI decision-making from deterministic financial authorization."**

---

## Likely Judge Interruptions & Backup Answers

**6. Why can't the AI just bypass Purchase Guard?**
> "Because Purchase Guard is a separate server-side financial boundary. The AI's recommendation does not itself authorize a payment. The transaction must pass the server-side validation and explicit confirmation checks before Razorpay order creation."

**7. What happens if Gemini fails?**
> "The pipeline has a fallback path. If the primary AI intent parsing fails, the system can fall back to catalog keyword search so the user can still continue shopping."

**8. How could this be extended to production?**
> "The production infrastructure would change, but the security boundary would remain: AI intelligence stays separate from server-side financial authorization."

**9. Explain RazorGuard in one sentence.**
> **"RazorGuard is an AI commerce agent that can understand shopping intent and recommend products, while a separate server-side Purchase Guard ensures the AI can never independently authorize an unsafe or tampered payment."**
