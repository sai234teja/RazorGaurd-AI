# RazorGuard AI - Architecture

RazorGuard AI implements a strict separation of concerns, dividing Agentic Commerce Intelligence from Financial Authority.

## Core Flow

```mermaid
flowchart TD
    %% Entities
    U[Human Buyer]
    B2A[External AI Buyer]
    
    %% AI Commerce Layer
    subgraph AI_Intelligence [AI Commerce Intelligence]
        direction TB
        A[Gemini Intent Parser]
        C[Catalog Search & Universal Ranker]
        R[Product Recommendation]
        A --> C --> R
    end
    
    %% B2A Manifest
    M[Agent-Readable Manifest\n/.well-known/agentic-commerce.json]
    
    %% App Orchestration
    O[Application Orchestration\nCart Management]
    E[Explicit User Confirmation]
    
    %% Security Boundary
    subgraph Security_Boundary [Financial Authority]
        direction TB
        PG{Purchase Guard}
        DB[(Authoritative Server Pricing SQLite)]
        PG -.->|Validates against| DB
    end
    
    %% Payment & Verification
    RZ[Razorpay Test Checkout]
    SV[Server-Side Signature Verification]
    DB2[(Order Lifecycle SQLite)]
    AT[Auditable Log]

    %% Connections
    U -->|Natural Language| AI_Intelligence
    B2A -->|Read-Only Discovery| M
    M -.->|Reads| DB
    
    R --> O
    O --> E
    E -->|Requests Checkout| PG
    
    PG -->|BLOCKED\nPrice Tampering| Block[Abort Transaction]
    PG -->|ALLOWED\nLOW RISK| RZ
    
    RZ -->|Payment Success| SV
    SV --> DB2
    DB2 --> AT
    
    %% Styling
    classDef default fill:#1a1e29,stroke:#48526a,stroke-width:1px,color:#e0e5eb
    classDef highlight fill:#281b3d,stroke:#a673ff,stroke-width:2px,color:#e0e5eb
    classDef security fill:#1e2b25,stroke:#35d07f,stroke-width:2px,color:#e0e5eb
    classDef blocked fill:#3b1c1c,stroke:#ff4d4d,stroke-width:2px,color:#e0e5eb
    
    class AI_Intelligence highlight
    class Security_Boundary security
    class Block blocked
```

## Architectural Tenets
1. **AI Discovery is Open:** The AI can rank, search, and parse intent. External agents can read the B2A manifest.
2. **Financial Authority is Gated:** The AI cannot authorize checkout. Purchase Guard independently evaluates the request.
3. **Server-Side Sovereignty:** The frontend price is never trusted. Purchase Guard deterministically recalculates the total using the server's SQLite database.
4. **B2A Does Not Bypass Security:** The agent-readable catalog is read-only. External agents must still pass through explicit confirmation and Purchase Guard to execute a payment.
