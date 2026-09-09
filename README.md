# 🛒 Supermarket POS

A Point-of-Sale system designed for supermarkets to streamline checkout operations, manage products and inventory, process payments, handle returns, track sales, and generate business reports.

The project is developed iteratively using the **Unified Process**, with an emphasis on object-oriented design, GRASP principles, GoF design patterns, persistence, testing, and maintainable software architecture.

## 📌 Project Status

**Iteration 3 — Complete ✅**

The current implementation includes:

* Product catalog management
* Cash sales processing
* Multiple payment methods
* Discounts and pricing strategies
* Offline payment support
* SQLite persistence
* Sale history
* Cash refunds and returns
* Sales reporting
* Inventory management
* User management
* User authentication
* Automated unit testing

The current test suite contains **219 passing tests**.

## ✨ Features

### 🧾 Point of Sale

* Create and process sales
* Add products to a sale
* Calculate line-item subtotals and sale totals
* Complete cash payments
* Calculate change due
* Prevent invalid sale operations

### 💳 Payment Processing

The system supports different payment mechanisms through an extensible payment architecture:

* Cash payments
* Card payments
* MTN Mobile Money
* Airtel Money
* Payment gateway adapters
* Payment gateway factory
* Offline payment handling

The payment architecture uses the **Adapter**, **Factory**, **Proxy**, and **Command** patterns.

### 💰 Pricing and Discounts

Sales pricing is handled through a strategy-based design that allows different pricing and discount rules to be introduced without modifying the core `Sale` class.

The project uses the **Strategy pattern** through `ISalePricingStrategy`.

### 📦 Product and Inventory Management

* Product catalog management
* Product descriptions
* Product lookup
* Stock-level management
* Inventory management
* Stock summary reporting
* Persistent product and inventory data

### 🔄 Returns and Refunds

The system supports:

* Starting a return
* Entering returned items
* Completing a return
* Cash refunds
* Persistent return history

### 📊 Reporting

The system provides reporting functionality including:

* Sales summaries
* Return summaries
* Top-selling products
* Stock summaries
* Persistent sales history
* Persistent return history

Reporting is implemented using a dedicated `SalesReportGenerator` to keep reporting responsibilities separate from core domain objects.

### 👤 User Management and Authentication

The system includes:

* User management
* User roles
* Password hashing
* User authentication
* Separate user-management responsibilities
* Authentication as a reusable service

Passwords are protected using **PBKDF2-HMAC-SHA256** using Python's standard library.

## 🏗️ Architecture and Design

The project follows object-oriented design principles and makes use of **GRASP** and **GoF design patterns**.

### GRASP Principles

Examples implemented in the project include:

* **Controller** — `Register`, `InventoryManager`, and `UserManager`
* **Creator** — `Sale` creates `SalesLineItem`
* **Information Expert** — `SalesLineItem` calculates its own subtotal
* **Pure Fabrication** — `SalesReportGenerator`
* **Polymorphism** — payment implementations
* **Protected Variations** — interfaces and abstractions around variable payment and pricing behavior

### Design Patterns

The project currently includes:

* **Strategy** — sale pricing and discounts
* **Adapter** — payment gateway integrations
* **Factory** — payment gateway selection
* **Proxy** — offline payment handling
* **Command** — offline synchronization queue
* **Facade** — persistence services
* **Data Mapper** — persistence of domain objects
* **Object Identifier** — persistent object identification

More detailed design decisions are documented in `docs/ARCHITECTURE.md`.

## 🗄️ Persistence

The application uses **SQLite** for persistent storage.

Persistent information includes:

* Product catalog data
* Completed sales
* Return history
* Inventory and stock levels

Persistence concerns are separated from the domain model using persistence facades and mapper classes.

## 🛠️ Technology Stack

| Technology                  | Purpose              |
| --------------------------- | -------------------- |
| **Python 3.10+**            | Programming language |
| **SQLite**                  | Persistent database  |
| **pytest**                  | Automated testing    |
| **Python Standard Library** | Runtime dependencies |

The project currently has no external runtime dependencies.

## 📂 Project Structure

src/supermarket_pos/

├── main.py                          # Entry point (launches desktop app)

│

├── domain/

│   ├── store.py                     # Root coordinator

│   ├── register.py                  # Cashier Controller (Process Sale + Returns)

│   ├── cashier.py

│   │

│   ├── common/

│   │   └── money.py

│   │

│   ├── product/

│   │   ├── product_description.py

│   │   ├── product_catalog.py

│   │   └── exceptions.py

│   │

│   ├── sales/

│   │   ├── sale.py

│   │   ├── sales_line_item.py

│   │   └── sale_observer.py         # Observer interface

│   │

│   ├── payment/

│   │   ├── payment.py

│   │   ├── cash_payment.py

│   │   ├── electronic_payment.py

│   │   ├── mobile_money_payment.py

│   │   ├── card_payment.py

│   │   ├── payment_declined_error.py

│   │   └── gateway/

│   │       ├── payment_gateway_adapter.py

│   │       ├── payment_gateway_factory.py

│   │       ├── mtn_momo_adapter.py

│   │       ├── airtel_money_adapter.py

│   │       ├── card_processor_adapter.py

│   │       ├── payment_service_proxy.py

│   │       ├── offline_sync_queue.py

│   │       └── ...

│   │

│   ├── returns/

│   │   ├── sale_return.py

│   │   ├── returned_line_item.py

│   │   └── cash_refund.py

│   │

│   ├── inventory/

│   │   ├── inventory.py

│   │   ├── inventory_manager.py

│   │   └── stock_level.py

│   │

│   ├── pricing/

│   │   ├── sale_pricing_strategy.py

│   │   ├── full_pricing_strategy.py

│   │   └── percentage_discount_pricing_strategy.py

│   │

│   └── users/

│       ├── user.py

│       ├── user_role.py

│       ├── user_manager.py

│       ├── authentication_service.py

│       ├── password_hasher.py

│       └── exceptions.py

│

├── persistence/                     # Technical Service

│   ├── persistence_facade.py

│   ├── product_description_mapper.py

│   ├── completed_sale_mapper.py

│   ├── completed_return_mapper.py

│   ├── stock_level_mapper.py

│   ├── user_mapper.py

│   └── ...

│

├── reporting/                       # Technical Service

│   ├── sales_report.py

│   ├── sales_report_generator.py

│   └── stock_report.py

│

└── ui/                              # New UI layer

├── __init__.py

└── desktop_app.py               # Full desktop application

## 🚀 Getting Started

### Prerequisites

Make sure you have:

* Python **3.10 or later**
* Git

### 1. Clone the Repository

```bash
git clone https://github.com/Phil-Samakayi/Supermarket-POS.git
cd Supermarket-POS
```

### 2. Create a Virtual Environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the Project

```bash
pip install -e ".[dev]"
```

### 4. Run the Application

```bash
python -m supermarket_pos.main
```

You can also run:

```bash
supermarket-pos
```

## 🧪 Running Tests

Run the complete test suite with:

```bash
pytest
```

The current implementation has **219 passing tests**.

## 📚 Documentation

Additional project documentation is available in the `docs/` directory.

### Architecture Documentation

`docs/ARCHITECTURE.md`

Contains important architectural and design decisions, including the problems considered, selected solutions, motivations, and alternatives.

### Iteration Plan

`docs/ITERATIONS.md`

Documents the development process and functionality delivered during each iteration.

### UML Documentation

`docs/Supermarket_POS_UseCase_UML.docx`

Contains the project's UML and design artifacts.

## 🔄 Development Approach

The project follows an **iterative Unified Process** approach.

Each iteration delivers a tested and integrated slice of functionality.

### Iteration 1 — Basics ✅

Implemented the core Process Sale use case and cash-only happy path.

### Iteration 2 — Design Patterns ✅

Introduced:

* Strategy-based pricing
* Payment gateway adapters
* Factory-based gateway selection
* Offline payment handling
* Command-based synchronization

### Iteration 3 — Intermediate Topics ✅

Implemented:

* Product persistence
* Sale history persistence
* Returns and cash refunds
* Sales reporting
* Inventory management
* User management
* Authentication

## 🎯 Future Enhancements

Potential future improvements include:

* Electronic refunds
* Linking returns to their original sales
* Automatic stock adjustment after sales
* Automatic stock adjustment after returns
* Making authentication a mandatory precondition for system operations
* Further development of the user interface
* Additional payment and business rules

## 👥 Team

**CSC4630 — Group 28**

## 📄 License

This project is maintained as an academic software engineering project.

---

## 🔗 Repository

[Supermarket-POS on GitHub](https://github.com/Phil-Samakayi/Supermarket-POS)
