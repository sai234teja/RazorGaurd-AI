import re
import os

script_file = 'frontend/script.js'
with open(script_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Patch renderIntent to use intent-grid
new_renderIntent = '''function renderIntent(intent) {
    intentContent.innerHTML = "";
    if (!intent) return;
    
    const grid = document.createElement("div");
    grid.className = "intent-grid";
    
    function addGridItem(label, value) {
        const item = document.createElement("div");
        item.className = "intent-item";
        item.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong>`;
        grid.appendChild(item);
    }

    if (intent.category) addGridItem("Category", intent.category);
    if (intent.subcategory) addGridItem("Product", intent.subcategory);
    if (intent.max_price !== null && intent.max_price !== undefined) addGridItem("Budget", `≤ ₹${formatNumber(intent.max_price)}`);
    if (intent.min_price !== null && intent.min_price !== undefined) addGridItem("Minimum price", `≥ ₹${formatNumber(intent.min_price)}`);
    
    if (intent.required) {
        Object.entries(intent.required).forEach(([k, v]) => {
            const label = formatKey(k);
            let val = v;
            if (typeof v === "object") {
                if (v[">="]) val = `≥ ${v[">="]}`;
                else if (v["<="]) val = `≤ ${v["<="]}`;
                else if (v["=="]) val = `${v["=="]}`;
            }
            addGridItem(label, val);
        });
    }

    if (Array.isArray(intent.use_cases) && intent.use_cases.length) {
        addGridItem("Use case", intent.use_cases.join(" · "));
    }

    if (intent.preferences && typeof intent.preferences === "object") {
        const prefs = Object.entries(intent.preferences).map(([k, p]) => formatKey(k));
        if (prefs.length > 0) {
            addGridItem("Priorities", prefs.join(" · "));
        }
    }
    
    intentContent.appendChild(grid);
}'''

# Replace renderIntent
content = re.sub(r'function renderIntent\(intent\) \{.*?(?=// ======================================================\n// ADD INTENT TAG)', new_renderIntent + '\n\n', content, flags=re.DOTALL)


# 2. Inject Comparison Table logic inside renderProducts (at the end before View More UX)
comparison_logic = '''
    // ======================================
    // TRADE-OFF COMPARISON TABLE
    // ======================================
    if (products.length >= 2) {
        const comparisonContainer = document.createElement("div");
        comparisonContainer.className = "comparison-section";
        
        let rows = "";
        const topPicks = products.slice(0, 3);
        
        // Find which attributes vary
        const priceRow = topPicks.map(p => `<div><strong>${p.name}</strong><br>₹${p.price.toLocaleString('en-IN')}</div>`).join("");
        
        let attrsHTML = "";
        const checkAttrs = ["processor", "ram_gb", "storage_gb", "camera_mp", "battery_mah"];
        checkAttrs.forEach(attr => {
            const hasAttr = topPicks.some(p => p.attributes && p.attributes[attr]);
            if (hasAttr) {
                const rowCells = topPicks.map(p => `<div>${p.attributes && p.attributes[attr] ? p.attributes[attr] : '-'}</div>`).join("");
                attrsHTML += `<div class="comp-row"><div class="comp-label">${formatKey(attr)}</div><div class="comp-cells">${rowCells}</div></div>`;
            }
        });
        
        comparisonContainer.innerHTML = `
            <h3>How the top picks differ</h3>
            <div class="comp-table">
                <div class="comp-row comp-header">
                    <div class="comp-label">Price</div>
                    <div class="comp-cells">${priceRow}</div>
                </div>
                ${attrsHTML}
            </div>
        `;
        
        // Insert after the first few products, or at the bottom before View More
        productsContainer.appendChild(comparisonContainer);
    }
'''

content = content.replace('// View More / Less UX', comparison_logic + '\n    // View More / Less UX')

# 3. Product Card Badges & Strong Match
# Find the product card rendering
# `<div class="product-card">` -> `<div class="product-card"> ${product.tradeoff_label ? `<div class="tradeoff-badge badge-${product.tradeoff_label.toLowerCase().replace(' ', '-')}">${product.tradeoff_label}</div>` : ''}`

content = content.replace(
    'card.className =\n                "product-card";',
    'card.className =\n                "product-card";'
)

# Insert badge above image
badge_injection = '''
            const tradeoffBadge = product.tradeoff_label ? `<div class="tradeoff-badge badge-${product.tradeoff_label.toLowerCase().replace(' ', '-')}">${product.tradeoff_label}<br><small>${product.tradeoff_reason}</small></div>` : "";
'''

content = content.replace('const score =', badge_injection + '\n            const score =')

# Replace generic match score
strong_match_logic = '''
            const scoreText = product.strong_match ? "Strong match" : (Number.isFinite(score) ? `${score.toFixed(2)}% match` : "Recommended");
'''
content = re.sub(r'const scoreText =.*?;\n', strong_match_logic + '\n', content, flags=re.DOTALL)

# Prepend tradeoffBadge to innerHTML
content = content.replace('<div class="product-header">', '${tradeoffBadge}\n                <div class="product-header">')

with open(script_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Frontend JS tradeoff patch complete.")
