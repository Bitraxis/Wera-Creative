import Stripe from "stripe";
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
    const cart = req.body.cart;

    const line_items = cart.map(item => ({
    price_data: {
        currency: "eur",
        product_data: { name: item.title },
      unit_amount: Math.round(item.price * 100)
    },
    quantity: item.qty
    }));
    const session = await stripe.checkout.sessions.create({
        mode: "payment",
        line_items,
        success_url: "http://127.0.0.1:5500/shop/success.html",
        cancel_url: "http://127.0.0.1:5500/shop/cart.html"
    });

    res.json({ url: session.url });
}
