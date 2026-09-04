import os

script_file = 'frontend/script.js'
with open(script_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove existing merchant insight card if any
if 'merchant-insight-card' in content:
    pass

ui_logic = '''
    // Remove old merchant insight if it exists
    const oldInsight = document.getElementById("merchant-insight-container");
    if (oldInsight) {
        oldInsight.remove();
    }

    if (data.merchant_insight) {
        const insightContainer = document.createElement("div");
        insightContainer.id = "merchant-insight-container";
        insightContainer.className = "merchant-insight-card";
        
        let altsHtml = "";
        if (data.merchant_insight.closest_alternatives && data.merchant_insight.closest_alternatives.length > 0) {
            altsHtml = `
                <div class="insight-alternatives">
                    <p class="insight-alts-title">Closest alternatives — do not satisfy all requirements</p>
                    <ul class="insight-alts-list">
                        ${data.merchant_insight.closest_alternatives.map(alt => `
                            <li>
                                <strong>${alt.name}</strong> - ₹${alt.price.toLocaleString('en-IN')}<br>
                                <span class="insight-alt-diff">${alt.difference}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        
        insightContainer.innerHTML = `
            <div class="insight-header">
                <span class="insight-icon">💡</span>
                <h3>Merchant opportunity detected</h3>
            </div>
            <div class="insight-body">
                <p><strong>Why the sale was lost:</strong> No catalog item satisfies the shopper's requirements.</p>
                <p><strong>What shoppers are asking for:</strong> ${data.merchant_insight.opportunity}</p>
                <p><strong>Catalog opportunity:</strong> Add products matching this combination.</p>
                ${altsHtml}
            </div>
        `;
        
        // Insert before productsContainer
        productsContainer.parentNode.insertBefore(insightContainer, productsContainer);
    }
'''

if 'merchant-insight-container' not in content:
    content = content.replace(
        'renderProducts(currentProducts);',
        ui_logic + '\n    renderProducts(currentProducts);'
    )

with open(script_file, 'w', encoding='utf-8') as f:
    f.write(content)
    
print("Frontend script updated.")
