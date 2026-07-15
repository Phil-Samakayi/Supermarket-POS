# Iteration Plan

Following the Unified Process (Larman, *Applying UML and Patterns*), each
iteration is timeboxed and delivers a tested, integrated, working slice of
the system — not a throwaway prototype. Full design artifacts (fully-dressed
use case, domain model, SSDs, design class diagram, layered architecture)
are in [`Supermarket_POS_UseCase_UML.docx`](Supermarket_POS_UseCase_UML.docx).

## Iteration 1 — Basics ✅ (current)

**Goal:** Prove the core domain model and the cash-only happy path of
Process Sale (UC1), end to end.

**Delivered:**
- Domain layer: `Store`, `Register`, `Cashier`, `ProductCatalog`,
  `ProductDescription`, `Sale`, `SalesLineItem`, `Payment` / `CashPayment`,
  and a `Money` value type (`Decimal`-backed, to avoid float rounding
  errors in currency arithmetic).
- `Register` acts as the GRASP Controller for the system operations implied
  by UC1's SSDs: `make_new_sale`, `enter_item`, `end_sale`,
  `make_cash_payment`.
- GRASP applied throughout: Creator (`Sale` creates `SalesLineItem`),
  Information Expert (`SalesLineItem` computes its own subtotal;
  `ProductCatalog` is the expert on product lookups), Controller (`Register`).
- Deliberately **out of scope** this iteration (see Larman: "don't
  implement all requirements at once"): mobile money / card payment,
  discounts and tax, offline sync, returns, reporting, and any UI beyond
  a console demo.
- Unit tests (pytest) covering the main success scenario and key
  extensions/error paths: 3a (item not found), the "can't pay before
  `end_sale`" and "can't add items after `end_sale`" invariants, and
  change-due calculation.
- `python -m supermarket_pos.main` exercises Start Up + Process Sale
  end to end as a console demo.

## Iteration 2 — More Patterns (planned)

- `ISalePricingStrategy` (**Strategy**) for discounts, replacing the plain
  summation in `Sale.get_total()`.
- `IPaymentGatewayAdapter` + `MTNMoMoAdapter` / `AirtelMoneyAdapter` /
  `CardProcessorAdapter` (**Adapter**), selected via `PaymentGatewayFactory`
  (**Factory**) — realizes UC1 extensions 9b/9c.
- `PaymentServiceProxy` + `OfflineSyncQueue` (**Proxy** + **Command**) for
  the offline-first requirement (UC1 extension *a) — this is the project's
  top-ranked risk (unreliable power/internet) and the reason Proxy was
  chosen over a simpler retry loop.
- `ISaleObserver` / `CheckoutScreen` (**Observer**) once a real UI is
  introduced, preserving Model-View Separation.

## Iteration 3 — Intermediate Topics (planned)

- Persistence (database-backed `ProductCatalog` and sale history, replacing
  the in-memory dict).
- Handle Returns use case.
- Reporting for Manager/Owner (sales and stock summaries).
- Manage Inventory / Manage Users use cases.
