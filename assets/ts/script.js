"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var ShoppingCart = /** @class */ (function () {
    function ShoppingCart() {
        this.cart = { items: [], total: 0 };
    }
    ShoppingCart.prototype.addItem = function (item) {
        var existing = this.cart.items.find(function (i) { return i.id === item.id; });
        if (existing) {
            existing.quantity += item.quantity;
        }
        else {
            this.cart.items.push(item);
        }
        this.updateTotal();
    };
    ShoppingCart.prototype.removeItem = function (id) {
        this.cart.items = this.cart.items.filter(function (item) { return item.id !== id; });
        this.updateTotal();
    };
    ShoppingCart.prototype.updateQuantity = function (id, quantity) {
        var item = this.cart.items.find(function (i) { return i.id === id; });
        if (item) {
            item.quantity = Math.max(0, quantity);
            if (item.quantity === 0) {
                this.removeItem(id);
            }
            else {
                this.updateTotal();
            }
        }
    };
    ShoppingCart.prototype.updateTotal = function () {
        this.cart.total = this.cart.items.reduce(function (sum, item) { return sum + item.price * item.quantity; }, 0);
    };
    ShoppingCart.prototype.getCart = function () {
        return this.cart;
    };
    ShoppingCart.prototype.clearCart = function () {
        this.cart = { items: [], total: 0 };
    };
    return ShoppingCart;
}());
exports.default = ShoppingCart;
