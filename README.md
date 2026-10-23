# E-Commerce Project: TechLand (PC Hardware & Industrial Automation Store)

Academic Year 2026-2027 — Semester Project

## 1. Team & Roles
- **Necșulea Andrei-Mihai**: Backend & Database Lead
- **Onofrei Alexandru-Gabriel**: Frontend & UI/UX Lead

---

## 2. Project Overview
A hybrid online store offering high-performance PC hardware (CPUs, DDR5 RAM, PCIe Gen5 NVMe SSDs) and certified industrial automation equipment (Siemens & Schneider PLCs, expansion I/O units, DIN-rail power supplies).

- **Target Customers**: Individual PC power users / engineering students (B2C) and plant maintenance engineers / industrial manufacturing contractors (B2B).
- **Tech Stack**: Django 5.x (Python 3.12), PostgreSQL 16 (Dockerized), Django Templates & Tailwind CSS, Stripe API (Sandbox / Test Mode).

---

## 3. Mandatory Requirements Ownership (A1–A12)
| Code | Requirement | Owner | Status |
| :--- | :--- | :--- | :--- |
| **A1** | Product catalog (server pagination, category & product detail views) | Andrei / Alexandru | Completed (P2/P3) |
| **A2** | Basic search (case-insensitive search by product name & SKU) | Andrei / Alexandru | Completed (P2) |
| **A3** | Shopping cart (server recalculation, quantity limits, persistent per user) | Andrei / Alexandru | Completed (P3) |
| **A4** | User accounts (secure hashing, profile & delivery addresses) | Andrei / Alexandru | Completed (P2/P3) |
| **A5** | Checkout (saved address selection, delivery method, order review) | Alexandru / Andrei | Completed (P3) |
| **A6** | Sandbox payment (Stripe Hosted Checkout & async signature webhook) | Andrei | Completed (P3) |
| **A7** | Stock management (atomic stock decrement, race-condition mitigation) | Andrei | Completed (P3) |
| **A8** | Order history (chronological order log, items, amounts, live status badges) | Alexandru | Completed (P3) |
| **A9** | Custom Administration Panel (branded dashboard, CRUD, order state machine) | Alexandru | Completed (P3) |
| **A10** | Basic security (server-side validation, CSRF tokens, ORM sanitization) | Andrei | Completed (P3) |
| **A11** | Responsive design (mobile-first layout, fully usable down to 360 px width) | Alexandru | Completed (P2/P3) |
| **A12** | Automated tests (12 unit & integration test suite, single command) | Andrei | Completed (P3) |

---

## 4. Local Setup & Running Instructions
The entire application starts locally in 5 streamlined commands:

```bash
# 1. Clone repository and navigate inside
git clone https://github.com/necsulea-andrei/techland.git && cd techland

# 2. Copy environment template and start containerized PostgreSQL database
cp .env.example .env && docker compose up -d

# 3. Create and activate virtual environment
python3 -m venv venv && source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Apply migrations, seed database with 32 catalog products and start server
python manage.py migrate && python manage.py seed_data && python manage.py runserver
```

### Auxiliary Operational Commands (Development & Testing)

```bash
# Run the complete automated test suite (A12)
python manage.py test orders

# Create administrative user for Django admin / portal panel (A9)
python manage.py createsuperuser

# Docker management
docker compose ps               # List active service containers
docker compose logs -f db       # Follow live PostgreSQL engine logs
docker compose down             # Stop database container
docker compose down -v          # Stop container and wipe persistent volume

# Stripe Webhook Listener (Localhost Development Forwarder)
stripe listen --events checkout.session.completed --forward-to localhost:8000/api/stripe/webhook/
```

---

## 5. Prototype Implementation Status (P2 Milestone)

All foundational deliverables and working prototype requirements for **Presentation 2 (P2)** have been completed across three logical phases:

### Phase 1: Infrastructure, Data Modeling & Database Seeding (Done)
- [x] **Containerized Relational Database**: Configured PostgreSQL 16 via Docker Compose (`docker-compose.yml`) connected to Django through environment variables (`.env`).
- [x] **Catalog Data Model**: Implemented `Category` and `Product` models featuring slugified routing, unique SKUs, stock levels, decimal pricing, and media attachments.
- [x] **User Accounts & Address Architecture (A4)**: Configured custom `Address` model with foreign key relationships, delivery metadata, and automatic single-default (`is_default`) enforcement.
- [x] **Database Seed Script**: Built custom management command (`python manage.py seed_data`) populating 32 realistic products across 4 dedicated industrial/consumer categories with full attribute specifications.
- [x] **Admin Inspection Panels**: Enabled Django admin views for real-time validation and management of categories, inventory, and saved addresses.

### Phase 2: Design System, Layout & User Authentication (Done)
- [x] **Responsive Master Layout (A11)**: Built mobile-first `base.html` template utilizing Tailwind CSS, tested and fully functional down to 360 px width.
- [x] **Global Navigation & UI Elements**: Implemented responsive navbar with category dropdowns, sticky search bar, dynamic authentication states, and footer.
- [x] **Authentication Flow (A4)**: Integrated complete user registration, secure login/logout views, password hashing (PBKDF2/bcrypt-compatible), and session management.

### Phase 3: Catalog Browsing & Search Prototype (Done)
- [x] **Paginated Product Catalog (A1)**: Implemented server-side paginated product listing (12 items per page) with category-specific filtering.
- [x] **Product Detail View (A1)**: Dedicated product view displaying full technical descriptions, dynamic stock badges, price tags, and high-resolution visuals.
- [x] **Text Search Engine (A2)**: Built case-insensitive server-side search querying product names and SKUs with dedicated empty-state feedback.

---

## 6. Final End-to-End Implementation (P3 Milestone)

The final architecture for **Presentation 3 (P3)** integrates complete full-stack capabilities, closing all requirements across Backend and Frontend ownership:

### Part A: Backend, Transactions & Testing (Lead: Andrei Necșulea)
- [x] **10-Table Normalized Relational Schema**: Built and migrated full schema across `accounts`, `catalog`, and `orders` applications (`User`, `Address`, `UserAddress`, `Category`, `Product`, `ProductImage`, `Review`, `Cart`, `CartItem`, `Order`, `OrderItem`).
- [x] **Server-Side Shopping Cart Engine (A3)**:
  - User-bound persistent cart retaining items across login/logout sessions.
  - Strict server-side recalculation of line totals and cart subtotal.
  - Server-side inventory boundary validation rejecting cart increments beyond physical stock.
- [x] **Stripe Sandbox Payment Integration (A6)**:
  - Endpoint creating Stripe Hosted Checkout Sessions populated with line items, dynamic callbacks, and `client_reference_id`.
  - Asynchronous webhook handler (`/api/stripe/webhook/`) verifying cryptographic signatures (`HTTP_STRIPE_SIGNATURE`).
- [x] **Concurrency & Atomic Stock Management (A7)**:
  - Stock decrement wrapped inside `transaction.atomic()` using `select_for_update()` row-level locks.
  - Atomic arithmetic decrements (`F('stock') - quantity`) preventing race conditions during simultaneous checkouts.
  - Webhook idempotency handling preventing duplicate inventory deductions on retried Stripe events.
- [x] **Security Hardening (A10)**:
  - CSRF verification on all state-mutating POST forms.
  - Django ORM parameterized queries safeguarding against SQL injection.
  - Strict `is_staff` permission decorators guarding administrative routes.
- [x] **Automated Test Suite (A12)**:
  - 12 comprehensive unit and integration tests executing under `python manage.py test orders`.
  - Automated coverage for cart persistence, price math, stock boundaries, webhook signatures, idempotency, and access controls.

### Part B: Frontend, UI/UX & Administrative Dashboard (Lead: Alexandru Onofrei)
- [x] **Tailwind CSS Mobile-First Design System (A11)**:
  - Comprehensive responsive styling verified down to 360 px viewport width (iPhone SE / compact mobile standards).
  - Fluid mobile navigation drawer, responsive sticky search bar, and zero horizontal viewport overflows.
- [x] **Dedicated Landing Page / Home View**:
  - Hero presentation highlighting the dual B2C (PC Enthusiasts) & B2B (Industrial Automation) product segmentation.
  - Direct visual category gateway grid and dynamically queried featured hardware cards.
- [x] **Interactive Shopping Cart Interface (A3)**:
  - Clean layout showing item thumbnails, unit prices, subtotal calculations, and responsive quantity updates.
  - Asynchronous AJAX quantity adjustment with instant subtotal and server error toast messages.
- [x] **Checkout & Order Review Interface (A5)**:
  - Multi-step order confirmation UI with saved delivery address selection and standard ground shipping calculation.
  - Dynamic order review summary with direct redirect trigger to Stripe Hosted Checkout.
  - Custom branded callback views for transaction success (`orders/success.html`) and cancellation (`orders/cancel.html`).
- [x] **Customer Order History Portal (A8)**:
  - Dedicated `/orders/history/` dashboard displaying chronological order logs.
  - Color-coded status badges reflecting lifecycle states (`New`, `Paid`, `Shipped`, `Delivered`, `Cancelled`).
  - Itemized purchase breakdown with frozen purchase prices and purchase timestamps.
- [x] **Custom Administration Portal (A9)**:
  - Branded control portal header and dashboard (`TechLand Control Portal`) mapped for management operations.
  - Advanced search filters by title, SKU, order status, and category.
  - Order management interface supporting administrative status transitions (`Paid` $\rightarrow$ `Shipped` $\rightarrow$ `Delivered`) and inline item inspection. 