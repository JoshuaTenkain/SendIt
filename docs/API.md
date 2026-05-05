# SEND-IT API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://api.send-it.example.com
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Authentication Endpoints

### Sign Up
Create a new user account.

**Endpoint:** `POST /auth/signup`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+27123456789"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Validation Rules:**
- Email: Valid email format
- Password: 8-128 characters
- First/Last Name: Optional, max 120 characters
- Phone: Optional, max 40 characters

---

### Login
Authenticate and receive JWT token.

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `422 Unprocessable Entity` - Validation error

---

## Address Endpoints

### List Addresses
Get all addresses for the authenticated user.

**Endpoint:** `GET /addresses`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "label": "Home",
    "line1": "123 Main Street",
    "line2": "Apt 4B",
    "city": "Cape Town",
    "province": "Western Cape",
    "postal_code": "8001",
    "country_code": "ZA",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Create Address
Add a new address for the authenticated user.

**Endpoint:** `POST /addresses`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "label": "Office",
  "line1": "456 Business Ave",
  "line2": "Suite 200",
  "city": "Johannesburg",
  "province": "Gauteng",
  "postal_code": "2000",
  "country_code": "ZA"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "label": "Office",
  "line1": "456 Business Ave",
  "line2": "Suite 200",
  "city": "Johannesburg",
  "province": "Gauteng",
  "postal_code": "2000",
  "country_code": "ZA",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Validation Rules:**
- line1: Required, non-empty
- city: Required, non-empty
- postal_code: Required, non-empty
- country_code: Required, 2 characters
- label, line2, province: Optional

---

### Update Address
Modify an existing address.

**Endpoint:** `PATCH /addresses/{address_id}`

**Headers:** `Authorization: Bearer <token>`

**Request Body:** (all fields optional)
```json
{
  "label": "New Home",
  "line1": "789 New Street"
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "label": "New Home",
  "line1": "789 New Street",
  ...
}
```

**Error Responses:**
- `404 Not Found` - Address doesn't exist or doesn't belong to user

---

### Delete Address
Remove an address.

**Endpoint:** `DELETE /addresses/{address_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Address doesn't exist or doesn't belong to user

---

## Quote Endpoints

### Create Quote
Request quotes from multiple couriers.

**Endpoint:** `POST /quotes`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "pickup_address_id": "550e8400-e29b-41d4-a716-446655440000",
  "delivery_address_id": "550e8400-e29b-41d4-a716-446655440001",
  "parcel": {
    "weight_kg": 5.5,
    "length_cm": 30.0,
    "width_cm": 20.0,
    "height_cm": 15.0
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "pickup_address_id": "550e8400-e29b-41d4-a716-446655440000",
  "delivery_address_id": "550e8400-e29b-41d4-a716-446655440001",
  "parcel": {
    "weight_kg": 5.5,
    "length_cm": 30.0,
    "width_cm": 20.0,
    "height_cm": 15.0
  },
  "results": {
    "quotes": [
      {
        "courier_id": "770e8400-e29b-41d4-a716-446655440000",
        "courier_name": "Mock Courier",
        "service_level": "Standard",
        "price_base": 85.50,
        "price_vat": 12.83,
        "price_total": 98.33,
        "estimated_delivery_days": 3,
        "currency": "ZAR"
      },
      {
        "courier_id": "770e8400-e29b-41d4-a716-446655440000",
        "courier_name": "Mock Courier",
        "service_level": "Express",
        "price_base": 125.00,
        "price_vat": 18.75,
        "price_total": 143.75,
        "estimated_delivery_days": 1,
        "currency": "ZAR"
      }
    ]
  },
  "expires_at": "2024-01-15T12:00:00Z",
  "created_at": "2024-01-15T11:30:00Z"
}
```

**Validation Rules:**
- Addresses must exist and belong to user
- Addresses must be different
- Parcel dimensions must be positive numbers
- Quote expires after 30 minutes

---

### Get Quote
Retrieve a specific quote.

**Endpoint:** `GET /quotes/{quote_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  ...
}
```

**Error Responses:**
- `404 Not Found` - Quote doesn't exist or doesn't belong to user

---

## Booking Endpoints

### Create Booking
Create a booking from a quote.

**Endpoint:** `POST /bookings`

**Headers:** 
```
Authorization: Bearer <token>
Idempotency-Key: unique-key-12345
```

**Request Body:**
```json
{
  "quote_id": "660e8400-e29b-41d4-a716-446655440000",
  "courier_id": "770e8400-e29b-41d4-a716-446655440000",
  "courier_service_level": "Express"
}
```

**Response:** `201 Created`
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "quote_id": "660e8400-e29b-41d4-a716-446655440000",
  "courier_id": "770e8400-e29b-41d4-a716-446655440000",
  "courier_service_level": "Express",
  "status": "pending_payment",
  "price_base": 125.00,
  "price_vat": 18.75,
  "price_total": 143.75,
  "commission_amount": 14.38,
  "tracking_reference": null,
  "shipment_id": null,
  "created_at": "2024-01-15T11:45:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

**Idempotency:**
- Same idempotency key returns existing booking
- Prevents duplicate bookings

**Validation Rules:**
- Quote must exist and belong to user
- Quote must not be expired
- Courier and service level must match quote results

---

### List Bookings
Get all bookings for authenticated user.

**Endpoint:** `GET /bookings`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "status": "paid",
    "courier_service_level": "Express",
    "price_total": 143.75,
    "tracking_reference": "MOCK-TRK-12345",
    ...
  }
]
```

---

### Get Booking
Retrieve specific booking details.

**Endpoint:** `GET /bookings/{booking_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "quote": {
    "pickup_address": {...},
    "delivery_address": {...},
    "parcel": {...}
  },
  ...
}
```

---

### Initiate Payment
Generate PayFast payment form data.

**Endpoint:** `POST /bookings/{booking_id}/payment`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "payment_url": "https://sandbox.payfast.co.za/eng/process",
  "payment_data": {
    "merchant_id": "10000100",
    "merchant_key": "46f0cd694581a",
    "amount": "143.75",
    "item_name": "Shipment Booking",
    "return_url": "http://localhost:3000/payment/success?booking_id=...",
    "cancel_url": "http://localhost:3000/payment/cancel?booking_id=...",
    "notify_url": "http://localhost:8000/webhooks/payfast",
    "m_payment_id": "880e8400-e29b-41d4-a716-446655440000",
    "signature": "..."
  }
}
```

**Error Responses:**
- `400 Bad Request` - Booking already paid
- `404 Not Found` - Booking doesn't exist

---

## Tracking Endpoints

### Get Tracking Events
Retrieve tracking history for a booking.

**Endpoint:** `GET /tracking/{booking_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "booking_id": "880e8400-e29b-41d4-a716-446655440000",
    "status": "in_transit",
    "location": "Cape Town Distribution Center",
    "description": "Package is in transit",
    "timestamp": "2024-01-16T08:00:00Z",
    "created_at": "2024-01-16T08:05:00Z"
  },
  {
    "id": "990e8400-e29b-41d4-a716-446655440001",
    "booking_id": "880e8400-e29b-41d4-a716-446655440000",
    "status": "picked_up",
    "location": "Cape Town Pickup Point",
    "description": "Package picked up from sender",
    "timestamp": "2024-01-15T14:00:00Z",
    "created_at": "2024-01-15T14:05:00Z"
  }
]
```

**Note:** Events are returned in reverse chronological order (newest first)

---

## Admin Endpoints

All admin endpoints require admin privileges.

### List Couriers
Get all couriers in the system.

**Endpoint:** `GET /admin/couriers`

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "code": "MOCK",
    "name": "Mock Courier",
    "is_enabled": true,
    "base_markup_pct": 20,
    "commission_pct": 10,
    "rating": 4
  }
]
```

---

### Update Courier
Modify courier settings.

**Endpoint:** `PATCH /admin/couriers/{courier_id}`

**Headers:** `Authorization: Bearer <admin-token>`

**Request Body:**
```json
{
  "is_enabled": false,
  "commission_pct": 12
}
```

**Response:** `200 OK`
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "is_enabled": false,
  "commission_pct": 12,
  ...
}
```

---

### List All Bookings
Get all bookings (admin view).

**Endpoint:** `GET /admin/bookings`

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "paid",
    "price_total": 143.75,
    "commission_amount": 14.38,
    ...
  }
]
```

**Note:** Limited to 100 most recent bookings

---

### List All Transactions
Get all payment transactions.

**Endpoint:** `GET /admin/transactions`

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440000",
    "booking_id": "880e8400-e29b-41d4-a716-446655440000",
    "amount": 143.75,
    "status": "completed",
    "payment_gateway": "payfast",
    "gateway_reference": "1234567",
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:05:00Z"
  }
]
```

---

### Get Revenue Summary
Retrieve platform revenue statistics.

**Endpoint:** `GET /admin/revenue`

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
{
  "total_revenue": 15432.50,
  "total_commission": 1543.25,
  "booking_count": 127,
  "currency": "ZAR"
}
```

---

## Webhook Endpoints

### PayFast Payment Notification
Receive payment confirmation from PayFast.

**Endpoint:** `POST /webhooks/payfast`

**Request Body:** (form-urlencoded)
```
m_payment_id=880e8400-e29b-41d4-a716-446655440000
pf_payment_id=1234567
payment_status=COMPLETE
amount_gross=143.75
signature=...
```

**Response:** `200 OK`

**Security:**
- Validates PayFast signature
- Verifies payment amount
- Updates booking status
- Creates shipment in background

---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message description"
}
```

### Validation Error Format
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "invalid-email"
    }
  ]
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

- **Default:** 100 requests per minute per IP
- **Headers:**
  - `X-RateLimit-Limit` - Request limit
  - `X-RateLimit-Remaining` - Remaining requests
  - `X-RateLimit-Reset` - Reset timestamp

**Rate Limit Exceeded Response:** `429 Too Many Requests`

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test API calls directly
- Download OpenAPI specification

---

## SDK Examples

### Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# Create quote
headers = {"Authorization": f"Bearer {token}"}
quote_data = {
    "pickup_address_id": "...",
    "delivery_address_id": "...",
    "parcel": {
        "weight_kg": 5.0,
        "length_cm": 30.0,
        "width_cm": 20.0,
        "height_cm": 15.0
    }
}
response = requests.post(
    "http://localhost:8000/quotes",
    json=quote_data,
    headers=headers
)
quote = response.json()
```

### JavaScript/TypeScript
```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// Create quote
const quoteResponse = await fetch('http://localhost:8000/quotes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    pickup_address_id: '...',
    delivery_address_id: '...',
    parcel: {
      weight_kg: 5.0,
      length_cm: 30.0,
      width_cm: 20.0,
      height_cm: 15.0
    }
  })
});
const quote = await quoteResponse.json();
```

---

## Versioning

Current API Version: **v1**

The API version is included in the base URL for future compatibility:
```
https://api.send-it.example.com/v1/...
```

---

## Support

For API support and questions:
- Email: api-support@send-it.example.com
- Documentation: https://docs.send-it.example.com
- Status Page: https://status.send-it.example.com
