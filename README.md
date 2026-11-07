# Lab 4 — Product Catalogue Replication

**Course:** Distributed Systems  
**Student:** Zhuzbai Damir  
**Lab:** 4

## 1. Objective

The goal of this lab is to implement product catalogue replication and compare asynchronous and synchronous replication.

The system demonstrates how the Order Service can receive old product data from a replica before replication is completed.

## 2. Technologies

- Python
- Flask
- Requests
- REST API
- Postman
- Visual Studio Code

## 3. System Architecture

The system contains three separate services:

| Service | Port | Description |
|---|---|---|
| Catalog Primary | 5001 | Stores and updates product data |
| Catalog Replica | 5002 | Receives updates from Primary |
| Order Service | 5003 | Creates orders using Primary or Replica |

Catalog Primary sends product updates to Catalog Replica.

Order Service can read product information from either catalogue using the `catalog_source` parameter.

## 4. Project Structure

```text
Lab4/
├── catalog_primary.py
├── catalog_replica.py
├── orders.py
├── requirements.txt
└── README.md
```

## 5. Installation and Running

Install dependencies:

```powershell
pip install -r requirements.txt
```

Open three separate terminals.

**Terminal 1 — Catalog Primary**

```powershell
python catalog_primary.py
```

**Terminal 2 — Catalog Replica**

```powershell
python catalog_replica.py
```

**Terminal 3 — Order Service**

```powershell
python orders.py
```

All three services must run at the same time.

## 6. Initial Product Data

Both Primary and Replica start with the same product:

```json
{
  "id": 1,
  "name": "Laptop",
  "price": 500000,
  "stock": 10,
  "version": 1
}
```

Every update on Primary increases the product version by 1.

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | localhost:5001/products/1 | Get product from Primary |
| GET | localhost:5002/products/1 | Get product from Replica |
| PUT | localhost:5001/products/1 | Update product |
| POST | localhost:5003/orders | Create order |
| GET | localhost:5001/health | Primary health check |
| GET | localhost:5002/health | Replica health check |
| GET | localhost:5003/health | Order health check |

All API requests were tested using Postman.

## 8. Experiment 1 — Asynchronous Replication

In asynchronous mode, Primary updates the product and immediately returns SUCCESS.

The update is delivered to Replica after 5 seconds.

**Request:**

```http
PUT http://localhost:5001/products/1
```

**JSON Body:**

```json
{
  "price": 450000,
  "mode": "async"
}
```

### Results

| Time | Primary | Replica | Order Price |
|---|---|---|---|
| Before update | 500000, v1 | 500000, v1 | 500000 |
| Immediately after update | 450000, v2 | 500000, v1 | 500000 |
| After 5 seconds | 450000, v2 | 450000, v2 | 450000 |

The Order Service received the old price of 500000 when reading from Replica before the update was delivered.

After replication, the Order Service received the new price of 450000.

**Observation:** Asynchronous replication can cause stale reads because Replica may temporarily contain outdated information.

## 9. Experiment 2 — Synchronous Replication

In synchronous mode, Primary sends the update to Replica and waits for an acknowledgement (ACK).

Primary returns SUCCESS only after receiving the acknowledgement.

**Request:**

```http
PUT http://localhost:5001/products/1
```

**JSON Body:**

```json
{
  "stock": 5,
  "mode": "sync"
}
```

### Results

| Service | Price | Stock | Version |
|---|---|---|---|
| Catalog Primary | 450000 | 5 | 3 |
| Catalog Replica | 450000 | 5 | 3 |
| Order Service (Replica) | 450000 | Read from updated replica | 3 |

### Replica Log

```text
[REPLICA] Applied version 3, price=450000, stock=5
PUT /replicate HTTP/1.1 200
```

### Primary Log

```text
[PRIMARY] Updated to version 3, mode=sync
[PRIMARY] Replica ACK: version 3
PUT /products/1 HTTP/1.1 200
```

The logs confirm that Replica applied version 3 and returned an acknowledgement before Primary completed the update request.

The Order Service successfully created an order using product version 3 from Replica.

## 10. Defence Questions

**1. Why did Order receive the old price immediately after the async update?**

Because Replica had not received the update yet. The update was delayed by 5 seconds.

**2. What is a stale read?**

A stale read happens when a service receives old data instead of the latest updated data.

**3. When does Primary return SUCCESS in async mode?**

Primary returns SUCCESS immediately after saving the update locally, without waiting for Replica.

**4. When does Primary return SUCCESS in sync mode?**

Primary returns SUCCESS after Replica applies the update and sends an acknowledgement.

**5. Why is sync mode usually slower?**

Because Primary must wait for Replica to receive and confirm the update before returning SUCCESS.

## 11. Conclusion

In this lab, I implemented three REST API services using Python and Flask.

I tested asynchronous and synchronous replication using Postman.

In asynchronous mode, Replica returned old data for a short time. In synchronous mode, Primary waited for Replica acknowledgement before returning SUCCESS.

I learned how replication works, what a stale read is, and why asynchronous and synchronous replication have different behavior.
