interface CartItem {
    id: string;
    name: string;
    price: number;
    quantity: number;
}

interface Cart {
    items: CartItem[];
    total: number;
}

class ShoppingCart {
    private cart: Cart = { items: [], total: 0 };

    addItem(item: CartItem): void {
        const existing = this.cart.items.find((i) => i.id === item.id);
        if (existing) {
            existing.quantity += item.quantity;
        } else {
            this.cart.items.push(item);
        }
        this.updateTotal();
    }

    removeItem(id: string): void {
        this.cart.items = this.cart.items.filter((item) => item.id !== id);
        this.updateTotal();
    }

    updateQuantity(id: string, quantity: number): void {
        const item = this.cart.items.find((i) => i.id === id);
        if (item) {
            item.quantity = Math.max(0, quantity);
            if (item.quantity === 0) {
                this.removeItem(id);
            } else {
                this.updateTotal();
            }
        }
    }

    private updateTotal(): void {
        this.cart.total = this.cart.items.reduce(
            (sum, item) => sum + item.price * item.quantity,
            0
        );
    }

    getCart(): Cart {
        return this.cart;
    }

    clearCart(): void {
        this.cart = { items: [], total: 0 };
    }
}

export default ShoppingCart;