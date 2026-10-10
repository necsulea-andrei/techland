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
```