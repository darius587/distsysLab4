
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

CATALOG_URLS = {
    "primary": "http://127.0.0.1:5001",
    "replica": "http://127.0.0.1:5002"
}

orders = {}
next_order_id = 1


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "orders"
    })


@app.route("/orders", methods=["POST"])
def create_order():
    global next_order_id

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    catalog_source = data.get("catalog_source", "primary")

    if product_id != 1:
        return jsonify({"error": "Product not found"}), 404

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    if catalog_source not in CATALOG_URLS:
        return jsonify({
            "error": "catalog_source must be primary or replica"
        }), 400

    catalog_url = CATALOG_URLS[catalog_source]

    try:
        response = requests.get(
            f"{catalog_url}/products/{product_id}",
            timeout=3
        )
        response.raise_for_status()
        product = response.json()

    except requests.RequestException as error:
        return jsonify({
            "error": "Catalog service unavailable",
            "details": str(error)
        }), 503

    if quantity > product["stock"]:
        return jsonify({
            "error": "Not enough stock"
        }), 400

    order = {
        "order_id": next_order_id,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "total_price": product["price"] * quantity,
        "product_version": product["version"],
        "catalog_source": catalog_source
    }

    orders[next_order_id] = order
    next_order_id += 1

    print(
        f"[ORDER] Created order {order['order_id']} "
        f"from {catalog_source}: "
        f"price={order['unit_price']}, "
        f"version={order['product_version']}",
        flush=True
    )

    return jsonify(order), 201


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = orders.get(order_id)

    if order is None:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


if __name__ == "__main__":
    app.run(port=5003, debug=False, threaded=True)
