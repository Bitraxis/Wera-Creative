const cart = new ShoppingCart();

function updateCartDisplay() {
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    cartItemsContainer.innerHTML = '';
    cart.getCart().items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = `${item.name} - $${item.price} x ${item.quantity}`;
        cartItemsContainer.appendChild(li);
    });
    cartTotal.textContent = `Total: $${cart.getCart().total.toFixed(2)}`;
}

document.getElementById('clear-cart').addEventListener('click', () => {
    cart.clearCart();
    updateCartDisplay();
});

// Example of adding items to the cart for demonstration
cart.addItem({ id: '1', name: 'Item 1', price: 10.00, quantity: 1 });
cart.addItem({ id: '2', name: 'Item 2', price: 15.00, quantity: 2 });
updateCartDisplay();