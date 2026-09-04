import os

css_file = 'frontend/style.css'
with open(css_file, 'r', encoding='utf-8') as f:
    content = f.read()

css_rules = '''
/* ======================================================
   MERCHANT INSIGHT CARD
   ====================================================== */
.merchant-insight-card {
    background-color: #1a1a2e;
    border: 1px solid #4d4dff;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 15px rgba(77, 77, 255, 0.2);
    color: #e0e0e0;
}

.insight-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    border-bottom: 1px solid #333;
    padding-bottom: 10px;
}

.insight-icon {
    font-size: 1.5rem;
    margin-right: 10px;
}

.insight-header h3 {
    margin: 0;
    color: #4d4dff;
    font-size: 1.2rem;
}

.insight-body p {
    margin: 8px 0;
    font-size: 0.95rem;
    line-height: 1.4;
}

.insight-body strong {
    color: #fff;
}

.insight-alternatives {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px dashed #444;
}

.insight-alts-title {
    color: #ffaa00 !important;
    font-weight: bold;
    margin-bottom: 10px !important;
}

.insight-alts-list {
    list-style-type: disc;
    padding-left: 20px;
    margin: 0;
}

.insight-alts-list li {
    margin-bottom: 8px;
    font-size: 0.9rem;
}

.insight-alt-diff {
    color: #aaa;
    font-size: 0.85rem;
}
'''

if '.merchant-insight-card' not in content:
    with open(css_file, 'a', encoding='utf-8') as f:
        f.write('\n' + css_rules)

print("CSS updated.")
