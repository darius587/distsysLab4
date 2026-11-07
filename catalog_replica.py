
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

product = {
    "id": 1,
    "name": "Laptop",
    "price": 500000,
    "stock": 10,
    "version": 1
}

lock = threading.Lock()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "replica"
    })


@app.route("/products/1", methods=["GET"])
def get_product():
    with lock:
        return jsonify(product.copy())


@app.route("/replicate", methods=["PUT"])
def replicate():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    required = ("id", "name", "price", "stock", "version")

    if any(field not in data for field in required):
        return jsonify({"error": "Missing product fields"}), 400

    if data["id"] != 1 or type(data["version"]) is not int:
        return jsonify({"error": "Invalid product ID or version"}), 400

    with lock:
        if data["version"] <= product["version"]:
            print(
                f"[REPLICA] Ignored old version {data['version']}",
                flush=True
            )
            return jsonify({
                "status": "ACK",
                "version": product["version"],
                "message": "Already applied or newer version exists"
            })

        product.update({
            "id": data["id"],
            "name": data["name"],
            "price": data["price"],
            "stock": data["stock"],
            "version": data["version"]
        })

        print(
            f"[REPLICA] Applied version {product['version']}, "
            f"price={product['price']}, "
            f"stock={product['stock']}",
            flush=True
        )

        return jsonify({
            "status": "ACK",
            "version": product["version"]
        })


if __name__ == "__main__":
    app.run(port=5002, debug=False, threaded=True)
