function loadCart() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    const container = document.getElementById("cart-items");

    if (cart.length === 0) {
        container.innerHTML = "<p>Your cart is empty.</p>";
        return;
    }

    container.innerHTML = cart.map(item => `
        <div class="cart-item">
        <img src="${item.image}" width="80">
        <strong>${item.title}</strong>
        <span>${item.qty} × ${item.price}€</span>
        </div>
    `).join("");
}

document.getElementById("checkout").addEventListener("click", async () => {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];

    const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cart })
    });

    const data = await res.json();
    window.location = data.url;
});

loadCart();
