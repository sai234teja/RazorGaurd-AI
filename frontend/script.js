const API_URL = "/api/recommend";

// ======================================================
// DOM ELEMENTS
// ======================================================

const input = document.getElementById("userInput");
const searchBtn = document.getElementById("searchBtn");

const searchText = document.getElementById("searchText");
const loadingText = document.getElementById("loadingText");

const results = document.getElementById("results");
const intentContent = document.getElementById("intentContent");
const productsContainer = document.getElementById("products");

const candidateCount = document.getElementById("candidateCount");
const errorBox = document.getElementById("errorBox");

// ======================================================
// CART DOM ELEMENTS
// ======================================================

const cartButton = document.getElementById("cartButton");
const cartCount = document.getElementById("cartCount");

const cartSection = document.getElementById("cartSection");
const closeCartButton = document.getElementById("closeCartButton");

const cartItemsContainer = document.getElementById("cartItems");
const emptyCart = document.getElementById("emptyCart");

const cartSummary = document.getElementById("cartSummary");
const cartItemCount = document.getElementById("cartItemCount");

const cartSubtotal = document.getElementById("cartSubtotal");
const cartTotal = document.getElementById("cartTotal");

const checkoutButton = document.getElementById("checkoutButton");
const cartToast = document.getElementById("cartToast");

// ======================================================
// CART STATE
// ======================================================

let cart = [];

// ======================================================
// CURRENT PRODUCTS
// ======================================================

let currentProducts = [];

// ======================================================
// CHECKOUT STATE
// ======================================================

let currentCheckout = null;

// ======================================================
// LOAD CART
// ======================================================

loadCart();

const STREAM_API_URL = "/api/recommend/stream";

// ======================================================
// SEARCH
// ======================================================

async function searchProducts() {
    const message = input.value.trim();

    if (!message) {
        showError("Please describe what product you are looking for.");
        return;
    }

    setLoading(true);
    hideError();
    results.classList.add("hidden");

    // Reset pipeline UI
    const pipelineVis = document.getElementById("pipeline-visualization");
    const stages = document.querySelectorAll(".pipeline-stage");
    stages.forEach(s => {
        s.classList.remove("running", "completed", "error");
    });
    
    resetJudgeMode();
    document.getElementById("judgeModePanel").classList.remove("hidden");

    if (pipelineVis) {
        pipelineVis.classList.remove("hidden");
    }

    try {
        // Try Streaming API first
        const response = await fetch(STREAM_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error("Stream API failed, falling back...");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let finalResult = null;

        while (true) {
            const { value, done } = await reader.read();
            
            if (value) {
                buffer += decoder.decode(value, { stream: true });
            }
            
            if (done && buffer.trim().length > 0 && !buffer.endsWith("\n\n")) {
                buffer += "\n\n";
            }

            const lines = buffer.split("\n\n");
            buffer = lines.pop() || ""; // keep incomplete chunk in buffer

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.slice(6);
                    try {
                        const event = JSON.parse(dataStr);

                        if (event.type === "stage") {
                            const stageEl = document.getElementById(`stage-${event.stage}`);
                            if (stageEl) {
                                if (event.status === "running") {
                                    stageEl.classList.add("running");
                                    stageEl.classList.remove("completed", "error");
                                } else if (event.status === "completed") {
                                    stageEl.classList.remove("running");
                                    stageEl.classList.add("completed");
                                } else if (event.status === "error") {
                                    stageEl.classList.remove("running");
                                    stageEl.classList.add("error");
                                }
                            }
                            handleJudgeModeStage(event.stage, event.status);
                        } else if (event.type === "result") {
                            finalResult = event;
                        }
                    } catch (e) {
                        console.error("Error parsing SSE JSON", e);
                    }
                }
            }
            
            if (done) break;
        }

        if (finalResult && finalResult.success && finalResult.data) {
            if (pipelineVis) {
                pipelineVis.classList.add("hidden");
            }
            renderResults(finalResult.data);
            setLoading(false);
            return;
        } else if (finalResult && !finalResult.success) {
            throw new Error(finalResult.error || "Recommendation failed.");
        } else {
            throw new Error("No final result received from stream.");
        }

    } catch (error) {
        console.warn("Stream failed, falling back to standard API...", error);
        
        // Hide pipeline UI since we are falling back
        if (pipelineVis) {
            pipelineVis.classList.add("hidden");
        }

        try {
            const fbResponse = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message })
            });

            let fbData;
            try {
                fbData = await fbResponse.json();
            } catch (jsonError) {
                throw new Error("The server returned an invalid response.");
            }

            if (!fbResponse.ok || !fbData.success) {
                throw new Error(fbData.error || fbData.message || "Unable to get recommendations.");
            }

            if (!fbData.data || !Array.isArray(fbData.data.products)) {
                throw new Error("The server response is missing product recommendations.");
            }

            renderResults(fbData.data);
        } catch (fbError) {
            console.error(fbError);
            showError(fbError.message || "An unexpected error occurred. Please try again.");
            setLoading(false);
        }
    }
}

// ======================================================
// RENDER RESULTS
// ======================================================

function renderResults(data) {

    results.classList.remove("hidden");
    const hero = document.querySelector(".hero");
    if (hero) hero.classList.add("hero-results-state");

    handleJudgeModeResult(data);

    renderIntent(data.intent);

    const count =
        data.candidate_count ??
        data.products?.length ??
        0;

    candidateCount.textContent =
        `${count} product${count === 1 ? "" : "s"} considered`;

    currentProducts =
        Array.isArray(data.products)
            ? data.products
            : [];

    
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

    renderProducts(currentProducts);

    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

// ======================================================
// INTENT
// ======================================================

function renderIntent(intent) {
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
}

// ======================================================
// ADD INTENT TAG
// ======================================================

function addIntentTag(label, value) {

    const tag =
        document.createElement("div");

    tag.className =
        "intent-tag";

    tag.innerHTML =
        `<strong>${escapeHtml(label)}:</strong>
         ${escapeHtml(String(value))}`;

    intentContent.appendChild(tag);
}

// ======================================================
// IMAGE PLACEHOLDERS
// ======================================================

function getCategoryImage(category) {
    const cat = String(category || "").toLowerCase();
    
    // SVG icons encoded as Data URIs for offline/safe fallback
    let svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>';
    
    if (cat.includes("phone")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>';
    } else if (cat.includes("laptop")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="20" x2="22" y2="20"></line></svg>';
    } else if (cat.includes("headphone") || cat.includes("audio")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path></svg>';
    } else if (cat.includes("watch")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="7"></circle><polyline points="12 9 12 12 13.5 13.5"></polyline><path d="M16.51 17.35l-.35 3.83a2 2 0 0 1-2 1.82H9.83a2 2 0 0 1-2-1.82l-.35-3.83m.01-10.7l.35-3.83A2 2 0 0 1 9.83 1h4.35a2 2 0 0 1 2 1.82l.35 3.83"></path></svg>';
    } else if (cat.includes("shoe")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12a10 10 0 0 1-10 10H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3c2 0 4 2 4 2h5s2-2 4-2h0a2 2 0 0 1 2 2v3z"></path></svg>';
    } else if (cat.includes("backpack") || cat.includes("bag")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>';
    } else if (cat.includes("fitness")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h3a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-3"></path><path d="M6 10H3a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h3"></path><path d="M6 14h12"></path></svg>';
    } else if (cat.includes("fryer") || cat.includes("kitchen")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"></path><path d="M20 14H4"></path><path d="M16 10h-2"></path><path d="M10 10H8"></path><path d="M6 10V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v4"></path></svg>';
    } else if (cat.includes("vacuum")) {
        svgIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="14" width="18" height="8" rx="2" ry="2"></rect><path d="M9 14v-4a3 3 0 0 1 6 0v4"></path><path d="M12 10V4"></path><path d="M8 4h8"></path></svg>';
    }
    const svgData = btoa(svgIcon);
    return `data:image/svg+xml;base64,${svgData}`;
}

// ======================================================
// PRODUCTS
// ======================================================

function renderProducts(products, isExpanded = false) {

    productsContainer.innerHTML = "";

    if (
        !Array.isArray(products) ||
        !products.length
    ) {

        productsContainer.innerHTML = `
            <div class="product-card">

                <h3>
                    No products found
                </h3>

                <p>
                    Try changing your budget or requirements.
                </p>

            </div>
        `;

        return;
    }

        const displayProducts = isExpanded ? products : products.slice(0, 5);
    displayProducts.forEach(
        (product, index) => {

            const card =
                document.createElement("div");

            card.className =
                "product-card";

            if (index === 0) {

                card.classList.add(
                    "best"
                );
            }

            
            const tradeoffBadge = product.tradeoff_label ? `<div class="tradeoff-badge badge-${product.tradeoff_label.toLowerCase().replace(' ', '-')}">${product.tradeoff_label}<br><small>${product.tradeoff_reason}</small></div>` : "";

            const score =
                Number(
                    product.match_score
                );

            
            const scoreText = product.strong_match ? "Strong match" : (Number.isFinite(score) ? `${score.toFixed(2)}% match` : "Recommended");


            const brand =
                product.brand &&
                product.brand !== "nan"
                    ? product.brand
                    : "";

            let imageUrl = normalizeUrl(product.image_url);
            
            // Ensure the image URL actually relates to the product category/name
            // and is not a random placeholder or unrelated web image
            const searchStr = (product.category + " " + product.subcategory + " " + product.name).toLowerCase();
            if (imageUrl && !imageUrl.includes('razorpay.com') && !imageUrl.includes('localhost')) {
                // If it's an external image, aggressively validate it
                if (imageUrl.includes('unsplash') || imageUrl.includes('placeholder') || imageUrl.includes('dummy')) {
                    imageUrl = "";
                }
            }
            
            // Final deterministic fallback to safe SVGs
            if (!imageUrl) {
                imageUrl = getCategoryImage(product.category + " " + product.subcategory);
            }

            const productUrl =
                normalizeUrl(
                    product.product_url
                );

            const alreadyInCart =
                getCartItem(
                    product.product_id
                );

            const addButtonText =
                alreadyInCart
                    ? `✓ In Cart (${alreadyInCart.quantity})`
                    : "🛒 Add to Cart";

            card.innerHTML = `

                <div class="rank">
                    ${
                        index === 0
                            ? "🏆 BEST MATCH"
                            : `#${index + 1}`
                    }
                </div>

                ${
                    imageUrl
                        ? `
                            <div class="product-image-wrapper">

                                <img
                                    class="product-image"
                                    src="${escapeHtml(imageUrl)}"
                                    alt="${escapeHtml(product.name || "Product")}"
                                    loading="lazy"
                                    onerror="this.onerror=null; this.src='${escapeHtml(getCategoryImage(product.category + ' ' + product.subcategory))}';"
                                >

                            </div>
                          `
                        : ""
                }

                <h3 class="product-name">

                    ${escapeHtml(
                        product.name || "Unnamed Product"
                    )}

                </h3>

                ${
                    brand
                        ? `
                            <div class="brand">
                                ${escapeHtml(brand)}
                            </div>
                          `
                        : ""
                }

                <div class="price-row">

                    <div>

                        <div class="price">

                            ₹${formatNumber(
                                product.price
                            )}

                        </div>

                        <div class="rating">

                            ⭐ ${escapeHtml(
                                String(
                                    product.rating ?? "N/A"
                                )
                            )}/5

                        </div>

                    </div>

                    <div class="score">

                        ${escapeHtml(
                            scoreText
                        )}

                    </div>

                </div>

                ${
                    product.description
                        ? `
                            <div class="description">

                                ${escapeHtml(
                                    product.description
                                )}

                            </div>
                          `
                        : ""
                }

                <div class="attributes">

                    ${renderAttributes(
                        product.attributes || {}
                    )}

                </div>

                <div class="stock">

                    ${
                        Number(product.stock) > 0
                            ? `✓ In stock (${escapeHtml(
                                String(product.stock)
                              )} available)`
                            : "✕ Out of stock"
                    }

                </div>

                <div class="why">

                    <div class="why-title">
                        WHY THIS MATCHES
                    </div>

                    ${renderWhy(
                        product.why || []
                    )}

                </div>

                <!-- ======================================
                     PRICE COMPARISON
                     ====================================== -->

                ${renderPriceComparison(
                    product.price_comparison,
                    product.price
                )}

                <!-- ======================================
                     PRODUCT ACTIONS
                     ====================================== -->

                <div class="product-actions">

                    <button
                        type="button"
                        class="add-to-cart-button"
                        data-product-id="${escapeHtml(
                            product.product_id
                        )}"
                    >

                        ${addButtonText}

                    </button>

                    ${
                        productUrl
                            ? `
                                <a
                                    class="product-link"
                                    href="${escapeHtml(productUrl)}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    View Product
                                </a>
                              `
                            : `
                                <button
                                    type="button"
                                    class="product-link product-link-disabled"
                                    disabled
                                >
                                    Product link unavailable
                                </button>
                              `
                    }

                </div>

            `;

            productsContainer.appendChild(
                card
            );
        }
    );


    
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

    // View More / Less UX
    if (products.length > 5) {
        const uxContainer = document.createElement("div");
        uxContainer.className = "view-more-container";
        uxContainer.style.textAlign = "center";
        uxContainer.style.margin = "20px 0";
        uxContainer.style.padding = "10px";
        uxContainer.style.borderTop = "1px solid #333";
        
        const message = document.createElement("p");
        message.style.color = "#888";
        message.style.fontSize = "0.9rem";
        message.style.marginBottom = "10px";
        
        if (!isExpanded) {
            message.textContent = `Showing the 5 best matches · ${products.length - 5} more available`;
        } else {
            message.textContent = "Showing all matching results";
        }
        
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "view-more-btn";
        btn.style.padding = "8px 16px";
        btn.style.background = "#222";
        btn.style.color = "#fff";
        btn.style.border = "1px solid #444";
        btn.style.borderRadius = "4px";
        btn.style.cursor = "pointer";
        btn.textContent = !isExpanded ? "View more results" : "Show top 5";
        
        btn.addEventListener("click", () => {
            renderProducts(products, !isExpanded);
        });
        
        uxContainer.appendChild(message);
        uxContainer.appendChild(btn);
        productsContainer.appendChild(uxContainer);
    }

    attachAddToCartListeners();

}

// ======================================================
// PRICE COMPARISON
// ======================================================

function renderPriceComparison(
    comparison,
    catalogPrice
) {

    if (
        !comparison ||
        typeof comparison !== "object"
    ) {

        return "";
    }

    const offers =
        Array.isArray(comparison.offers)
            ? comparison.offers
            : [];

    const hasOffers =
        comparison.has_offers &&
        offers.length > 0;

    if (!hasOffers) {

        return `
            <div class="price-comparison">

                <div class="price-comparison-header">

                    <span>
                        💰 Price Comparison
                    </span>

                    <span class="comparison-status">
                        No offers available
                    </span>

                </div>

                <div class="comparison-note">

                    No merchant offers are currently available
                    for this product.

                </div>

            </div>
        `;
    }

    const lowestPrice =
        Number(comparison.lowest_total);

    const savings =
        Number(comparison.savings);

    const merchant =
        comparison.lowest_merchant ||
        "Lowest-price merchant";

    const offerCount =
        Number(comparison.offer_count) ||
        offers.length;

    const lowestOffer =
        offers.find(
            offer => offer.is_lowest
        ) ||
        offers.reduce(
            (lowest, offer) => {

                const current =
                    Number(
                        offer.total_price ??
                        offer.price ??
                        Infinity
                    );

                const previous =
                    Number(
                        lowest?.total_price ??
                        lowest?.price ??
                        Infinity
                    );

                return current < previous
                    ? offer
                    : lowest;

            },
            null
        );

    return `

        <div class="price-comparison">

            <div class="price-comparison-header">

                <div>

                    <span class="price-comparison-title">
                        💰 Compare Prices
                    </span>

                    <span class="offer-count">
                        ${offerCount} offers
                    </span>

                </div>

                <span class="lowest-badge">
                    🏆 LOWEST PRICE
                </span>

            </div>

            <div class="lowest-price-box">

                <div class="lowest-price-info">

                    <div class="lowest-label">
                        Best available price
                    </div>

                    <div class="lowest-price">

                        ₹${formatNumber(lowestPrice)}

                    </div>

                    <div class="lowest-merchant">

                        at

                        <strong>
                            ${escapeHtml(merchant)}
                        </strong>

                    </div>

                </div>

                ${
                    Number.isFinite(savings) &&
                    savings > 0
                        ? `
                            <div class="savings-box">

                                Save

                                <strong>
                                    ₹${formatNumber(savings)}
                                </strong>

                            </div>
                          `
                        : ""
                }

            </div>

            <div class="offer-list">

                ${offers.map(
                    (offer, index) => {

                        const offerPrice =
                            Number(
                                offer.total_price ??
                                offer.price ??
                                0
                            );

                        const shipping =
                            Number(
                                offer.shipping_fee || 0
                            );

                        const delivery =
                            offer.delivery_days;

                        const isLowest =
                            offer.is_lowest === true ||
                            (
                                lowestOffer &&
                                String(
                                    offer.offer_id
                                ) === String(
                                    lowestOffer.offer_id
                                )
                            );

                        const merchantName =
                            offer.merchant_name ||
                            "Merchant";

                        const sourceType =
                            String(
                                offer.source_type ||
                                ""
                            ).toLowerCase();

                        const isDemo =
                            sourceType === "demo";

                        const offerUrl =
                            normalizeUrl(
                                offer.product_url
                            );

                        return `

                            <div class="
                                offer-row
                                ${isLowest ? "lowest-offer" : ""}
                            ">

                                <div class="offer-merchant">

                                    <div class="merchant-name">

                                        ${
                                            isLowest
                                                ? "🏆 "
                                                : ""
                                        }

                                        ${escapeHtml(
                                            merchantName
                                        )}

                                    </div>

                                    <div class="merchant-meta">

                                        ${
                                            isDemo
                                                ? `
                                                    <span class="demo-badge">
                                                        DEMO
                                                    </span>
                                                  `
                                                : `
                                                    <span class="verified-badge">
                                                        ${
                                                            offer.is_verified
                                                                ? "✓ VERIFIED"
                                                                : "UNVERIFIED"
                                                        }
                                                    </span>
                                                  `
                                        }

                                    </div>

                                </div>

                                <div class="offer-details">

                                    <div class="offer-price">

                                        ₹${formatNumber(
                                            offerPrice
                                        )}

                                    </div>

                                    ${
                                        shipping > 0
                                            ? `
                                                <div class="offer-shipping">
                                                    + ₹${formatNumber(shipping)} shipping
                                                </div>
                                              `
                                            : `
                                                <div class="offer-shipping">
                                                    Free shipping
                                                </div>
                                              `
                                    }

                                    ${
                                        delivery !== null &&
                                        delivery !== undefined
                                            ? `
                                                <div class="offer-delivery">
                                                    ${escapeHtml(
                                                        String(delivery)
                                                    )} day${Number(delivery) === 1 ? "" : "s"}
                                                </div>
                                              `
                                            : ""
                                    }

                                </div>

                                <div class="offer-action">

                                    ${
                                        offerUrl
                                            ? `
                                                <a
                                                    href="${escapeHtml(offerUrl)}"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    class="offer-view-button"
                                                >
                                                    View Deal
                                                </a>
                                              `
                                            : `
                                                <span class="offer-no-link">
                                                    Link unavailable
                                                </span>
                                              `
                                    }

                                </div>

                            </div>

                        `;
                    }
                ).join("")}

            </div>

            ${
                offers.some(
                    offer =>
                        String(
                            offer.source_type || ""
                        ).toLowerCase() === "demo"
                )
                    ? `
                        <div class="comparison-disclaimer">

                            ⚠️ Some offers shown here are
                            DEMO/SIMULATED offers.
                            They are not live retailer prices.

                        </div>
                      `
                    : ""
            }

        </div>
    `;
}

// ======================================================
// ADD TO CART BUTTON LISTENERS
// ======================================================

function attachAddToCartListeners() {

    const buttons =
        document.querySelectorAll(
            ".add-to-cart-button[data-product-id]"
        );

    buttons.forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const productId =
                        button.dataset.productId;

                    const product =
                        currentProducts.find(
                            item =>
                                String(
                                    item.product_id
                                ) === String(
                                    productId
                                )
                        );

                    if (!product) {

                        showError(
                            "Unable to add this product to cart."
                        );

                        return;
                    }

                    addToCart(
                        product
                    );

                    updateProductButton(
                        button,
                        productId
                    );
                }
            );
        }
    );
}

// ======================================================
// ADD TO CART
// ======================================================

function addToCart(product) {

    const existing =
        getCartItem(
            product.product_id
        );

    if (existing) {

        const stock =
            Number(product.stock);

        if (
            Number.isFinite(stock) &&
            stock > 0 &&
            existing.quantity >= stock
        ) {

            showToast(
                "Maximum available stock reached."
            );

            return;
        }

        existing.quantity += 1;

    } else {

        cart.push({

            product_id:
                product.product_id,

            name:
                product.name,

            price:
                Number(product.price) || 0,

            rating:
                Number(product.rating) || 0,

            stock:
                Number(product.stock) || 0,

            description:
                product.description || "",

            image_url:
                product.image_url || "",

            product_url:
                product.product_url || "",

            quantity:
                1
        });
    }

    saveCart();

    updateCartUI();

    showToast(
        `${product.name} added to cart`
    );
}

// ======================================================
// GET CART ITEM
// ======================================================

function getCartItem(productId) {

    return cart.find(
        item =>
            String(item.product_id) ===
            String(productId)
    );
}

// ======================================================
// INCREASE QUANTITY
// ======================================================

function increaseQuantity(productId) {

    const item =
        getCartItem(
            productId
        );

    if (!item) {
        return;
    }

    if (
        item.stock > 0 &&
        item.quantity >= item.stock
    ) {

        showToast(
            "Maximum available stock reached."
        );

        return;
    }

    item.quantity += 1;

    saveCart();

    updateCartUI();
}

// ======================================================
// DECREASE QUANTITY
// ======================================================

function decreaseQuantity(productId) {

    const item =
        getCartItem(
            productId
        );

    if (!item) {
        return;
    }

    if (
        item.quantity > 1
    ) {

        item.quantity -= 1;

    } else {

        removeFromCart(
            productId
        );

        return;
    }

    saveCart();

    updateCartUI();
}

// ======================================================
// REMOVE FROM CART
// ======================================================

function removeFromCart(productId) {

    cart =
        cart.filter(
            item =>
                String(item.product_id) !==
                String(productId)
        );

    saveCart();

    updateCartUI();

    showToast(
        "Product removed from cart"
    );
}

// ======================================================
// UPDATE CART UI
// ======================================================

function updateCartUI() {

    const totalQuantity =
        cart.reduce(
            (
                total,
                item
            ) =>
                total + item.quantity,
            0
        );

    const subtotal =
        cart.reduce(
            (
                total,
                item
            ) =>
                total +
                (
                    item.price *
                    item.quantity
                ),
            0
        );

    if (cartCount) {

        cartCount.textContent =
            totalQuantity;
        cartCount.classList.remove('bump');
        void cartCount.offsetWidth; // restart animation
        cartCount.classList.add('bump');
    }

    if (
        cart.length === 0
    ) {

        if (emptyCart) {

            emptyCart.classList.remove(
                "hidden"
            );
        }

        if (cartSummary) {

            cartSummary.classList.add(
                "hidden"
            );
        }

        if (cartItemsContainer) {

            cartItemsContainer.innerHTML =
                "";
        }

        return;
    }

    if (emptyCart) {

        emptyCart.classList.add(
            "hidden"
        );
    }

    if (cartSummary) {

        cartSummary.classList.remove(
            "hidden"
        );
    }

    if (cartItemCount) {

        cartItemCount.textContent =
            totalQuantity;
    }

    if (cartSubtotal) {

        cartSubtotal.textContent =
            `₹${formatNumber(subtotal)}`;
    }

    if (cartTotal) {

        cartTotal.textContent =
            `₹${formatNumber(subtotal)}`;
    }

    renderCartItems();
}

// ======================================================
// RENDER CART ITEMS
// ======================================================

function renderCartItems() {

    if (!cartItemsContainer) {
        return;
    }

    cartItemsContainer.innerHTML =
        "";

    cart.forEach(
        item => {

            const itemElement =
                document.createElement(
                    "div"
                );

            itemElement.className =
                "cart-item";

            const itemTotal =
                item.price *
                item.quantity;

            itemElement.innerHTML = `

                <div class="cart-item-info">

                    ${
                        item.image_url
                            ? `
                                <img
                                    class="cart-item-image"
                                    src="${escapeHtml(
                                        item.image_url
                                    )}"
                                    alt="${escapeHtml(
                                        item.name
                                    )}"
                                >
                              `
                            : `
                                <div class="cart-item-placeholder">
                                    🛍️
                                </div>
                              `
                    }

                    <div class="cart-item-details">

                        <h3>
                            ${escapeHtml(
                                item.name
                            )}
                        </h3>

                        <p>
                            ₹${formatNumber(
                                item.price
                            )}
                        </p>

                    </div>

                </div>

                <div class="cart-item-controls">

                    <button
                        type="button"
                        class="quantity-button"
                        data-action="decrease"
                        data-product-id="${escapeHtml(
                            item.product_id
                        )}"
                    >
                        −
                    </button>

                    <span class="quantity">
                        ${item.quantity}
                    </span>

                    <button
                        type="button"
                        class="quantity-button"
                        data-action="increase"
                        data-product-id="${escapeHtml(
                            item.product_id
                        )}"
                    >
                        +
                    </button>

                    <strong class="cart-item-total">
                        ₹${formatNumber(
                            itemTotal
                        )}
                    </strong>

                    <button
                        type="button"
                        class="remove-cart-button"
                        data-product-id="${escapeHtml(
                            item.product_id
                        )}"
                    >
                        🗑️
                    </button>

                </div>

            `;

            cartItemsContainer.appendChild(
                itemElement
            );
        }
    );

    attachCartListeners();
}

// ======================================================
// CART BUTTON LISTENERS
// ======================================================

function attachCartListeners() {

    document
        .querySelectorAll(
            ".quantity-button"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const productId =
                            button.dataset.productId;

                        const action =
                            button.dataset.action;

                        if (
                            action ===
                            "increase"
                        ) {

                            increaseQuantity(
                                productId
                            );

                        } else {

                            decreaseQuantity(
                                productId
                            );
                        }
                    }
                );
            }
        );

    document
        .querySelectorAll(
            ".remove-cart-button"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        removeFromCart(
                            button.dataset.productId
                        );
                    }
                );
            }
        );
}

// ======================================================
// UPDATE PRODUCT BUTTON
// ======================================================

function updateProductButton(
    button,
    productId
) {

    const item =
        getCartItem(
            productId
        );

    if (!item) {

        button.textContent =
            "🛒 Add to Cart";

        return;
    }

    button.textContent =
        `✓ In Cart (${item.quantity})`;
}

// ======================================================
// REFRESH PRODUCT BUTTONS
// ======================================================

function refreshProductButtons() {

    document
        .querySelectorAll(
            ".add-to-cart-button"
        )
        .forEach(
            button => {

                updateProductButton(
                    button,
                    button.dataset.productId
                );
            }
        );
}

// ======================================================
// CART OPEN
// ======================================================

function openCart() {

    if (!cartSection) {
        return;
    }

    cartSection.classList.remove(
        "hidden"
    );

    cartSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    updateCartUI();
}

// ======================================================
// CART CLOSE
// ======================================================

function closeCart() {

    if (!cartSection) {
        return;
    }

    cartSection.classList.add(
        "hidden"
    );
}

// ======================================================
// SAVE CART
// ======================================================

function saveCart() {

    try {

        localStorage.setItem(
            "razorguard_cart",
            JSON.stringify(cart)
        );

    } catch (error) {

        console.warn(
            "Unable to save cart:",
            error
        );
    }
}

// ======================================================
// LOAD CART
// ======================================================

function loadCart() {

    try {

        const saved =
            localStorage.getItem(
                "razorguard_cart"
            );

        if (saved) {

            const parsed =
                JSON.parse(
                    saved
                );

            if (
                Array.isArray(parsed)
            ) {

                cart =
                    parsed;
                updateJudgeMode('j-step-verify', 'completed');

                cart = [];
                saveCart();
            }
        }

    } catch (error) {

        console.warn(
            "Unable to load cart:",
            error
        );

        cart = [];
    }

    updateCartUI();
}

// ======================================================
// CART TOGGLE
// ======================================================

if (cartButton) {

    cartButton.addEventListener(
        "click",
        openCart
    );
}

if (closeCartButton) {

    closeCartButton.addEventListener(
        "click",
        closeCart
    );
}

// ======================================================
// CHECKOUT BUTTON
// ======================================================

if (checkoutButton) {
    checkoutButton.addEventListener(
        "click",
        prepareCheckout
    );
}

// ======================================================
// PREPARE CHECKOUT
// ======================================================

async function prepareCheckout() {

    if (
        !Array.isArray(cart) ||
        cart.length === 0
    ) {

        showToast(
            "Your cart is empty."
        );

        return;
    }

    const originalText =
        checkoutButton.textContent;

    checkoutButton.disabled =
        true;

    checkoutButton.textContent =
        "Preparing Checkout...";

    resetJudgeMode();
    document.getElementById("judgeModePanel").classList.remove("hidden");
    updateJudgeMode('j-step-confirm', 'completed');
    updateJudgeMode('j-step-price', 'in-progress');

    try {

        const response =
            await fetch(
                "/api/checkout/prepare",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        items: cart
                    })
                }
            );

        let data;

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "The server returned an invalid checkout response."
            );
        }

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                data.message ||
                "Unable to prepare checkout."
            );
        }

        if (
            data.status !==
            "awaiting_confirmation"
        ) {

            throw new Error(
                "Checkout is not waiting for user confirmation."
            );
        }

        if (!data.order) {

            throw new Error(
                "Checkout response is missing the order."
            );
        }

        currentCheckout = {
            order:
                data.order,

            verification:
                data.verification,

            paymentProvider:
                data.payment_provider,

            testMode:
                data.test_mode === true
        };

        window.razorGuardCheckout =
            currentCheckout;

        updateJudgeMode('j-step-price', 'completed');
        updateJudgeMode('j-step-pg', 'completed');
        updateJudgeMode('j-step-razorpay', 'completed');
        updateJudgeMode('j-step-verify', 'in-progress');

        showCheckoutConfirmation(
            data
        );

    } catch (error) {

        console.error(
            "Checkout preparation error:",
            error
        );

        showToast(
            error.message ||
            "Unable to prepare checkout."
        );
        handleJudgeModeFailure(error.message || "Unable to prepare checkout.");

    } finally {

        checkoutButton.disabled =
            false;

        checkoutButton.textContent =
            originalText;
    }
}

// ======================================================
// CHECKOUT CONFIRMATION MODAL
// ======================================================

function showCheckoutConfirmation(
    checkoutData
) {

    const order =
        checkoutData.order;

    const verification =
        checkoutData.verification;

    if (
        !order ||
        !verification
    ) {

        showToast(
            "Invalid checkout response."
        );

        return;
    }

    const existingModal =
        document.getElementById(
            "checkoutConfirmationModal"
        );

    if (existingModal) {

        existingModal.remove();
    }

    const items =
        Array.isArray(order.items)
            ? order.items
            : [];

    const itemHtml =
        items.map(
            item => {

                const name =
                    escapeHtml(
                        item.name ||
                        "Product"
                    );

                const quantity =
                    Number(
                        item.quantity || 1
                    );

                const lineTotal =
                    Number(
                        item.line_total || 0
                    );

                return `
                    <div class="checkout-item">

                        <div>

                            <strong>
                                ${name}
                            </strong>

                            <span>
                                Qty: ${quantity}
                            </span>

                        </div>

                        <strong>
                            ₹${formatNumber(lineTotal)}
                        </strong>

                    </div>
                `;
            }
        ).join("");

    const modal =
        document.createElement(
            "div"
        );

    modal.id =
        "checkoutConfirmationModal";

    modal.className =
        "checkout-confirmation-overlay";

    modal.innerHTML = `

        <div
            class="checkout-confirmation-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="checkoutConfirmationTitle"
        >

            <div class="checkout-confirmation-header">

                <div>

                    <span class="checkout-test-badge">
                        ${
                            checkoutData.test_mode === true
                                ? "RAZORPAY TEST MODE"
                                : "RAZORPAY"
                        }
                    </span>

                    <h2 id="checkoutConfirmationTitle">
                        Confirm Your Order
                    </h2>

                    <p>
                        Please review your order before continuing.
                    </p>

                </div>

                <button
                    type="button"
                    class="checkout-close-button"
                    id="checkoutCancelButton"
                    aria-label="Cancel checkout"
                >
                    ×
                </button>

            </div>

            <div class="checkout-confirmation-body">

                <div class="checkout-customer-details">
                    <h3>Delivery Details</h3>
                    <div class="form-group">
                        <label for="checkoutName">Full Name</label>
                        <input type="text" id="checkoutName" class="form-input" placeholder="e.g. Rahul Sharma" required>
                    </div>
                    <div class="form-group">
                        <label for="checkoutEmail">Email Address</label>
                        <input type="email" id="checkoutEmail" class="form-input" placeholder="e.g. rahul@example.com" required>
                    </div>
                    <div class="form-group">
                        <label for="checkoutPhone">Phone Number</label>
                        <input type="tel" id="checkoutPhone" class="form-input" placeholder="e.g. +91 9876543210" required>
                    </div>
                    <div class="form-group">
                        <label for="checkoutAddress">Delivery Address</label>
                        <textarea id="checkoutAddress" class="form-input" rows="2" placeholder="e.g. 123 Main St, Apt 4" required></textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group half">
                            <label for="checkoutCity">City</label>
                            <input type="text" id="checkoutCity" class="form-input" placeholder="e.g. Bangalore" required>
                        </div>
                        <div class="form-group half">
                            <label for="checkoutState">State</label>
                            <input type="text" id="checkoutState" class="form-input" placeholder="e.g. Karnataka" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="checkoutPin">PIN Code</label>
                        <input type="text" id="checkoutPin" class="form-input" placeholder="e.g. 560001" required>
                    </div>
                </div>

                <div class="checkout-order-summary">

                    <div class="checkout-items">

                        ${itemHtml}

                    </div>

                    <div class="checkout-summary">

                        <div class="checkout-summary-row">

                            <span>
                                Subtotal
                            </span>

                            <strong>
                                ₹${formatNumber(
                                    Number(
                                        order.subtotal || 0
                                    )
                                )}
                            </strong>

                        </div>

                        <div class="checkout-summary-row">

                            <span>
                                Shipping
                            </span>

                            <strong>
                                ₹${formatNumber(
                                    Number(
                                        order.shipping_fee || 0
                                    )
                                )}
                            </strong>

                        </div>

                        ${
                            Number(order.discount || 0) > 0
                                ? `
                                    <div class="checkout-summary-row">

                                        <span>
                                            Discount
                                        </span>

                                        <strong>
                                            -₹${formatNumber(
                                                Number(
                                                    order.discount || 0
                                                )
                                            )}
                                        </strong>

                                    </div>
                                  `
                                : ""
                        }

                        <div class="checkout-summary-row checkout-total-row">

                            <span>
                                Total
                            </span>

                            <strong>
                                ₹${formatNumber(
                                    Number(
                                        order.total || 0
                                    )
                                )}
                            </strong>

                        </div>

                    </div>

                    <div class="checkout-verification">

                        <span>
                            ✓ Order total verified
                        </span>

                        <span>
                            ✓ Payment protected by RazorGuard
                        </span>

                        ${
                            verification.valid === true
                                ? `
                                    <span>
                                        ✓ Checkout validation passed
                                    </span>
                                  `
                                : `
                                    <span>
                                        ⚠️ Checkout validation failed
                                    </span>
                                  `
                        }

                    </div>



                    <div class="checkout-confirmation-footer">

                        <button
                            type="button"
                            class="checkout-cancel-action"
                            id="checkoutCancelAction"
                        >
                            Cancel
                        </button>

                        <button
                            type="button"
                            class="checkout-confirm-action"
                            id="checkoutConfirmButton"
                        >
                            Confirm &amp; Pay
                        </button>

                    </div>

                </div>

            </div>
        </div>
    `;

    document.body.appendChild(
        modal
    );

    const cancelButton =
        modal.querySelector(
            "#checkoutCancelButton"
        );

    const cancelAction =
        modal.querySelector(
            "#checkoutCancelAction"
        );

    const confirmButton =
        modal.querySelector(
            "#checkoutConfirmButton"
        );

    const closeModal =
        () => {

            modal.remove();

            currentCheckout =
                null;

            window.razorGuardCheckout =
                null;
        };

    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            closeModal
        );
    }

    if (cancelAction) {

        cancelAction.addEventListener(
            "click",
            closeModal
        );
    }



    if (confirmButton) {

        confirmButton.addEventListener(
            "click",
            () => {
                confirmCheckoutOrder(
                    checkoutData,
                    modal,
                    confirmButton
                );
            }
        );
    }

    const handleEscape =
        event => {

            if (
                event.key === "Escape"
            ) {

                closeModal();

                document.removeEventListener(
                    "keydown",
                    handleEscape
                );
            }
        };

    document.addEventListener(
        "keydown",
        handleEscape
    );
}

// ======================================================
// CONFIRM CHECKOUT
// ======================================================

async function confirmCheckoutOrder(
    checkoutData,
    modal,
    confirmButton
) {

    const order =
        checkoutData.order;

    if (!order) {

        showToast(
            "Checkout order is missing."
        );

        return;
    }

    // Capture customer details
    const nameEl = document.getElementById("checkoutName");
    const emailEl = document.getElementById("checkoutEmail");
    const phoneEl = document.getElementById("checkoutPhone");
    const addressEl = document.getElementById("checkoutAddress");
    const cityEl = document.getElementById("checkoutCity");
    const stateEl = document.getElementById("checkoutState");
    const pinEl = document.getElementById("checkoutPin");

    if (!nameEl.value || !emailEl.value || !phoneEl.value || !addressEl.value || !cityEl.value || !stateEl.value || !pinEl.value) {
        showToast("Please fill in all delivery details.");
        return;
    }

    order.customer_details = {
        name: nameEl.value.trim(),
        email: emailEl.value.trim(),
        phone: phoneEl.value.trim(),
        address: addressEl.value.trim(),
        city: cityEl.value.trim(),
        state: stateEl.value.trim(),
        pin: pinEl.value.trim()
    };

    const originalText =
        confirmButton.textContent;

    confirmButton.disabled =
        true;

    confirmButton.textContent =
        "RazorGuard is verifying your purchase…";

    try {

        // ==================================================
        // STEP 1 — CONFIRM ORDER
        // ==================================================

        const confirmationResponse =
            await fetch(
                "/api/checkout/confirm",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        order: order
                    })
                }
            );

        let confirmationData;

        try {

            confirmationData =
                await confirmationResponse.json();

        } catch (jsonError) {

            throw new Error(
                "The server returned an invalid confirmation response."
            );
        }

        if (
            !confirmationResponse.ok ||
            !confirmationData.success
        ) {

            throw new Error(
                confirmationData.error ||
                confirmationData.message ||
                "Unable to confirm checkout."
            );
        }

        if (
            confirmationData.status !==
            "confirmed"
        ) {

            throw new Error(
                "Checkout confirmation was not accepted."
            );
        }

        const confirmedOrder =
            confirmationData.order;

        if (!confirmedOrder) {

            throw new Error(
                "The confirmation response is missing the order."
            );
        }

        // ==================================================
        // STEP 2 — STORE CONFIRMED ORDER
        // ==================================================

        currentCheckout = {

            order:
                confirmedOrder,

            verification:
                checkoutData.verification,

            paymentProvider:
                checkoutData.payment_provider,

            testMode:
                confirmationData.test_mode === true,

            confirmed:
                true
        };

        window.razorGuardCheckout =
            currentCheckout;

        confirmButton.textContent =
            "Creating Payment...";

        // ==================================================
        // STEP 3 — CREATE RAZORPAY PAYMENT ORDER
        // ==================================================

        const paymentOrderResponse =
            await fetch(
                "/api/checkout/payment-order",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        order:
                            confirmedOrder
                    })
                }
            );

        let paymentData;

        try {

            paymentData =
                await paymentOrderResponse.json();

        } catch (jsonError) {

            throw new Error(
                "The server returned an invalid payment response."
            );
        }

        if (
            !paymentOrderResponse.ok ||
            !paymentData.success
        ) {

            throw new Error(
                paymentData.error ||
                paymentData.message ||
                "Unable to create Razorpay payment order."
            );
        }

        if (
            paymentData.status !==
            "payment_pending"
        ) {

            throw new Error(
                "Razorpay payment order was not created."
            );
        }

        // ==================================================
        // STEP 4 — VALIDATE RAZORPAY RESPONSE
        // ==================================================

        const razorpayOrder =
            paymentData.razorpay_order;

        const razorpayKeyId =
            paymentData.razorpay_key_id;

        if (!razorpayOrder) {

            throw new Error(
                "Razorpay order information is missing."
            );
        }

        if (!razorpayOrder.id) {

            throw new Error(
                "Razorpay order ID is missing."
            );
        }

        if (!razorpayKeyId) {

            throw new Error(
                "Razorpay Key ID is missing from the server response."
            );
        }

        // ==================================================
        // STEP 5 — CHECK RAZORPAY SDK
        // ==================================================

        if (
            typeof window.Razorpay !==
            "function"
        ) {

            throw new Error(
                "Razorpay Checkout SDK is not loaded. Please refresh the page."
            );
        }

        const razorpayAmount =
            Number(
                razorpayOrder.amount
            );

        if (
            !Number.isFinite(
                razorpayAmount
            ) ||
            razorpayAmount <= 0
        ) {

            throw new Error(
                "Invalid Razorpay payment amount."
            );
        }

        // ==================================================
        // STEP 6 — SAVE PAYMENT STATE
        // ==================================================

        currentCheckout = {

            ...currentCheckout,

            order:
                paymentData.order ||
                confirmedOrder,

            razorpayOrder:
                razorpayOrder,

            razorpayKeyId:
                razorpayKeyId,

            purchaseGuard:
                paymentData.purchase_guard,

            paymentPending:
                true
        };

        window.razorGuardCheckout =
            currentCheckout;

        // (Modal close deferred until after Purchase Protection Panel)

        // ==================================================
        // STEP 8 — PREPARE RAZORPAY OPTIONS
        // ==================================================

        const currency =
            razorpayOrder.currency ||
            confirmedOrder.currency ||
            "INR";

        const productItems =
            Array.isArray(
                confirmedOrder.items
            )
                ? confirmedOrder.items
                : [];

        const productName =
            productItems.length > 0
                ? productItems[0].name ||
                  "RazorGuard AI Order"
                : "RazorGuard AI Order";

        const razorpayOptions = {

            // PUBLIC KEY ONLY
            key:
                razorpayKeyId,

            // AMOUNT IS IN PAISE
            amount:
                razorpayAmount,

            currency:
                currency,

            name:
                "RazorGuard AI",

            description:
                productName,

            order_id:
                razorpayOrder.id,

            prefill: {

                name:
                    "",

                email:
                    "",

                contact:
                    ""
            },

            theme: {

                color:
                    "#111827"
            },

            modal: {

                ondismiss:
                    function () {

                        console.log(
                            "Razorpay checkout dismissed."
                        );

                        showToast(
                            "Payment window closed. Your order is still pending."
                        );
                    }
            },

            // ==================================================
            // PAYMENT SUCCESS
            // ==================================================

  handler:
    async function (
        razorpayResponse
    ) {

        console.log(
            "Razorpay payment response:",
            razorpayResponse
        );

        // ==================================================
        // STEP 1 — VALIDATE RAZORPAY RESPONSE
        // ==================================================

        if (!razorpayResponse) {

            showToast(
                "Razorpay returned an empty payment response."
            );

            return;
        }

        const razorpayPaymentId =
            razorpayResponse.razorpay_payment_id;

        const razorpayOrderId =
            razorpayResponse.razorpay_order_id;

        const razorpaySignature =
            razorpayResponse.razorpay_signature;

        if (!razorpayPaymentId) {

            showToast(
                "Razorpay payment ID is missing."
            );

            return;
        }

        if (!razorpayOrderId) {

            showToast(
                "Razorpay order ID is missing."
            );

            return;
        }

        if (!razorpaySignature) {

            showToast(
                "Razorpay payment signature is missing."
            );

            return;
        }

        // ==================================================
        // STEP 2 — STORE PENDING VERIFICATION STATE
        // ==================================================

        currentCheckout = {

            ...currentCheckout,

            paymentResponse:
                razorpayResponse,

            paymentStatus:
                "received_pending_verification"
        };

        window.razorGuardCheckout =
            currentCheckout;

        showToast(
            "Payment received. Verifying securely..."
        );

        // ==================================================
        // STEP 3 — SEND PAYMENT DATA TO BACKEND
        // ==================================================

        try {

            const verificationResponse =
                await fetch(
                    "/api/checkout/verify-payment",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            order:
                                currentCheckout.order,

                            razorpay_payment_id:
                                razorpayPaymentId,

                            razorpay_order_id:
                                razorpayOrderId,

                            razorpay_signature:
                                razorpaySignature
                        })
                    }
                );

            let verificationData;

            try {

                verificationData =
                    await verificationResponse.json();

            } catch (jsonError) {

                throw new Error(
                    "The server returned an invalid payment verification response."
                );
            }

            // ==================================================
            // STEP 4 — HANDLE VERIFICATION FAILURE
            // ==================================================

            if (
                !verificationResponse.ok ||
                !verificationData.success ||
                verificationData.status !==
                    "payment_verified"
            ) {

                console.error(
                    "Payment verification failed:",
                    verificationData
                );

                currentCheckout = {

                    ...currentCheckout,

                    paymentStatus:
                        "verification_failed",

                    verification:
                        verificationData.verification ||
                        null
                };

                window.razorGuardCheckout =
                    currentCheckout;

                showToast(
                    verificationData.error ||
                    "Payment verification failed."
                );

                return;
            }

            // ==================================================
            // STEP 5 — SERVER VERIFIED PAYMENT
            // ==================================================

            currentCheckout = {

                ...currentCheckout,

                paymentResponse:
                    razorpayResponse,

                paymentStatus:
                    "verified",

                verification:
                    verificationData.verification,

                verifiedPayment:
                    verificationData.payment,

                razorpayOrder:
                    verificationData.razorpay_order,

                audit:
                    verificationData.audit
            };

            window.razorGuardCheckout =
                currentCheckout;

            // ==================================================
            // STEP 6 — SUCCESS UI
            // ==================================================

            showOrderSuccessView(verificationData);

            console.log(
                "RazorGuard payment verification successful:",
                verificationData
            );

            // ==================================================
            // STEP 7 — REFRESH CART
            // ==================================================

            cart = [];

            saveCart();

            updateCartUI();

        } catch (error) {

            console.error(
                "Payment verification request failed:",
                error
            );

            currentCheckout = {

                ...currentCheckout,

                paymentStatus:
                    "verification_error",

                verificationError:
                    error.message
            };

            window.razorGuardCheckout =
                currentCheckout;

            showToast(
                error.message ||
                "Unable to verify payment with the server."
            );
        }
    }

    };

        // ==================================================
        // STEP 9 — CREATE RAZORPAY INSTANCE
        // ==================================================

        const razorpay =
            new window.Razorpay(
                razorpayOptions
            );

        // ==================================================
        // STEP 10 — PAYMENT FAILURE
        // ==================================================

        razorpay.on(
            "payment.failed",
            function (
                response
            ) {

                console.error(
                    "Razorpay payment failed:",
                    response
                );

                const description =
                    response &&
                    response.error &&
                    response.error.description
                        ? response.error.description
                        : "Razorpay payment failed.";

                currentCheckout = {

                    ...currentCheckout,

                    paymentStatus:
                        "failed",

                    paymentError:
                        response &&
                        response.error
                            ? response.error
                            : response
                };

                window.razorGuardCheckout =
                    currentCheckout;

                showToast(
                    description
                );
            }
        );

        // ==================================================
        // STEP 11 — RENDER RAZORGUARD PROTECTION PANEL
        // ==================================================

        if (modal) {
            const checks = paymentData.purchase_guard.checks || {};
            const decision = paymentData.purchase_guard.decision;
            const risk_level = (paymentData.purchase_guard.risk_level || 'unknown').toLowerCase();
            const isAllowed = decision === 'allowed';
            
            modal.innerHTML = `
                <div class="modal-content razorguard-premium-panel">
                    <div class="panel-header">
                        <span class="shield-icon">🛡</span>
                        <h2>RAZORGUARD PURCHASE PROTECTION</h2>
                        <p>Independent security verification</p>
                    </div>
                    <div class="panel-body">
                        <div class="risk-widget risk-${risk_level}">
                            <div class="risk-score-circle">
                                <span class="risk-score-value">${paymentData.purchase_guard.risk_score}</span>
                                <span class="risk-score-max">/ 100</span>
                            </div>
                            <div class="risk-level-label">${risk_level.toUpperCase()} RISK</div>
                        </div>
                        
                        <div class="security-verification">
                            <h3>SECURITY VERIFICATION</h3>
                            <ul class="check-list">
                                <li class="scan-step slide-in-1">
                                    <span class="scan-label">Product price integrity</span>
                                    <span class="scan-status ${isAllowed ? 'verified' : 'failed'}">
                                        ${isAllowed ? '✓ VERIFIED' : 'FAILED'}
                                    </span>
                                </li>
                                <li class="scan-step slide-in-2">
                                    <span class="scan-label">Order total integrity</span>
                                    <span class="scan-status ${checks.total_valid ? 'verified' : 'failed'}">
                                        ${checks.total_valid ? '✓ VERIFIED' : 'FAILED'}
                                    </span>
                                </li>
                                <li class="scan-step slide-in-3">
                                    <span class="scan-label">User confirmation</span>
                                    <span class="scan-status ${checks.confirmation_valid ? 'verified' : 'failed'}">
                                        ${checks.confirmation_valid ? '✓ VERIFIED' : 'FAILED'}
                                    </span>
                                </li>
                                <li class="scan-step slide-in-4">
                                    <span class="scan-label">Currency validation</span>
                                    <span class="scan-status ${checks.currency_valid ? 'verified' : 'failed'}">
                                        ${checks.currency_valid ? '✓ VERIFIED' : 'FAILED'}
                                    </span>
                                </li>
                                <li class="scan-step slide-in-5">
                                    <span class="scan-label">Payment provider</span>
                                    <span class="scan-status ${checks.payment_provider_valid ? 'verified' : 'failed'}">
                                        ${checks.payment_provider_valid ? '✓ VERIFIED' : 'FAILED'}
                                    </span>
                                </li>
                            </ul>
                        </div>
                        
                        <hr class="panel-divider">
                        
                        <div class="security-boundary-visual slide-in-6">
                            <div class="boundary-row">
                                <div class="boundary-node ai">AI DECISION</div>
                                <div class="boundary-arrow">→</div>
                                <div class="boundary-node security">SECURITY BOUNDARY</div>
                            </div>
                            <div class="boundary-arrow-down">↓</div>
                            <div class="boundary-row">
                                <div class="boundary-node razorpay">RAZORPAY CHECKOUT</div>
                            </div>
                        </div>
                        
                        <div class="decision-status slide-in-7 risk-${risk_level}">
                            <span class="decision-dot"></span>
                            ${isAllowed ? 'SAFE TO CONTINUE' : 'PURCHASE BLOCKED'}
                        </div>
                        
                        <div class="panel-actions slide-in-8">
                            ${isAllowed 
                                ? '<button id="razorguardContinueBtn" class="continue-btn">Continue to Razorpay &rarr;</button>' 
                                : '<button id="razorguardCancelBtn" class="cancel-btn">Return to Cart</button>'}
                        </div>
                    </div>
                </div>
            `;

            const continueBtn = modal.querySelector("#razorguardContinueBtn");
            if (continueBtn) {
                continueBtn.addEventListener("click", () => {
                    showToast("Purchase verified. Opening secure Razorpay checkout…");
                    if (modal && modal.parentNode) {
                        modal.remove();
                    }
                    try {
                        razorpay.open();
                        console.log(
                            "Razorpay Checkout opened.",
                            {
                                orderId: razorpayOrder.id,
                                amount: razorpayAmount,
                                currency: currency,
                                testMode: paymentData.test_mode === true
                            }
                        );
                    } catch (err) {
                        console.error("Failed to open Razorpay:", err);
                        showToast("Failed to open Razorpay Checkout.");
                    }
                });
            }

            const cancelBtn = modal.querySelector("#razorguardCancelBtn");
            if (cancelBtn) {
                cancelBtn.addEventListener("click", () => {
                    if (modal && modal.parentNode) {
                        modal.remove();
                    }
                });
            }
        } else {
            razorpay.open();
        }

        console.log(
            "RazorGuard Protection Panel rendered.",
            {
                orderId:
                    razorpayOrder.id,

                amount:
                    razorpayAmount,

                currency:
                    currency,

                testMode:
                    paymentData.test_mode === true
            }
        );

    } catch (error) {

        console.error(
            "Checkout / Razorpay error:",
            error
        );

        showToast(
            error.message ||
            "Unable to start Razorpay checkout."
        );

        confirmButton.disabled =
            false;

        confirmButton.textContent =
            originalText;
    }
}
// ======================================================
// ATTRIBUTES
// ======================================================

function renderAttributes(
    attributes
) {

    if (
        !attributes ||
        typeof attributes !== "object"
    ) {

        return "";
    }

    const importantKeys = [

        "wireless",
        "battery_hours",
        "battery_mah",
        "battery_days",

        "noise_cancellation",
        "microphone_quality",

        "camera_mp",

        "ram_gb",
        "storage_gb",
        "processor",

        "gps",
        "heart_rate",
        "water_resistant",

        "comfort",
        "lightweight",

        "cordless",
        "portable",

        "capacity_liters",
        "power_watts",

        "suction_power",
        "resistance"
    ];

    let html = "";

    importantKeys.forEach(
        key => {

            if (
                attributes[key] === undefined ||
                attributes[key] === null ||
                attributes[key] === ""
            ) {

                return;
            }

            const value =
                attributes[key];

            const text =
                `${formatKey(key)}: ${formatAttributeValue(
                    key,
                    value
                )}`;

            html += `

                <div class="attribute">

                    ${escapeHtml(text)}

                </div>

            `;
        }
    );

    return html;
}

// ======================================================
// WHY THIS MATCHES
// ======================================================

function renderWhy(
    items
) {

    if (
        !Array.isArray(items) ||
        !items.length
    ) {

        return `

            <div class="why-item">

                Good overall match

            </div>

        `;
    }

    return items
        .slice(
            0,
            6
        )
        .map(
            item => `

                <div class="why-item">

                    ✓ ${escapeHtml(item)}

                </div>

            `
        )
        .join("");
}

// ======================================================
// LOADING
// ======================================================

function setLoading(
    loading
) {

    searchBtn.disabled =
        loading;

    if (loading) {

        searchText.classList.add(
            "hidden"
        );

        loadingText.classList.remove(
            "hidden"
        );

        searchBtn.setAttribute(
            "aria-busy",
            "true"
        );

    } else {

        searchText.classList.remove(
            "hidden"
        );

        loadingText.classList.add(
            "hidden"
        );

        searchBtn.removeAttribute(
            "aria-busy"
        );
    }
}

// ======================================================
// ERROR
// ======================================================

function showError(
    message
) {

    errorBox.textContent =
        "⚠️ " + message;

    errorBox.classList.remove(
        "hidden"
    );
}

function hideError() {

    errorBox.classList.add(
        "hidden"
    );

    errorBox.textContent =
        "";
}

// ======================================================
// TOAST
// ======================================================

let toastTimer = null;

function showToast(
    message
) {

    if (!cartToast) {
        return;
    }

    cartToast.textContent =
        message;

    cartToast.classList.remove(
        "hidden"
    );

    if (toastTimer) {

        clearTimeout(
            toastTimer
        );
    }

    toastTimer =
        setTimeout(
            () => {

                cartToast.classList.add(
                    "hidden"
                );

            },
            2500
        );
}

// ======================================================
// EXAMPLE BUTTONS
// ======================================================

document
    .querySelectorAll(
        ".example-btn"
    )
    .forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    input.value =
                        button.textContent.trim();

                    input.focus();
                }
            );
        }
    );

// ======================================================
// ENTER KEY
// ======================================================

input.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            searchProducts();
        }
    }
);

// ======================================================
// SEARCH BUTTON
// ======================================================

searchBtn.addEventListener(
    "click",
    searchProducts
);

// ======================================================
// FORMAT NUMBER
// ======================================================

function formatNumber(
    value
) {

    const number =
        Number(value);

    if (
        !Number.isFinite(number)
    ) {

        return "0";
    }

    return number.toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 2
        }
    );
}

// ======================================================
// FORMAT KEY
// ======================================================

function formatKey(
    key
) {

    return String(key)
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );
}

// ======================================================
// FORMAT ATTRIBUTE
// ======================================================

function formatAttributeValue(
    key,
    value
) {

    if (
        typeof value === "boolean"
    ) {

        return value
            ? "Yes"
            : "No";
    }

    if (
        key === "camera_mp"
    ) {

        return `${value} MP`;
    }

    if (
        key === "ram_gb"
    ) {

        return `${value} GB`;
    }

    if (
        key === "storage_gb"
    ) {

        return `${value} GB`;
    }

    if (
        key === "battery_hours"
    ) {

        return `${value} hrs`;
    }

    if (
        key === "battery_mah"
    ) {

        return `${value} mAh`;
    }

    if (
        key === "battery_days"
    ) {

        return `${value} days`;
    }

    if (
        key === "power_watts"
    ) {

        return `${value} W`;
    }

    if (
        key === "capacity_liters"
    ) {

        return `${value} L`;
    }

    if (
        key === "suction_power"
    ) {

        return `${value} Pa`;
    }

    return String(value);
}

// ======================================================
// PRICE EXTRACTION
// ======================================================

function extractPrice(
    text
) {

    if (!text) {
        return 0;
    }

    const cleaned =
        String(text)
            .replace(
                /[₹,\s]/g,
                ""
            );

    const value =
        parseFloat(
            cleaned
        );

    return Number.isFinite(value)
        ? value
        : 0;
}

// ======================================================
// RATING EXTRACTION
// ======================================================

function extractRating(
    text
) {

    if (!text) {
        return 0;
    }

    const match =
        String(text).match(
            /(\d+(?:\.\d+)?)/
        );

    if (!match) {
        return 0;
    }

    const value =
        parseFloat(
            match[1]
        );

    return Number.isFinite(value)
        ? value
        : 0;
}

// ======================================================
// STOCK EXTRACTION
// ======================================================

function extractStock(
    text
) {

    if (!text) {
        return 0;
    }

    const match =
        String(text).match(
            /(\d+)\s+available/i
        );

    if (!match) {
        return 0;
    }

    return parseInt(
        match[1],
        10
    );
}

// ======================================================
// NORMALIZE URL
// ======================================================

function normalizeUrl(
    value
) {

    if (
        !value ||
        value === "nan" ||
        value === "None" ||
        value === "null"
    ) {

        return "";
    }

    const url =
        String(value).trim();

    if (!url) {
        return "";
    }

    if (
        url.startsWith(
            "http://"
        ) ||
        url.startsWith(
            "https://"
        ) ||
        url.startsWith(
            "/"
        )
    ) {

        return url;
    }

    return "";
}

// ======================================================
// ESCAPE HTML
// ======================================================

function escapeHtml(
    value
) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}

// ======================================================
// INITIAL UI
// ======================================================

updateCartUI();

// ======================================================
// ORDER SUCCESS AND HISTORY VIEWS
// ======================================================

function showOrderSuccessView(verificationData) {
    // Hide other views
    const mainSearchView = document.getElementById("main-search-view");
    if (mainSearchView) mainSearchView.classList.add("hidden");
    const cartModal = document.getElementById("cart-modal") || document.getElementById("cartSection");
    if (cartModal) cartModal.classList.add("hidden");
    const checkoutModal = document.getElementById("checkout-modal");
    if (checkoutModal) checkoutModal.classList.add("hidden");

    // Show order success view
    const successView = document.getElementById("order-success-view");
    if (successView) {
        successView.classList.remove("hidden");
        const idsContainer = document.getElementById("successOrderIds");
        if (idsContainer) {
            idsContainer.innerHTML = `Order: <span id="success-order-id" style="color:#fff">${verificationData.internal_order_id || "N/A"}</span> &nbsp;|&nbsp; Payment: <span id="success-razorpay-id" style="color:#fff">${verificationData.payment_id || "N/A"}</span>`;
        }
    }
}

async function fetchOrders() {
    try {
        const res = await fetch("/api/orders");
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) {
            renderOrders(data.data || data.orders);
        }
    } catch (e) {
        console.error("Error fetching orders:", e);
    }
}

function renderOrders(orders) {
    const list = document.getElementById("ordersList");
    if (!list) return;
    
    if (!orders || orders.length === 0) {
        list.innerHTML = `<div style="text-align:center; padding:40px; color:#a3abc0;">
            <div style="font-size:32px; margin-bottom:15px;">📦</div>
            <p style="font-size:16px;">No orders yet.</p>
            <p style="font-size:13px; color:#69748a;">Complete a purchase to see your order history here.</p>
        </div>`;
        return;
    }

    list.innerHTML = orders.map(order => `
        <div class="cart-item" style="padding: 18px;">
            <div>
                <div style="font-size:14px; font-weight:800; color:white; margin-bottom:6px;">${order.internal_order_id}</div>
                <div style="font-size:12px; color:var(--muted); margin-bottom:4px;">${order.items ? order.items.map(i => i.name).join(', ') : ''}</div>
                <div style="font-size:12px; color:var(--muted-2);">${order.paid_at ? new Date(order.paid_at).toLocaleString() : ''}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:16px; font-weight:800; color:white; margin-bottom:6px;">₹${Number(order.total).toLocaleString('en-IN')}</div>
                <div class="status" style="margin-bottom:8px;">
                    <span class="status-dot"></span>${order.status}
                </div>
                <div style="margin-top: 4px;">
                    <button onclick="showOrderDetails('${order.internal_order_id}')" class="add-to-cart-button" style="padding: 8px 12px;">View Details</button>
                </div>
            </div>
        </div>
    `).join("");
}

async function showOrderDetails(orderId) {
    try {
        const res = await fetch(`/api/orders/${orderId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        const order = data.data || data.order;
        if (!data.success || !order) return;

        // Hide other views, show details
        const ordersView = document.getElementById("orders-view");
        if (ordersView) ordersView.classList.add("hidden");
        const successView = document.getElementById("order-success-view");
        if (successView) successView.classList.add("hidden");
        
        const detailsView = document.getElementById("order-details-view");
        if (detailsView) detailsView.classList.remove("hidden");

        // Populate order heading
        const detailOrderId = document.getElementById("detailOrderId");
        if (detailOrderId) detailOrderId.textContent = order.internal_order_id || orderId;
        
        const detailOrderDate = document.getElementById("detailOrderDate");
        if (detailOrderDate) detailOrderDate.textContent = order.paid_at ? new Date(order.paid_at).toLocaleString() : (order.created_at ? new Date(order.created_at).toLocaleString() : "");

        // Populate items
        const detailOrderItems = document.getElementById("detailOrderItems");
        if (detailOrderItems && order.items) {
            detailOrderItems.innerHTML = order.items.map(item => `
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:14px; color:#e0e5eb;">
                    <div>${item.name} <span style="color:#69748a;">× ${item.quantity}</span></div>
                    <div style="font-weight:600;">₹${Number(item.price).toLocaleString('en-IN')}</div>
                </div>
            `).join("");
        }

        // Populate payment info
        const detailPaymentInfo = document.getElementById("detailPaymentInfo");
        if (detailPaymentInfo) {
            detailPaymentInfo.innerHTML = `
                <div><span style="color:#69748a;">Status</span></div><div style="font-weight:600; color:#35d07f; text-transform:uppercase;">${order.status}</div>
                <div><span style="color:#69748a;">Total</span></div><div style="font-weight:600;">₹${Number(order.total).toLocaleString('en-IN')}</div>
                <div><span style="color:#69748a;">Currency</span></div><div>${order.currency || 'INR'}</div>
                <div><span style="color:#69748a;">Razorpay Order</span></div><div style="font-size:12px;">${order.razorpay_order_id || 'N/A'}</div>
                <div><span style="color:#69748a;">Payment ID</span></div><div style="font-size:12px;">${order.razorpay_payment_id || 'N/A'}</div>
                <div><span style="color:#69748a;">Paid At</span></div><div style="font-size:12px;">${order.paid_at ? new Date(order.paid_at).toLocaleString() : 'N/A'}</div>
            `;
        }

        // Populate Purchase Guard report
        const detailGuardScore = document.getElementById("detailGuardScore");
        if (detailGuardScore) {
            const riskScore = order.purchase_guard_risk_score;
            const riskLevel = order.purchase_guard_risk_level || "unknown";
            const decision = order.purchase_guard_decision || "N/A";
            const riskClass = riskLevel.toLowerCase() === "low" ? "risk-low" : riskLevel.toLowerCase() === "medium" ? "risk-medium" : "risk-high";
            
            detailGuardScore.className = riskClass;
            detailGuardScore.innerHTML = `
                <div class="risk-score-circle" style="width:60px;height:60px;">
                    <span class="risk-score-value" style="font-size:18px;">${riskScore != null ? riskScore : '?'}</span>
                    <span class="risk-score-max">/100</span>
                </div>
                <div>
                    <div class="risk-level-label" style="font-size:13px;">${riskLevel.toUpperCase()} RISK</div>
                    <div style="font-size:12px; color:#a3abc0; margin-top:4px;">Decision: <strong style="color:#e0e5eb;">${decision.toUpperCase()}</strong></div>
                </div>
            `;
        }

        // Populate security checks
        const detailGuardChecks = document.getElementById("detailGuardChecks");
        if (detailGuardChecks) {
            const checks = order.purchase_guard_checks || {};
            if (typeof checks === 'object' && Object.keys(checks).length > 0) {
                detailGuardChecks.innerHTML = Object.entries(checks).map(([name, result]) => {
                    const passed = result === true || result === "passed" || result === "pass";
                    return `<li class="scan-step">
                        <span>${name.replace(/_/g, ' ')}</span>
                        <span class="scan-status ${passed ? 'verified' : 'failed'}">${passed ? '✓ PASSED' : '✗ FAILED'}</span>
                    </li>`;
                }).join("");
            } else {
                detailGuardChecks.innerHTML = '<li class="scan-step"><span style="color:#69748a;">No check data available</span></li>';
            }
        }

        // Populate explanation
        const detailGuardExplanation = document.getElementById("detailGuardExplanation");
        if (detailGuardExplanation) {
            detailGuardExplanation.textContent = order.purchase_guard_decision === "allowed" 
                ? "This transaction was verified by Purchase Guard before Razorpay order creation."
                : "Purchase Guard security analysis for this order.";
        }

    } catch (e) {
        console.error("Error viewing order details:", e);
    }
}

// Setup My Orders button
document.addEventListener("DOMContentLoaded", () => {
    // "My Orders" button in the header (HTML id: ordersButton)
    const myOrdersBtn = document.getElementById("ordersButton");
    if (myOrdersBtn) {
        myOrdersBtn.addEventListener("click", () => {
            // Hide all other views
            const hero = document.querySelector(".hero");
            if (hero) hero.classList.add("hidden");
            const results = document.getElementById("results");
            if (results) results.classList.add("hidden");
            const cartSection = document.getElementById("cartSection");
            if (cartSection) cartSection.classList.add("hidden");
            const successView = document.getElementById("order-success-view");
            if (successView) successView.classList.add("hidden");
            const detailsView = document.getElementById("order-details-view");
            if (detailsView) detailsView.classList.add("hidden");

            // Show orders view
            const ordersView = document.getElementById("orders-view");
            if (ordersView) ordersView.classList.remove("hidden");
            fetchOrders();
        });
    }

    // "Back to Shop" button from My Orders view
    const backToShopFromOrdersBtn = document.getElementById("backToShopFromOrdersBtn");
    if (backToShopFromOrdersBtn) {
        backToShopFromOrdersBtn.addEventListener("click", () => {
            const ordersView = document.getElementById("orders-view");
            if (ordersView) ordersView.classList.add("hidden");
            
            // Show dashboard elements
            const hero = document.querySelector(".hero");
            if (hero) hero.classList.remove("hidden");
            
            // Also show results if there was a previous search
            const results = document.getElementById("results");
            // We check if the products div has any children (meaning a search was done)
            const products = document.getElementById("products");
            if (results && products && products.innerHTML.trim() !== "") {
                results.classList.remove("hidden");
            }
        });
    }

    // "Back to Orders" button in Order Details view (HTML id: backToOrdersBtn)
    const backBtn = document.getElementById("backToOrdersBtn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            const detailsView = document.getElementById("order-details-view");
            if (detailsView) detailsView.classList.add("hidden");
            const ordersView = document.getElementById("orders-view");
            if (ordersView) ordersView.classList.remove("hidden");
        });
    }

    // "Continue Shopping" from Order Success
    const continueBtn = document.getElementById("continueShoppingBtn");
    if (continueBtn) {
        continueBtn.addEventListener("click", () => {
            const successView = document.getElementById("order-success-view");
            if (successView) successView.classList.add("hidden");
            const hero = document.querySelector(".hero");
            if (hero) hero.classList.remove("hidden");
        });
    }

    // "View Order" from Order Success - navigate to order details
    const viewOrderBtn = document.getElementById("viewSuccessOrderBtn");
    if (viewOrderBtn) {
        viewOrderBtn.addEventListener("click", () => {
            // Try to get the order ID from the success view
            const orderIdEl = document.getElementById("success-order-id");
            const orderId = orderIdEl ? orderIdEl.textContent : null;
            if (orderId && orderId !== "N/A") {
                const successView = document.getElementById("order-success-view");
                if (successView) successView.classList.add("hidden");
                showOrderDetails(orderId);
            }
        });
    }
});

// ======================================================
// JUDGE MODE OBSERVABILITY
// ======================================================

function updateJudgeMode(stepId, status) {
    const el = document.getElementById(stepId);
    if (!el) return;
    el.className = "judge-step " + status;
    const icon = el.querySelector(".j-icon");
    if (icon) {
        if (status === "completed") icon.textContent = "✓";
        else if (status === "in-progress") icon.textContent = "→";
        else if (status === "blocked") icon.textContent = "✕";
        else icon.textContent = "○";
    }
}

function resetJudgeMode() {
    const steps = document.querySelectorAll(".judge-step");
    steps.forEach(el => {
        el.className = "judge-step pending";
        const icon = el.querySelector(".j-icon");
        if (icon) icon.textContent = "○";
    });
    // Reset layers specifically
    const aiTitle = document.querySelector("#judgeLayerAI").previousElementSibling;
    if (aiTitle) aiTitle.textContent = "AI UNDERSTANDING";
    const appTitle = document.querySelector("#judgeLayerApp").previousElementSibling;
    if (appTitle) appTitle.textContent = "APPLICATION ENFORCEMENT";
    
    // Clear out any dynamic blocked reason nodes
    const blockedReason = document.getElementById("j-step-blocked");
    if (blockedReason) blockedReason.remove();
}

function handleJudgeModeStage(stage, status) {
    if (stage === "intent_parser" || stage === "intent_normalizer") {
        updateJudgeMode('j-step-intent', status === 'completed' ? 'completed' : 'in-progress');
    }
    else if (stage === "catalog_search") {
        updateJudgeMode('j-step-catalog', status === 'completed' ? 'completed' : 'in-progress');
    }
    else if (stage === "product_ranking") {
        updateJudgeMode('j-step-rank', status === 'completed' ? 'completed' : 'in-progress');
    }
}

function handleJudgeModeResult(data) {
    if (data.merchant_insight) {
        // Zero-match flow
        updateJudgeMode('j-step-intent', 'completed');
        updateJudgeMode('j-step-catalog', 'completed');
        
        // Transform the UI for zero match
        document.querySelector("#judgeLayerApp").previousElementSibling.textContent = "STRICT CATALOG CHECK";
        const rankEl = document.getElementById('j-step-rank');
        if (rankEl) {
            rankEl.querySelector('.j-text').textContent = "0 exact matches";
            updateJudgeMode('j-step-rank', 'completed');
        }
        
        const explainEl = document.getElementById('j-step-explain');
        if (explainEl) {
            explainEl.className = "judge-step completed";
            explainEl.innerHTML = '<span class="j-icon">✓</span> <span class="j-text">MERCHANT INTELLIGENCE: Gap identified & lost-sale logged</span>';
        }
    } else {
        // Normal recommendation flow
        updateJudgeMode('j-step-intent', 'completed');
        updateJudgeMode('j-step-catalog', 'completed');
        updateJudgeMode('j-step-rank', 'completed');
        updateJudgeMode('j-step-explain', 'completed');
        
        const rankEl = document.getElementById('j-step-rank');
        if (rankEl && rankEl.querySelector('.j-text').textContent !== "Recommendations ranked") {
            rankEl.querySelector('.j-text').textContent = "Recommendations ranked";
        }
        const explainEl = document.getElementById('j-step-explain');
        if (explainEl && explainEl.querySelector('.j-text').textContent !== "Recommendations explained") {
            explainEl.innerHTML = '<span class="j-icon">○</span> <span class="j-text">Recommendations explained</span>';
            updateJudgeMode('j-step-explain', 'completed');
        }
    }
}

function handleJudgeModeFailure(reason) {
    // Show failure
    const layerAppTitle = document.querySelector("#judgeLayerApp").previousElementSibling;
    if (layerAppTitle) layerAppTitle.textContent = "TRANSACTION BLOCKED";
    
    // Create reason node if not exists
    let blockedNode = document.getElementById("j-step-blocked");
    if (!blockedNode) {
        blockedNode = document.createElement("li");
        blockedNode.id = "j-step-blocked";
        blockedNode.className = "judge-step blocked";
        blockedNode.innerHTML = `<span class="j-icon">✕</span> <span class="j-text">Reason: ${reason}</span>`;
        document.getElementById("judgeLayerApp").appendChild(blockedNode);
    }
    
    updateJudgeMode('j-step-confirm', 'completed');
    updateJudgeMode('j-step-price', 'completed');
    updateJudgeMode('j-step-pg', 'blocked');
    updateJudgeMode('j-step-razorpay', 'pending');
    updateJudgeMode('j-step-verify', 'pending');
    
    const razorpayNode = document.getElementById("j-step-razorpay");
    if (razorpayNode) {
        razorpayNode.querySelector('.j-text').textContent = "No unauthorized Razorpay order created";
        updateJudgeMode('j-step-razorpay', 'completed');
    }
}
