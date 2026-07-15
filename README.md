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

**Iteration 1 (Basics)** — cash-only Process Sale happy path implemented
and tested. See [`docs/ITERATIONS.md`](docs/ITERATIONS.md) for what's
in scope now vs. planned for later iterations.

### Tech Stack

- Python 3.10+
- [pytest](https://docs.pytest.org/) for testing
- Standard library only at runtime (no external dependencies yet)

### Project Structure

```
src/supermarket_pos/
├── main.py                        # Iteration-1 console demo (Start Up + Process Sale)
└── domain/
    ├── store.py                   # Creator of Register / ProductCatalog
    ├── register.py                # GRASP Controller for Process Sale
    ├── cashier.py
    ├── common/
    │   └── money.py                # Decimal-backed Money value type
    ├── product/
    │   ├── product_description.py
    │   ├── product_catalog.py     # Information Expert for product lookups
    │   └── exceptions.py
    ├── sales/
    │   ├── sale.py
    │   └── sales_line_item.py
    └── payment/
        ├── payment.py              # Abstract superclass (Polymorphism)
        └── cash_payment.py

tests/domain/
├── common/test_money.py
├── payment/test_cash_payment.py
├── sales/test_sale.py
└── test_register.py
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
