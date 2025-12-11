async function loadProducts() {
  const grid = document.getElementById("product-grid");

  // Fetch the list of product files from directory listing
  const productFiles = await fetch("/assets/_shop/products/")
    .then(res => res.text());

  // Extract filenames from directory listing
  const matches = productFiles.match(/href="([^"]+\.json)"/g) || [];
  const files = matches.map(m => {
    const fullPath = m.replace('href="', '').replace('"', '');
    return fullPath.split('/').pop(); // Get just the filename
  });
  function addToCart(product) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];

    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ ...product, qty: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    alert("Added to cart!");
  }

  document.addEventListener("click", e => {
    if (e.target.classList.contains("add-to-cart")) {
      const btn = e.target;
      addToCart({
        id: btn.dataset.id,
        title: btn.dataset.title,
        price: parseFloat(btn.dataset.price),
        image: btn.dataset.image
      });
    }
  });

  for (const file of files) {
    const product = await fetch("/assets/_shop/products/" + file).then(r => r.json());

    const card = document.createElement("div");
    card.className = "product-card";

    let priceHTML = `<div class="price">${product.price}€</div>`;
    if (product.sale && product.salePrice) {
      priceHTML = `
        <div class="price-section">
          <span class="price-original">${product.price}€</span>
          <span class="price-sale">${product.salePrice}€</span>
        </div>
      `;
    }

    card.innerHTML = `
      <img src="${product.image}" alt="${product.title}">
      <h3>${product.title}</h3>
      ${priceHTML}
      <p>${product.description || ""}</p>
      <button class="add-to-cart" data-id="${product.id}" data-price="${product.sale ? product.salePrice : product.price}" data-title="${product.title}" data-image="${product.image}">
      Add to Cart
      </button>
    `;


    grid.appendChild(card);
  }
}

loadProducts();
