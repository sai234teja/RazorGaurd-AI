import os

css_file = 'frontend/style.css'
css_styles = """
/* ==================================================
   INTENT GRID
   ================================================== */
.intent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
    margin-top: 12px;
}
.intent-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.intent-item span {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.intent-item strong {
    font-size: 0.9rem;
    color: var(--text-primary);
    font-weight: 500;
}

/* ==================================================
   TRADEOFF BADGES
   ================================================== */
.tradeoff-badge {
    margin: -20px -20px 16px -20px;
    padding: 12px 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.tradeoff-badge small {
    font-size: 0.75rem;
    font-weight: 400;
    text-transform: none;
    letter-spacing: normal;
    opacity: 0.9;
}
.badge-best-overall {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
    color: #a855f7;
    border-bottom-color: rgba(168, 85, 247, 0.2);
}
.badge-best-value {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
    color: #10b981;
    border-bottom-color: rgba(16, 185, 129, 0.2);
}
.badge-best-performance {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%);
    color: #f97316;
    border-bottom-color: rgba(249, 115, 22, 0.2);
}

/* ==================================================
   COMPARISON TABLE
   ================================================== */
.comparison-section {
    grid-column: 1 / -1;
    background: var(--surface-light);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin: 16px 0;
}
.comparison-section h3 {
    font-size: 1.1rem;
    font-weight: 500;
    margin-bottom: 16px;
    color: var(--text-primary);
}
.comp-table {
    display: flex;
    flex-direction: column;
    gap: 1px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.comp-row {
    display: flex;
    background: var(--surface-light);
}
.comp-header {
    background: rgba(255, 255, 255, 0.02);
}
.comp-label {
    width: 140px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
}
.comp-cells {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
}
.comp-cells > div {
    padding: 12px 16px;
    font-size: 0.9rem;
    color: var(--text-primary);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    text-align: center;
}
.comp-cells > div:last-child {
    border-right: none;
}
.comp-header .comp-cells > div {
    font-size: 0.85rem;
    color: var(--text-secondary);
}
.comp-header .comp-cells strong {
    color: var(--text-primary);
    font-size: 0.95rem;
    display: block;
    margin-bottom: 4px;
}
"""

with open(css_file, 'a', encoding='utf-8') as f:
    f.write(css_styles)

print("CSS appended.")
