
from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

REPLICA_URL = "http://127.0.0.1:5002"

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
    return jsonify({"status": "ok", "service": "primary"})


@app.route("/products/1", methods=["GET"])
def get_product():
    with lock:
        return jsonify(product.copy())


def send_to_replica(updated_product, delay=0):
    if delay:
        time.sleep(delay)

    try:
        response = requests.put(
            f"{REPLICA_URL}/replicate",
            json=updated_product,
            timeout=3
        )
        response.raise_for_status()
        print(
            f"[PRIMARY] Replica ACK: "
            f"version {updated_product['version']}",
            flush=True
        )
        return True
    except requests.RequestException as error:
        print(f"[PRIMARY] Replication failed: {error}", flush=True)
        return False


@app.route("/products/1", methods=["PUT"])
def update_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    mode = data.get("mode", "async")

    if mode not in ("async", "sync"):
        return jsonify({"error": "mode must be async or sync"}), 400

    if not any(key in data for key in ("price", "stock")):
        return jsonify({"error": "price or stock required"}), 400

    with lock:
        for field in ("price", "stock"):
            if field in data:
                value = data[field]
                if type(value) is not int or value < 0:
                    return jsonify(
                        {"error": f"{field} must be a non-negative integer"}
                    ), 400
                product[field] = value

        product["version"] += 1
        updated = product.copy()

    print(
        f"[PRIMARY] Updated to version {updated['version']}, "
        f"mode={mode}",
        flush=True
    )

    if mode == "async":
        threading.Thread(
            target=send_to_replica,
            args=(updated, 5),
            daemon=True
        ).start()

        return jsonify({
            "status": "SUCCESS",
            "mode": "async",
            "product": updated
        })

    if send_to_replica(updated):
        return jsonify({
            "status": "SUCCESS",
            "mode": "sync",
            "product": updated
        })

    return jsonify({
        "status": "ERROR",
        "message": "Replica acknowledgement not received",
        "product": updated
    }), 503


if __name__ == "__main__":
    app.run(port=5001, debug=False, threaded=True)
