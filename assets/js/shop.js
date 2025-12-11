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
    `;


    grid.appendChild(card);
  }
}

loadProducts();
