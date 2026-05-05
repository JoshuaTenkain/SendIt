# SEND-IT Architecture Documentation

## System Overview

SEND-IT is a courier aggregation platform built with a modern microservices-inspired architecture, consisting of three main components:

1. **Frontend** - Next.js 14 (React) application
2. **Backend** - FastAPI (Python) REST API
3. **Database** - PostgreSQL with SQLAlchemy ORM

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Next.js Frontend (Port 3000)               │  │
│  │  - React Components                                  │  │
│  │  - Client-side Routing                              │  │
│  │  - JWT Token Management                             │  │
│  │  - TailwindCSS Styling                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          FastAPI Backend (Port 8000)                 │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │           API Routers                        │   │  │
│  │  │  - Auth  - Quotes    - Admin               │   │  │
│  │  │  - Addresses - Bookings - Webhooks         │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                      │                              │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │         Service Layer                        │   │  │
│  │  │  - Quote Service                            │   │  │
│  │  │  - Booking Service                          │   │  │
│  │  │  - Payment Service                          │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                      │                              │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │      Courier Adapters                       │   │  │
│  │  │  - Mock Courier (Extensible Pattern)       │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SQLAlchemy ORM
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         PostgreSQL Database (Port 5432)              │  │
│  │                                                       │  │
│  │  Tables:                                             │  │
│  │  - users                - bookings                   │  │
│  │  - addresses            - transactions               │  │
│  │  - couriers             - tracking_events            │  │
│  │  - quotes               - commission_records         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                         │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   PayFast    │         │   Courier    │                 │
│  │   Payment    │         │   APIs       │                 │
│  │   Gateway    │         │  (Future)    │                 │
│  └──────────────┘         └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Frontend Architecture

#### Technology Stack
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **Icons:** Lucide React
- **State Management:** React Hooks (useState, useEffect)
- **HTTP Client:** Fetch API

#### Directory Structure
```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── admin/             # Admin portal
│   │   ├── addresses/         # Address management
│   │   ├── bookings/          # Booking details
│   │   ├── dashboard/         # User dashboard
│   │   ├── login/             # Authentication
│   │   ├── payment/           # Payment callbacks
│   │   ├── quote/             # Quote request
│   │   └── signup/            # Registration
│   ├── components/            # Reusable components
│   │   ├── Navbar.tsx
│   │   ├── Breadcrumbs.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── EmptyState.tsx
│   │   └── StatusBadge.tsx
│   └── lib/                   # Utilities
│       ├── api.ts             # API client
│       └── auth.ts            # Auth helpers
└── public/                    # Static assets
```

#### Key Patterns
- **Client Components:** All pages use `'use client'` directive
- **API Client:** Centralized API calls with token management
- **Route Protection:** Authentication checks in useEffect
- **Error Handling:** Try-catch with user-friendly messages
- **Loading States:** Consistent spinner components

---

### Backend Architecture

#### Technology Stack
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt (passlib)
- **Validation:** Pydantic v2
- **Logging:** Structlog
- **Rate Limiting:** SlowAPI

#### Directory Structure
```
backend/
├── app/
│   ├── main.py                # Application entry point
│   ├── database.py            # Database configuration
│   ├── deps.py                # Dependency injection
│   ├── config.py              # Settings management
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── address.py
│   │   ├── courier.py
│   │   ├── quote.py
│   │   ├── booking.py
│   │   ├── transaction.py
│   │   ├── tracking_event.py
│   │   └── commission_record.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── auth.py
│   │   ├── address.py
│   │   ├── courier.py
│   │   ├── quote.py
│   │   ├── booking.py
│   │   └── transaction.py
│   ├── routers/               # API endpoints
│   │   ├── auth.py
│   │   ├── addresses.py
│   │   ├── quotes.py
│   │   ├── bookings.py
│   │   ├── tracking.py
│   │   ├── admin.py
│   │   └── webhooks.py
│   ├── services/              # Business logic
│   │   ├── quote_service.py
│   │   ├── booking_service.py
│   │   └── payment_service.py
│   └── adapters/              # External integrations
│       └── mock_courier.py
├── alembic/                   # Database migrations
│   └── versions/
├── scripts/                   # Utility scripts
│   └── seed_data.py
└── tests/                     # Test suite
```

#### Layered Architecture

**1. Router Layer** (`routers/`)
- HTTP request handling
- Input validation (Pydantic)
- Response serialization
- Authentication/authorization
- Minimal business logic

**2. Service Layer** (`services/`)
- Business logic implementation
- Transaction management
- Multi-step operations
- External service coordination
- Error handling

**3. Data Access Layer** (`models/`)
- Database models (SQLAlchemy)
- Relationships
- Constraints
- Indexes

**4. Adapter Layer** (`adapters/`)
- External API integrations
- Courier-specific implementations
- Retry logic
- Error normalization

---

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│─────────────│
│ id (PK)     │
│ email       │
│ password    │
│ is_admin    │
└─────────────┘
      │ 1
      │
      │ *
┌─────────────┐         ┌─────────────┐
│   Address   │         │    Quote    │
│─────────────│         │─────────────│
│ id (PK)     │         │ id (PK)     │
│ user_id (FK)│         │ user_id (FK)│
│ label       │         │ pickup_id   │──┐
│ line1       │◄────────│ delivery_id │  │
│ city        │         │ parcel      │  │
│ postal_code │         │ results     │  │
└─────────────┘         │ expires_at  │  │
                        └─────────────┘  │
                              │ 1        │
                              │          │
                              │ *        │
                        ┌─────────────┐  │
                        │   Booking   │  │
                        │─────────────│  │
                        │ id (PK)     │  │
                        │ user_id (FK)│  │
                        │ quote_id(FK)│  │
                        │ courier_id  │──┼──┐
                        │ status      │  │  │
                        │ price_total │  │  │
                        │ tracking_ref│  │  │
                        └─────────────┘  │  │
                              │ 1        │  │
                    ┌─────────┼──────────┘  │
                    │         │             │
                    │ *       │ *           │
          ┌─────────────┐ ┌─────────────┐  │
          │Transaction  │ │TrackingEvent│  │
          │─────────────│ │─────────────│  │
          │ id (PK)     │ │ id (PK)     │  │
          │ booking_id  │ │ booking_id  │  │
          │ amount      │ │ status      │  │
          │ status      │ │ location    │  │
          │ gateway     │ │ timestamp   │  │
          └─────────────┘ └─────────────┘  │
                                            │
                                            │
                                      ┌─────────────┐
                                      │   Courier   │
                                      │─────────────│
                                      │ id (PK)     │
                                      │ code        │
                                      │ name        │
                                      │ is_enabled  │
                                      │ commission% │
                                      └─────────────┘
```

---

## Key Workflows

### 1. Quote Request Flow

```
User Request
    │
    ▼
[Validate Addresses] ──► Address not found ──► 404 Error
    │
    ▼
[Fetch Active Couriers]
    │
    ▼
[Parallel Quote Requests] ──► Timeout/Error ──► Log & Continue
    │                                              │
    ▼                                              │
[Aggregate Results] ◄──────────────────────────────┘
    │
    ▼
[Calculate Pricing]
    │
    ▼
[Store Quote with Expiry]
    │
    ▼
Return Quote Results
```

### 2. Booking & Payment Flow

```
Create Booking Request
    │
    ▼
[Validate Quote] ──► Expired ──► 400 Error
    │
    ▼
[Check Idempotency] ──► Exists ──► Return Existing
    │
    ▼
[Create Booking (pending_payment)]
    │
    ▼
[Create Transaction (pending)]
    │
    ▼
Return Booking
    │
    ▼
User Initiates Payment
    │
    ▼
[Generate PayFast Form]
    │
    ▼
Redirect to PayFast
    │
    ▼
PayFast Processes Payment
    │
    ▼
[Webhook Notification]
    │
    ▼
[Verify Signature]
    │
    ▼
[Update Transaction (completed)]
    │
    ▼
[Update Booking (paid)]
    │
    ▼
[Background: Create Shipment]
    │
    ▼
[Create Tracking Events]
```

### 3. Admin Revenue Tracking

```
Booking Created
    │
    ▼
[Calculate Commission]
    │
    ▼
Payment Confirmed
    │
    ▼
[Create Commission Record]
    │
    ▼
Admin Views Revenue
    │
    ▼
[Aggregate Transactions]
    │
    ▼
[Sum Commission Records]
    │
    ▼
Display Statistics
```

---

## Security Architecture

### Authentication Flow

```
1. User Login
   ├─► Validate credentials
   ├─► Hash password comparison
   └─► Generate JWT token
       ├─► Payload: user_id, email, is_admin
       ├─► Expiry: 7 days
       └─► Algorithm: HS256

2. Protected Endpoint Access
   ├─► Extract Bearer token
   ├─► Verify signature
   ├─► Check expiration
   └─► Load user from database
```

### Authorization Levels

1. **Public Endpoints**
   - `/auth/signup`
   - `/auth/login`

2. **Authenticated Endpoints**
   - `/addresses/*`
   - `/quotes/*`
   - `/bookings/*`
   - `/tracking/*`

3. **Admin Endpoints**
   - `/admin/*`
   - Requires `is_admin = true`

### Security Measures

- **Password Hashing:** bcrypt with salt
- **JWT Tokens:** Signed with secret key
- **CORS:** Configured for frontend origin
- **Rate Limiting:** 100 req/min per IP
- **Input Validation:** Pydantic schemas
- **SQL Injection:** SQLAlchemy parameterization
- **XSS Protection:** React auto-escaping
- **CSRF:** Not needed (stateless JWT)

---

## Database Design

### Indexing Strategy

```sql
-- Performance indexes
CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_quotes_user_id ON quotes(user_id);
CREATE INDEX idx_quotes_expires_at ON quotes(expires_at);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_transactions_booking_id ON transactions(booking_id);
CREATE INDEX idx_tracking_events_booking_id ON tracking_events(booking_id);
```

### Constraints

```sql
-- Data integrity
ALTER TABLE addresses ADD CONSTRAINT check_line1_not_empty 
  CHECK (length(trim(line1)) > 0);

ALTER TABLE addresses ADD CONSTRAINT check_country_code_length 
  CHECK (length(country_code) = 2);

-- Relationships
ALTER TABLE bookings ADD CONSTRAINT fk_booking_user 
  FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE bookings ADD CONSTRAINT fk_booking_quote 
  FOREIGN KEY (quote_id) REFERENCES quotes(id);
```

---

## Scalability Considerations

### Current Architecture
- **Monolithic backend** - Single FastAPI application
- **Single database** - PostgreSQL instance
- **Synchronous processing** - Request-response pattern

### Future Enhancements

1. **Horizontal Scaling**
   - Load balancer (nginx/HAProxy)
   - Multiple backend instances
   - Session-less design (JWT) enables easy scaling

2. **Caching Layer**
   - Redis for quote results
   - Cache courier responses
   - Session storage

3. **Message Queue**
   - RabbitMQ/Celery for background tasks
   - Async shipment creation
   - Email notifications
   - Webhook retries

4. **Database Optimization**
   - Read replicas for reporting
   - Connection pooling (already implemented)
   - Query optimization
   - Partitioning for large tables

5. **Microservices Migration**
   ```
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Quote     │  │   Booking   │  │   Payment   │
   │   Service   │  │   Service   │  │   Service   │
   └─────────────┘  └─────────────┘  └─────────────┘
          │                │                │
          └────────────────┴────────────────┘
                         │
                  ┌─────────────┐
                  │  API Gateway│
                  └─────────────┘
   ```

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  db:
    - PostgreSQL 15
    - Port: 5432
    - Volume: postgres_data
  
  backend:
    - FastAPI application
    - Port: 8000
    - Depends on: db
    - Auto-reload enabled
  
  frontend:
    - Next.js dev server
    - Port: 3000
    - Depends on: backend
    - Hot module replacement
```

### Production Deployment (Recommended)

```
┌─────────────────────────────────────────┐
│           Load Balancer (nginx)         │
│              Port 80/443                │
└─────────────────────────────────────────┘
              │              │
    ┌─────────┴─────┐   ┌───┴──────────┐
    │               │   │              │
┌───▼────┐    ┌─────▼───┐  ┌──────────▼──┐
│Frontend│    │Backend  │  │  Backend    │
│(Static)│    │Instance1│  │  Instance 2 │
└────────┘    └─────────┘  └─────────────┘
                   │              │
              ┌────┴──────────────┴────┐
              │                        │
         ┌────▼─────┐          ┌──────▼────┐
         │PostgreSQL│          │   Redis   │
         │ Primary  │          │   Cache   │
         └──────────┘          └───────────┘
```

---

## Monitoring & Observability

### Logging Strategy

**Backend:**
- Structured logging (structlog)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging
- Error stack traces

**Frontend:**
- Console logging (development)
- Error boundary components
- API error tracking

### Metrics to Monitor

1. **Application Metrics**
   - Request rate
   - Response time (p50, p95, p99)
   - Error rate
   - Active users

2. **Database Metrics**
   - Connection pool usage
   - Query performance
   - Slow queries
   - Table sizes

3. **Business Metrics**
   - Quotes requested
   - Bookings created
   - Payment success rate
   - Revenue per day

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db_connection(),
        "timestamp": datetime.utcnow()
    }
```

---

## Testing Strategy

### Backend Testing

```
tests/
├── test_auth.py           # Authentication tests
├── test_addresses.py      # Address CRUD tests
├── test_quotes.py         # Quote generation tests
├── test_bookings.py       # Booking flow tests
├── test_payments.py       # Payment integration tests
└── test_admin.py          # Admin functionality tests
```

**Test Types:**
- Unit tests (services, utilities)
- Integration tests (API endpoints)
- Database tests (models, queries)

### Frontend Testing (Recommended)

- Component tests (Jest + React Testing Library)
- E2E tests (Playwright/Cypress)
- Visual regression tests

---

## Technology Decisions

### Why FastAPI?
- ✅ High performance (async support)
- ✅ Automatic API documentation
- ✅ Type safety with Pydantic
- ✅ Modern Python features
- ✅ Easy testing

### Why Next.js?
- ✅ Server-side rendering capability
- ✅ File-based routing
- ✅ Built-in optimization
- ✅ Great developer experience
- ✅ Production-ready

### Why PostgreSQL?
- ✅ ACID compliance
- ✅ JSON support (quote results)
- ✅ Robust indexing
- ✅ Mature ecosystem
- ✅ Excellent performance

### Why JWT?
- ✅ Stateless authentication
- ✅ Scalable (no server-side sessions)
- ✅ Cross-domain support
- ✅ Standard format
- ✅ Easy to implement

---

## Extensibility Points

### Adding New Couriers

1. Create adapter in `adapters/new_courier.py`
2. Implement interface:
   ```python
   class NewCourierAdapter:
       async def get_quote(self, request: QuoteRequest) -> QuoteResult
       async def create_shipment(self, booking: Booking) -> ShipmentResult
       async def get_tracking(self, tracking_ref: str) -> TrackingResult
   ```
3. Register in courier service
4. Add courier to database

### Adding New Payment Gateways

1. Create service in `services/new_payment_service.py`
2. Implement payment interface
3. Add webhook handler
4. Update configuration

### Adding New Features

- **Notifications:** Email/SMS service integration
- **Analytics:** Event tracking system
- **Reporting:** Export functionality
- **Multi-currency:** Currency conversion service
- **Insurance:** Insurance calculation module

---

## Performance Characteristics

### Expected Performance

- **Quote Generation:** < 2 seconds (3 couriers)
- **Booking Creation:** < 500ms
- **Payment Initiation:** < 300ms
- **Tracking Fetch:** < 200ms
- **Admin Dashboard:** < 1 second

### Bottlenecks

1. **Courier API Calls** - Mitigated with:
   - Parallel requests
   - Timeouts (5s per courier)
   - Retry logic

2. **Database Queries** - Optimized with:
   - Proper indexing
   - Connection pooling
   - Query optimization

3. **Frontend Rendering** - Improved with:
   - Code splitting
   - Lazy loading
   - Optimized images

---

## Conclusion

The SEND-IT architecture is designed for:
- **Maintainability:** Clear separation of concerns
- **Scalability:** Stateless design, horizontal scaling ready
- **Security:** Multiple layers of protection
- **Extensibility:** Plugin-based courier system
- **Performance:** Async operations, caching, indexing
- **Developer Experience:** Type safety, auto-documentation, hot reload

The system is production-ready and can handle growth through horizontal scaling and strategic optimizations.
