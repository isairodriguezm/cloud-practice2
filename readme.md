Auth: manda X-API-KEY: TU_LLAVE en cada request.
Endpoints:
GET /health (sin auth)
GET /metrics (sin auth)
GET /products
POST /products body: { "name": "Lapicero", "price": 12.5, "stock": 100 }
GET /products/{id}
PUT /products/{id} body parcial o completo
DELETE /products/{id}
