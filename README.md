## Supermarket-POS

A Point-of-Sale system for a supermarket that streamlines checkout
operations, manages inventory, tracks sales, and provides analytical
insights for business growth.

Built iteratively following the Unified Process, as described in Craig
Larman's *Applying UML and Patterns*. Full design artifacts (fully-dressed
use case, domain model, System Sequence Diagrams, design class diagram,
layered architecture) are in
[`docs/Supermarket_POS_UseCase_UML.docx`](docs/Supermarket_POS_UseCase_UML.docx);
the iteration plan is in [`docs/ITERATIONS.md`](docs/ITERATIONS.md).

![Supermarket POS Screenshot](https://github.com/Phil-Samakayi/Supermarket-POS/blob/main/ChatGPT%20Image%20Mar%202%2C%202026%2C%2003_57_58%20AM.png?raw=true)

### Status

**Iterations 1–3 are complete** (219/219 tests passing). See
[`docs/ITERATIONS.md`](docs/ITERATIONS.md) for the full breakdown and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a running record of
*why* each design decision was made (Larman's technical-memo format:
Issue → Solution → Motivation → Alternatives Considered), added
iteration by iteration rather than written up after the fact.

- **Iteration 1 — Basics:** cash-only Process Sale, end to end.
- **Iteration 2 — Patterns:** discount pricing (Strategy); mobile
  money/card payment (Adapter + Factory); offline resilience for
  mobile money payments when a gateway is unreachable (Proxy +
  Command).
- **Iteration 3 — Intermediate topics:** SQLite persistence for the
  product catalog and sale/return history (Facade + Database Mapper);
  Handle Returns (cash refunds); Reporting (sales summaries,
  top-selling items, stock levels); Manage Inventory; Manage Users +
  Authenticate User.

A few integrations are deliberately deferred rather than built in a
rush — named explicitly in `ARCHITECTURE.md`, not silently skipped:
electronic refunds, returns linked to their original sale, automatic
stock adjustment on sale/return, authentication as a precondition of
other operations, and the Observer pattern (waiting on a real UI to
subscribe to).

### Tech Stack

- Python 3.10+
- [pytest](https://docs.pytest.org/) for testing
- SQLite (standard library `sqlite3`) for persistence
- Standard library only at runtime — no external dependencies

### Project Structure

```
src/supermarket_pos/
├── main.py                        # Console demo (Start Up + Process Sale)
├── domain/
│   ├── store.py                   # Root object; coordinates Register,
│   │                               #   InventoryManager, UserManager, persistence
│   ├── register.py                # GRASP Controller: Process Sale + Handle Returns (Cashier)
│   ├── cashier.py
│   ├── common/
│   │   └── money.py                # Decimal-backed Money value type
│   ├── product/
│   │   ├── product_description.py
│   │   ├── product_catalog.py     # Information Expert for product lookups
│   │   └── exceptions.py
│   ├── pricing/                   # Strategy: ISalePricingStrategy
│   │   ├── sale_pricing_strategy.py
│   │   ├── full_pricing_strategy.py
│   │   └── percentage_discount_pricing_strategy.py
│   ├── sales/
│   │   ├── sale.py
│   │   └── sales_line_item.py
│   ├── payment/
│   │   ├── payment.py              # Abstract superclass (Polymorphism)
│   │   ├── cash_payment.py
│   │   ├── electronic_payment.py   # Do-It-Myself: authorizes itself via its adapter
│   │   ├── mobile_money_payment.py
│   │   ├── card_payment.py
│   │   └── gateway/                # Adapter + Factory + Proxy + Command
│   │       ├── payment_gateway_adapter.py     # IPaymentGatewayAdapter interface
│   │       ├── mtn_momo_adapter.py
│   │       ├── airtel_money_adapter.py
│   │       ├── card_processor_adapter.py
│   │       ├── payment_gateway_factory.py     # Factory + Singleton
│   │       ├── payment_service_proxy.py       # Proxy: offline failover
│   │       ├── offline_payment_command.py     # Command
│   │       └── offline_sync_queue.py
│   ├── returns/                   # Handle Returns (cash-refund only)
│   │   ├── sale_return.py
│   │   ├── returned_line_item.py
│   │   └── cash_refund.py
│   ├── inventory/                 # Manage Inventory — separate Controller (Manager/Owner)
│   │   ├── inventory_manager.py
│   │   ├── inventory.py
│   │   └── stock_level.py
│   └── users/                     # Manage Users + Authenticate User —
│       │                          #   separate Controller (System Administrator)
│       ├── user_manager.py
│       ├── authentication_service.py
│       ├── user.py
│       ├── user_role.py
│       └── password_hasher.py
├── persistence/                   # Technical Service partition (Larman Ch.13.6)
│   ├── persistence_facade.py      # Facade over per-class Database Mappers
│   ├── product_description_mapper.py
│   ├── stock_level_mapper.py
│   ├── user_mapper.py
│   ├── completed_sale_mapper.py   # Read-only snapshot, not a live Sale reconstruction
│   ├── completed_return_mapper.py
│   └── sqlite_*.py                # Wiring helpers
└── reporting/                     # Technical Service partition (Larman Ch.13.6)
    ├── sales_report_generator.py  # Pure Fabrication
    └── stock_report.py

tests/   # mirrors src/ 1:1 — one test module per production module
```

### Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run

```bash
python -m supermarket_pos.main
# or, once installed:
supermarket-pos
```

### Test

```bash
pytest
```

### Team

CSC4630 — Group 28
