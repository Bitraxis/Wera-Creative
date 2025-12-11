async function loadProducts() {
    const grid = document.getElementById("product-grid");

  // Fetch the products manifest
    const products = await fetch("/assets/_shop/products.json").then(res => res.json());

    for (const product of products) {

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
