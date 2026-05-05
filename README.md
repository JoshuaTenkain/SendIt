# SEND-IT — Courier Aggregation Platform

**Enterprise-grade MVP** for comparing and booking courier services across multiple providers.

Built for the South African market with PayFast payment integration.

---

## 🚀 Quick Start (Docker)

```bash
# Clone and navigate
cd SendIt

# Copy environment template
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed initial data (couriers + test users)
docker-compose exec backend python scripts/seed_data.py

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

> **Note:** You may see a warning about the `version` attribute in `docker-compose.yml` being obsolete. This is safe to ignore or you can remove the `version: '3.8'` line from the file.

**Test Credentials:**

- User: `test@send-it.local` / `pass123`
- Admin: `admin@send-it.local` / `admin123`

---

## 📦 Architecture

### Monolithic MVP Design

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Next.js 14 (TypeScript + Tailwind CSS)
- **Database**: PostgreSQL 15
- **Payments**: PayFast (sandbox + production ready)
- **Email**: SendGrid (optional for MVP)

### Key Features

✅ User authentication (JWT)
✅ Address management
✅ Multi-courier quote comparison
✅ Booking creation with idempotency
✅ Secure PayFast payment integration
✅ Shipment tracking
✅ Admin dashboard (couriers, revenue, bookings)
✅ Courier adapter system (Aramex, The Courier Guy, Pargo, Mock)

---

## 🛠️ Local Development (without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Set up PostgreSQL database (if not using Docker)
# Make sure PostgreSQL is running and create database:
# createdb sendit

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_data.py

# Start dev server
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

> **Note:** The project uses `bcrypt==4.0.1` and `passlib==1.7.4` for password hashing compatibility.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local

# Start dev server
npm run dev
```

Frontend runs at: http://localhost:3000

---

## 📊 Database Schema

### Core Tables

- **users** — User accounts (customers + admins)
- **addresses** — Pickup/delivery addresses
- **couriers** — Courier partner configuration
- **quotes** — Quote requests + normalized results
- **bookings** — Shipment bookings with idempotency
- **transactions** — Payment records (PayFast)
- **tracking_events** — Shipment tracking history
- **commission_records** — Platform commission tracking

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🔌 API Endpoints

### Authentication

- `POST /auth/signup` — Create account
- `POST /auth/login` — Login (returns JWT)

### Addresses

- `GET /addresses` — List user addresses
- `POST /addresses` — Create address
- `PATCH /addresses/{id}` — Update address
- `DELETE /addresses/{id}` — Delete address

### Quotes

- `POST /quotes` — Generate quote comparison
- `GET /quotes/{id}` — Retrieve quote

### Bookings

- `POST /bookings` — Create booking (requires `Idempotency-Key` header)
- `GET /bookings` — List user bookings
- `GET /bookings/{id}` — Get booking details
- `POST /bookings/{id}/payment` — Initiate PayFast payment

### Payments

- `POST /payments/payfast/notify` — PayFast ITN callback (webhook)

### Tracking

- `GET /tracking/{booking_id}` — Get tracking events

### Shipments

- `POST /shipments/{booking_id}/create` — Manually trigger shipment creation
- `POST /shipments/{booking_id}/refresh-tracking` — Refresh tracking data

### Admin (requires admin role)

- `GET /admin/couriers` — List all couriers
- `PATCH /admin/couriers/{id}` — Update courier config
- `GET /admin/bookings` — List all bookings
- `GET /admin/transactions` — List all transactions
- `GET /admin/revenue` — Revenue summary

API Documentation: http://localhost:8000/docs

---

## 🚚 Courier Integration

### Adapter Interface

All couriers implement:

```python
class CourierAdapter:
    async def get_quote(*, pickup, delivery, parcel) -> list[QuoteResult]
    async def create_shipment(*, booking) -> dict
    async def track_shipment(*, tracking_reference) -> list[dict]
```

### Supported Couriers

- **Mock Courier** (development/testing)
- **Aramex** (stub implementation)
- **The Courier Guy** (stub implementation)
- **Pargo** (stub implementation)

To add a new courier:

1. Create adapter in `backend/app/integrations/couriers/`
2. Register in `CourierRegistry.default_adapters()`
3. Add courier record via admin API or seed script

---

## 💳 PayFast Integration

### Sandbox Mode (Default)

Uses PayFast test credentials for development.

### Production Setup

1. Create PayFast merchant account
2. Update `.env`:
   ```
   SENDIT_PAYFAST_MERCHANT_ID=your_merchant_id
   SENDIT_PAYFAST_MERCHANT_KEY=your_merchant_key
   SENDIT_PAYFAST_PASSPHRASE=your_passphrase
   SENDIT_PAYFAST_SANDBOX=false
   ```
3. Configure ITN callback URL in PayFast dashboard:
   ```
   https://yourdomain.com/payments/payfast/notify
   ```

### Payment Flow

1. User creates booking → status: `pending_payment`
2. Frontend calls `/bookings/{id}/payment` → receives PayFast form data
3. User completes payment on PayFast
4. PayFast sends ITN to `/payments/payfast/notify`
5. Backend verifies signature + amount → updates booking to `paid`
6. Background task creates shipment with courier

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Test Coverage

- Quote generation + ranking
- Booking creation + idempotency
- Payment confirmation flow
- Courier adapter mocks

---

## 🔐 Security Features

✅ Password hashing (bcrypt)
✅ JWT authentication
✅ Input validation (Pydantic)
✅ Rate limiting (200 req/min default)
✅ PayFast signature verification
✅ Idempotency protection on bookings
✅ SQL injection protection (SQLAlchemy ORM)

---

## 📈 Deployment

### Production Checklist

- [ ] Change `SENDIT_JWT_SECRET_KEY` to random 32+ char string
- [ ] Set `SENDIT_PAYFAST_SANDBOX=false` + real credentials
- [ ] Configure SendGrid API key for emails
- [ ] Set up SSL/TLS (HTTPS)
- [ ] Configure production database with backups
- [ ] Set up monitoring (Sentry, Datadog, etc.)
- [ ] Configure CORS origins for production domain
- [ ] Review rate limits for production traffic

### Docker Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🏗️ Project Structure

```
SendIt/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + middleware
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── deps.py              # FastAPI dependencies (auth)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── integrations/        # External APIs
│   │   │   ├── couriers/        # Courier adapters
│   │   │   └── payments/        # PayFast client
│   │   └── utils/               # Helpers (security, logging)
│   ├── alembic/                 # Database migrations
│   ├── scripts/                 # Seed data, etc.
│   ├── tests/                   # Pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages (App Router)
│   │   └── lib/                 # API client, auth helpers
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🤝 Contributing

This is an MVP codebase designed for rapid iteration. Key principles:

- **Monolith first** — optimize for team velocity
- **Production-ready** — security, validation, error handling
- **Maintainable** — clear separation of concerns
- **Testable** — business logic isolated in services

---

## 📄 License

Proprietary — All rights reserved.

---

## 🆘 Support

For issues or questions:

1. Check API docs: http://localhost:8000/docs
2. Review logs: `docker-compose logs backend`
3. Inspect database: `docker-compose exec db psql -U sendit`

---

## 🔧 Troubleshooting

### Docker Issues

**"Cannot connect to Docker daemon"**

- Make sure Docker Desktop is running
- Try: `docker ps` to verify Docker is accessible

**"Port already in use"**

- Check if services are already running: `docker compose ps`
- Stop existing containers: `docker compose down`
- Or change ports in `docker-compose.yml`

**Frontend build fails with TypeScript errors**

- The frontend Dockerfile uses development mode (`npm run dev`)
- TypeScript strict mode is enabled - some IDE warnings are expected until dependencies are installed

**Backend bcrypt errors**

- The project uses `bcrypt==4.0.1` for compatibility
- If you see bcrypt version errors, rebuild containers: `docker compose up -d --build`

### Database Issues

**"Relation does not exist"**

- Run migrations: `docker compose exec backend alembic upgrade head`

**"Courier not found" errors**

- Seed the database: `docker compose exec backend python scripts/seed_data.py`

### General Tips

- View container logs: `docker compose logs -f [service-name]`
- Restart a specific service: `docker compose restart [service-name]`
- Rebuild from scratch: `docker compose down -v && docker compose up -d --build`

---

**Built with ❤️ for the South African logistics market**
