document.addEventListener('DOMContentLoaded', () => {
  const userInput = document.getElementById('userInput');
  const searchBtn = document.getElementById('searchBtn');
  const searchText = document.getElementById('searchText');
  const loadingText = document.getElementById('loadingText');
  const resultsSection = document.getElementById('resultsSection');
  const productsContainer = document.getElementById('products');
  const intentContent = document.getElementById('intentContent');
  const candidateCount = document.getElementById('candidateCount');
  const errorBox = document.getElementById('errorBox');
  const emptyState = document.getElementById('emptyState');

  const exampleButtons = document.querySelectorAll('.example-btn');

  const currencyFormatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  });

  const setLoading = (isLoading) => {
    searchBtn.disabled = isLoading;
    searchText.classList.toggle('hidden', isLoading);
    loadingText.classList.toggle('hidden', !isLoading);
  };

  const hideAllStates = () => {
    resultsSection.classList.add('hidden');
    errorBox.classList.add('hidden');
    emptyState.classList.add('hidden');
  };

  const showEmptyState = () => {
    hideAllStates();
    emptyState.classList.remove('hidden');
  };

  const showError = (message) => {
    hideAllStates();
    errorBox.textContent = message;
    errorBox.classList.remove('hidden');
  };

  const showResults = () => {
    hideAllStates();
    resultsSection.classList.remove('hidden');
  };

  const renderIntent = (intent) => {
    intentContent.innerHTML = '';

    if (!intent || typeof intent !== 'object') {
      intentContent.textContent = 'No intent detected yet.';
      return;
    }

    const tags = [];

    if (intent.category) tags.push(`Category: ${intent.category}`);
    if (intent.subcategory) tags.push(`Subcategory: ${intent.subcategory}`);
    if (intent.budget && Number(intent.budget) > 0) tags.push(`Budget: ${currencyFormatter.format(Number(intent.budget))}`);
    if (intent.brand) tags.push(`Brand: ${intent.brand}`);
    if (intent.requirements && Array.isArray(intent.requirements)) {
      intent.requirements.slice(0, 4).forEach((item) => tags.push(String(item)));
    }

    if (!tags.length) {
      intentContent.textContent = 'No extra preferences detected.';
      return;
    }

    tags.forEach((tagText) => {
      const tag = document.createElement('span');
      tag.className = 'intent-tag';
      tag.textContent = tagText;
      intentContent.appendChild(tag);
    });
  };

  const normalizeLabel = (key) => {
    const map = {
      camera_mp: 'Camera',
      ram_gb: 'RAM',
      storage_gb: 'Storage',
      battery_mah: 'Battery',
      battery_hours: 'Battery',
      display_size: 'Display',
      display: 'Display',
      processor: 'Processor',
      '5g': '5G',
      bluetooth: 'Bluetooth',
      noise_cancellation: 'Noise Cancellation',
      microphone: 'Microphone',
      cushion: 'Cushioning',
      cushioning: 'Cushioning',
      size: 'Size',
      material: 'Material',
      weight: 'Weight',
      connectivity: 'Connectivity',
      charging: 'Charging',
      resolution: 'Resolution',
      os: 'OS',
      warranty: 'Warranty',
      color: 'Color',
    };

    return map[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const formatAttributeValue = (value) => {
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }

    if (typeof value === 'number') {
      if (Number.isInteger(value)) return String(value);
      return Number(value).toFixed(1).replace(/\.0$/, '');
    }

    return String(value);
  };

  const renderAttributes = (attributes) => {
    if (!attributes || typeof attributes !== 'object') {
      return document.createElement('div');
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'product-attributes';

    const relevantKeys = [
      'camera_mp',
      'ram_gb',
      'storage_gb',
      'battery_mah',
      'battery_hours',
      'display_size',
      'display',
      'processor',
      '5g',
      'noise_cancellation',
      'microphone',
      'cushioning',
      'size',
      'material',
      'weight',
      'connectivity',
      'charging',
      'resolution',
      'os',
      'warranty',
      'color'
    ];

    const selected = relevantKeys
      .filter((key) => Object.prototype.hasOwnProperty.call(attributes, key) && attributes[key] !== null && attributes[key] !== undefined && attributes[key] !== '')
      .slice(0, 4);

    if (!selected.length) {
      Object.keys(attributes)
        .slice(0, 4)
        .forEach((key) => selected.push(key));
    }

    selected.forEach((key) => {
      const chip = document.createElement('span');
      chip.className = 'attr-chip';
      chip.textContent = `${normalizeLabel(key)}: ${formatAttributeValue(attributes[key])}`;
      wrapper.appendChild(chip);
    });

    return wrapper;
  };

  const renderWhyList = (whyList) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'product-why';

    const title = document.createElement('h4');
    title.textContent = 'Why this matches';
    wrapper.appendChild(title);

    const list = document.createElement('ul');
    list.className = 'why-list';

    const items = Array.isArray(whyList) && whyList.length ? whyList : ['Strong match based on your request and budget.'];

    items.slice(0, 4).forEach((reason) => {
      const item = document.createElement('li');
      item.textContent = reason;
      list.appendChild(item);
    });

    wrapper.appendChild(list);
    return wrapper;
  };

  const renderProductCard = (product) => {
    const card = document.createElement('article');
    card.className = 'product-card';

    const imageWrap = document.createElement('div');
    imageWrap.className = 'product-image-wrap';

    const image = document.createElement('img');
    image.className = 'product-image';
    image.alt = product.name || 'Product image';
    image.src = product.image_url || 'https://via.placeholder.com/800x640?text=Product+Image';
    image.loading = 'lazy';
    image.onerror = () => {
      image.src = 'https://via.placeholder.com/800x640?text=Product+Image';
    };

    const badge = document.createElement('span');
    badge.className = 'product-badge';
    badge.textContent = (product.category || 'Product').toUpperCase();

    imageWrap.appendChild(image);
    imageWrap.appendChild(badge);

    const content = document.createElement('div');
    content.className = 'product-content';

    const topLine = document.createElement('div');
    topLine.className = 'product-topline';

    const brand = document.createElement('span');
    brand.className = 'product-brand';
    brand.textContent = product.brand || 'Brand';

    const score = document.createElement('span');
    score.className = 'product-score';
    score.textContent = `${Math.round(Number(product.match_score || 0))}% match`;

    topLine.appendChild(brand);
    topLine.appendChild(score);

    const name = document.createElement('h3');
    name.className = 'product-name';
    name.textContent = product.name || 'Product name';

    const meta = document.createElement('div');
    meta.className = 'product-meta';

    const price = document.createElement('span');
    price.className = 'product-price';
    price.textContent = currencyFormatter.format(Number(product.price || 0));

    const rating = document.createElement('span');
    rating.className = 'product-rating';
    rating.textContent = `★ ${Number(product.rating || 0).toFixed(1)}`;

    meta.appendChild(price);
    meta.appendChild(rating);

    const stock = document.createElement('span');
    const stockValue = Number(product.stock || 0);
    stock.className = `product-stock ${stockValue > 0 ? 'in-stock' : 'out-of-stock'}`;
    stock.textContent = stockValue > 0 ? `In stock (${stockValue})` : 'Out of stock';

    const attrs = renderAttributes(product.attributes);
    const why = renderWhyList(product.why);

    const actions = document.createElement('div');
    actions.className = 'product-actions';

    const viewButton = document.createElement('a');
    viewButton.className = 'action-btn primary';
    viewButton.textContent = 'View Product';

    if (product.product_url) {
      viewButton.href = product.product_url;
      viewButton.target = '_blank';
      viewButton.rel = 'noopener noreferrer';
    } else {
      viewButton.href = '#';
      viewButton.setAttribute('aria-disabled', 'true');
      viewButton.classList.add('disabled');
      viewButton.classList.remove('primary');
      viewButton.classList.add('secondary');
      viewButton.addEventListener('click', (event) => event.preventDefault());
    }

    const buyButton = document.createElement('button');
    buyButton.type = 'button';
    buyButton.className = 'action-btn secondary';
    buyButton.textContent = 'Checkout coming next';
    buyButton.disabled = true;

    actions.appendChild(viewButton);
    actions.appendChild(buyButton);

    content.appendChild(topLine);
    content.appendChild(name);
    content.appendChild(meta);
    content.appendChild(stock);
    content.appendChild(attrs);
    content.appendChild(why);
    content.appendChild(actions);

    card.appendChild(imageWrap);
    card.appendChild(content);

    return card;
  };

  const renderResults = (payload) => {
    const products = Array.isArray(payload?.products) ? payload.products : [];
    const intent = payload?.intent || {};

    renderIntent(intent);
    candidateCount.textContent = `${products.length} product${products.length === 1 ? '' : 's'} matched`;
    productsContainer.innerHTML = '';

    if (!products.length) {
      showError('No products matched your request. Try adjusting the budget, category, or requirements.');
      return;
    }

    showResults();
    products.forEach((product) => {
      productsContainer.appendChild(renderProductCard(product));
    });
  };

  const handleSearch = async () => {
    const message = userInput.value.trim();

    if (!message) {
      showError('Please enter a product request before searching.');
      return;
    }

    setLoading(true);
    hideAllStates();

    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      if (!response.ok || !data?.success) {
        throw new Error(data?.error || 'Something went wrong while fetching recommendations.');
      }

      renderResults(data.data || { products: [], intent: {} });
    } catch (error) {
      showError(error.message || 'Unable to load recommendations right now. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSearch();
    }
  });

  searchBtn.addEventListener('click', handleSearch);

  exampleButtons.forEach((button) => {
    button.addEventListener('click', () => {
      userInput.value = button.textContent.trim();
      userInput.focus();
    });
  });

  showEmptyState();
});
