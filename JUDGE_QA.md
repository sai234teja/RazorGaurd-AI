# RazorGuard AI Commerce Agent — Judge Q&A

**1. What makes this different from a normal chatbot?**
Unlike a standard chatbot that relies on the LLM to generate unstructured text and product answers directly, RazorGuard uses the AI purely as a translation layer. The LLM extracts intent and constraints into a deterministic JSON payload. A hard-coded backend pipeline then executes this payload against an authoritative SQLite catalog. The AI never controls the final product data.

**2. Why is Razorpay important?**
Razorpay is used to execute the actual financial transaction securely. By integrating Razorpay with our server-side Purchase Guard, we prove that the checkout flow is isolated from the AI. The AI's job ends at the recommendation; Razorpay and our backend handle the money securely.

**3. Can the AI change the price?**
No. The AI has absolutely no authority over the price. Even if the AI hallucinates a price in the chat, the checkout system (Purchase Guard) fetches the authoritative price directly from the secure backend database before creating the Razorpay order. 

**4. What happens if the AI recommends the wrong product?**
Because the system filters products using strict SQL queries based on the extracted constraints, the AI cannot recommend a product that doesn't exist. If the intent parsing is slightly off, the worst case is an irrelevant recommendation, but it will still be a real, verifiable product from the catalog.

**5. What happens if the client tampers with the price?**
If a malicious user modifies the price in the frontend before checkout, Purchase Guard intercepts the request on the backend. It recalculates the total using the trusted database pricing. If the client's payload mismatches the server's authoritative calculation, the server rejects the request immediately, preventing an unsafe Razorpay order from being generated.

**6. How are hard constraints enforced?**
The AI is instructed to output JSON parameters (like `max_price`, `min_price`, `required_attributes`). The backend application takes these parameters and translates them into hard SQL `WHERE` clauses (e.g., `price <= ?`). Products that fail these clauses are strictly excluded from the "exact match" results.

**7. What happens when there is no product match?**
If the hard constraints filter out all products (e.g., asking for an impossibly cheap laptop), the system returns 0 exact matches. It then triggers a fallback query to find the "closest alternatives" by relaxing constraints, separating them visually for the user.

**8. How does this generate merchant value?**
When a query results in 0 exact matches, RazorGuard logs a "Merchant Lost Sale Intelligence" event. This audit trail tells merchants exactly what customers are searching for that the store cannot fulfill, allowing the merchant to identify catalog gaps and restock or introduce new products driven by real user demand.

**9. What exactly does Purchase Guard do?**
Purchase Guard is a deterministic backend middleware. When a checkout request is made, it intercepts the cart payload, looks up every item ID in the authoritative database, fetches the true price, calculates the final total, and validates the total against the client's request. It completely prevents price tampering and hallucinated products from entering the payment gateway.

**10. Is this autonomous?**
No. It is an interactive, human-in-the-loop shopping assistant. The AI parses the user's input and recommends actions, but the user must explicitly click "Buy Now" and authorize the payment. 

**11. Does this implement UAP/ACP?**
We apply the architectural philosophy of separating the reasoning engine (AI) from the execution engine (server/database), which conceptually aligns with safe agent design, but we do not claim this is a formal implementation of the Universal Agent Protocol (UAP) or Agent Control Protocol (ACP).

**12. What happens if Gemini fails?**
If the Gemini API times out or fails, the backend will catch the exception and return a graceful error message to the user, instructing them to try again later. The failure of the LLM simply pauses the assistant functionality; it does not compromise the database, catalog, or security of the application.

**13. What happens if all AI providers fail?**
The core commerce application (database, static assets, checkout flow) remains secure and isolated. Users would not be able to process natural language queries, but no financial or catalog systems would be compromised.

**14. How is payment verified?**
After a successful Razorpay transaction, the client sends the Razorpay payment ID and signature to the backend. The backend cryptographically verifies the signature using the Razorpay API secret. The order is only marked complete after this server-side cryptographic validation.

**15. Where is the source of truth for price?**
The source of truth for all pricing (and product data) is strictly the backend SQLite database (`commerce.db`). The frontend and the AI are always treated as untrusted clients.

**16. What is the role of the agent-readable manifest?**
The manifest serves as a machine-readable declaration of the catalog's structure and the rules of engagement. It ensures the AI understands how to format its JSON intent payload correctly so that the deterministic backend can map those intents to actual SQL queries.

**17. Why shouldn't the AI directly authorize payments?**
LLMs are probabilistic and susceptible to hallucinations and prompt injection. If an AI could authorize payments or dictate final checkout totals, a malicious user could trick the AI into applying a 100% discount or authorizing a charge without consent. 

**18. What prevents a recommendation from bypassing catalog constraints?**
The AI does not query the database directly. It only provides the parameters. The deterministic Python backend constructs and executes the SQL query. Therefore, the AI physically cannot inject unauthorized SQL or force the backend to return a product that violates the backend's strict filtering logic.
