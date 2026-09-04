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

// ======================================================
// SEARCH
// ======================================================

async function searchProducts() {

    const message = input.value.trim();

    if (!message) {

        showError(
            "Please describe what product you are looking for."
        );

        return;
    }

    setLoading(true);
    hideError();

    results.classList.add("hidden");

    try {

        const response = await fetch(
            API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );

        let data;

        try {

            data = await response.json();

        } catch (jsonError) {

            throw new Error(
                "The server returned an invalid response."
            );
        }

        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                data.message ||
                "Unable to get recommendations."
            );
        }

        if (
            !data.data ||
            !Array.isArray(data.data.products)
        ) {

            throw new Error(
                "The server response is missing product recommendations."
            );
        }

        renderResults(data.data);

    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        showError(
            error.message ||
            "Something went wrong while searching."
        );

    } finally {

        setLoading(false);
    }
}

// ======================================================
// RENDER RESULTS
// ======================================================

function renderResults(data) {

    results.classList.remove("hidden");

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

    if (!intent) {
        return;
    }

    if (intent.category) {

        addIntentTag(
            "Category",
            intent.category
        );
    }

    if (intent.subcategory) {

        addIntentTag(
            "Product",
            intent.subcategory
        );
    }

    if (
        intent.max_price !== null &&
        intent.max_price !== undefined
    ) {

        addIntentTag(
            "Budget",
            `₹${formatNumber(intent.max_price)}`
        );
    }

    if (
        intent.min_price !== null &&
        intent.min_price !== undefined
    ) {

        addIntentTag(
            "Minimum price",
            `₹${formatNumber(intent.min_price)}`
        );
    }

    if (
        Array.isArray(intent.use_cases) &&
        intent.use_cases.length
    ) {

        intent.use_cases.forEach(
            useCase => {

                addIntentTag(
                    "Use case",
                    useCase
                );
            }
        );
    }

    if (
        intent.preferences &&
        typeof intent.preferences === "object"
    ) {

        Object.entries(
            intent.preferences
        ).forEach(
            ([key, preference]) => {

                if (
                    !preference ||
                    typeof preference !== "object"
                ) {

                    return;
                }

                let value =
                    preference.value;

                const direction =
                    preference.direction;

                if (
                    value === null ||
                    value === undefined
                ) {

                    if (
                        direction === "maximize"
                    ) {

                        value = "Best";

                    } else if (
                        direction === "minimize"
                    ) {

                        value = "Lowest";

                    } else {

                        return;
                    }
                }

                addIntentTag(
                    formatKey(key),
                    formatAttributeValue(
                        key,
                        value
                    )
                );
            }
        );
    }
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
// PRODUCTS
// ======================================================

function renderProducts(products) {

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

    products.forEach(
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

            const score =
                Number(
                    product.match_score
                );

            const scoreText =
                Number.isFinite(score)
                    ? `${score.toFixed(2)}% match`
                    : "Recommended";

            const brand =
                product.brand &&
                product.brand !== "nan"
                    ? product.brand
                    : "";

            const imageUrl =
                normalizeUrl(
                    product.image_url
                );

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
                                    onerror="this.parentElement.style.display='none';"
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
            ".add-to-cart-button"
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
    `;

    document.body.appendChild(
        modal
    );

    const cancelButton =
        document.getElementById(
            "checkoutCancelButton"
        );

    const cancelAction =
        document.getElementById(
            "checkoutCancelAction"
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

    const confirmButton =
        document.getElementById(
            "checkoutConfirmButton"
        );

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

    const originalText =
        confirmButton.textContent;

    confirmButton.disabled =
        true;

    confirmButton.textContent =
        "Confirming...";

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

        // ==================================================
        // STEP 7 — CLOSE OUR CONFIRMATION MODAL
        // ==================================================

        if (
            modal &&
            modal.parentNode
        ) {

            modal.remove();
        }

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

            showToast(
                "Payment verified successfully. Order confirmed! ✓"
            );

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
        // STEP 11 — OPEN RAZORPAY CHECKOUT
        // ==================================================

        razorpay.open();

        console.log(
            "Razorpay Checkout opened.",
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