# E-Commerce Project: PC Hardware & Industrial Automation Store

Academic Year 2026-2027 — Semester Project

## 1. Team & Roles
* **Necșulea Andrei-Mihai**: Backend & Database Lead
* **Onofrei Alexandru-Gabriel**: Frontend & UI/UX Lead

---

## 2. Project Overview
A hybrid online store offering PC hardware (CPUs, RAM, SSDs) and industrial automation modules (PLCs, I/O modules, power supplies).

* **Target Customers**: Individual PC enthusiasts / students (B2C) and maintenance engineers / manufacturing businesses (B2B).
* **Tech Stack**: Django (Python), PostgreSQL, Django Templates & Tailwind CSS, Stripe (Test Mode).

---

## 3. Mandatory Requirements Ownership (A1–A12)
| Code | Requirement | Owner | Status |
| :--- | :--- | :--- | :--- |
| **A1** | Product catalog (pagination, category/product views) | Andrei / Alexandru | Planned (P2) |
| **A2** | Basic search (text search by name) | Andrei / Alexandru | Planned (P2) |
| **A3** | Shopping cart (server recalculation, persistence) | Andrei / Alexandru | Planned (P3) |
| **A4** | User accounts (bcrypt/Argon2, delivery addresses) | Andrei | Planned (P2) |
| **A5** | Checkout (addresses, ≥2 delivery options, summary) | Alexandru | Planned (P3) |
| **A6** | Sandbox payment (asynchronous Stripe webhook) | Andrei | Planned (P3) |
| **A7** | Stock management (atomic decrement, anti-race condition) | Andrei | Planned (P3) |
| **A8** | Order history (date, items, total, status) | Alexandru | Planned (P3) |
| **A9** | Custom Administration Panel (CRUD, order status) | Alexandru | Planned (P3) |
| **A10** | Basic security (server-side validation, CSRF, ORM) | Andrei | Planned (P3) |
| **A11** | Responsive design (usable down to 360 px width) | Alexandru | Planned (P2/P3) |
| **A12** | Automated tests (≥10 tests, single command) | Andrei | Planned (P3) |

---

## 4. Local Setup & Running Instructions
The application starts locally in fewer than 5 commands:

```bash
# 1. Clone repository and navigate inside
git clone https://github.com/necsulea-andrei/techland.git && cd techland

# 2. Copy environment template
cp .env.example .env

# 3. Create and activate virtual environment
python3 -m venv venv && source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Apply migrations and start server
python manage.py migrate && python manage.py runserver

#6.run docker commands

docker compose up -d #start container
docker compose ps #list containers
docker compose down #stop containers
docker compose down -v #stop containers and remove volumes
docker compose logs -f db #follow logs

#7.create super user
python manage.py createsuperuser

#8.run tests
python manage.py test
```

---

## 5. Current Implementation Status (P2 Milestone)

All core deliverables and working prototype requirements for **Presentation 2 (P2)** have been completed across three logical phases:

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
- [x] **Paginated Product Catalog (A1)**: Implemented server-side paginated product listing (at most 24 items per page) with category-specific filtering.
- [x] **Product Detail View (A1)**: Dedicated product view displaying full technical descriptions, dynamic stock badges, price tags, and high-resolution visuals.
- [x] **Text Search Engine (A2)**: Built case-insensitive server-side search querying product names with dedicated empty-state feedback.

---