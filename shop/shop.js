async function loadProducts() {
    const grid = document.getElementById("product-grid");

  // Fetch the list of product files
    const productFiles = await fetch("/content/products/")
        .then(res => res.text());

  // Extract filenames from directory listing
    const matches = productFiles.match(/href="([^"]+\.json)"/g) || [];
    const files = matches.map(m => m.replace('href="', '').replace('"', ''));

    for (const file of files) {
        const product = await fetch("/content/products/" + file).then(r => r.json());

        const card = document.createElement("div");
        card.className = "product-card";

        card.innerHTML = `
        <img src="${product.image}" alt="${product.name}">
        <h3>${product.name}</h3>
        <div class="price">$${product.price}</div>
        <p>${product.description || ""}</p>
        `;

        grid.appendChild(card);
    }
}

loadProducts();
