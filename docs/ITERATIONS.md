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

## Iteration 2 — More Patterns (in progress)

Design rationale for each pattern decision below is recorded as a technical
memo in [`ARCHITECTURE.md`](ARCHITECTURE.md) (Larman Ch.39's format:
Issue → Solution Summary → Factors → Solution → Motivation → Alternatives
Considered), added iteration by iteration rather than written up
retroactively.

- ✅ `ISalePricingStrategy` (**Strategy**) for discounts, replacing the
  plain summation in `Sale.get_total()`. See
  [ARCHITECTURE.md § Pricing](ARCHITECTURE.md#pricing-discounts).
- ✅ `IPaymentGatewayAdapter` + `MTNMoMoAdapter` / `AirtelMoneyAdapter` /
  `CardProcessorAdapter` (**Adapter**), selected via `PaymentGatewayFactory`
  (**Factory**) — realizes UC1 extensions 9b/9c. See
  [ARCHITECTURE.md § Payment gateway integration](ARCHITECTURE.md#payment-gateway-integration).
- ✅ `PaymentServiceProxy` + `OfflineSyncQueue` (**Proxy** + **Command**) for
  the offline-first requirement (UC1 extension *a) — this is the project's
  top-ranked risk (unreliable power/internet) and the reason Proxy was
  chosen over a simpler retry loop. Applied to mobile money only; card
  payments have no offline equivalent and still fail fast on an
  unreachable gateway. See
  [ARCHITECTURE.md § Offline payment failover](ARCHITECTURE.md#offline-payment-failover).
- ⏳ `ISaleObserver` / `CheckoutScreen` (**Observer**) — deliberately
  deferred until a real UI exists to subscribe. Introducing an Observer
  before a genuine subscriber exists would be speculative future-proofing
  (Larman's Protected Variations discussion warns against exactly this —
  "pick your battles" rather than engineering flexibility nothing yet
  needs).

**Current test count:** 78/78 passing on a fresh install (as of the
Proxy/Command slice).

## Iteration 3 — Intermediate Topics (planned)

- Persistence (database-backed `ProductCatalog` and sale history, replacing
  the in-memory dict).
- Handle Returns use case.
- Reporting for Manager/Owner (sales and stock summaries).
- Manage Inventory / Manage Users use cases.
