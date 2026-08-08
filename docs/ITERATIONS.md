# Iteration Plan

Following the Unified Process (Larman, *Applying UML and Patterns*), each
iteration is timeboxed and delivers a tested, integrated, working slice of
the system — not a throwaway prototype. Full design artifacts (fully-dressed
use case, domain model, SSDs, design class diagram, layered architecture)
are in [`Supermarket_POS_UseCase_UML.docx`](Supermarket_POS_UseCase_UML.docx).

## Iteration 1 — Basics ✅

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

## Iteration 2 — More Patterns ✅ (Observer deferred)

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
- ⏳ **Deliberately deferred, not dropped:** `ISaleObserver` /
  `CheckoutScreen` (**Observer**). Decision made explicitly at the end of
  Iteration 2 (not just left hanging): introducing an Observer before a
  genuine subscriber exists would be speculative future-proofing
  (Larman's Protected Variations discussion warns against exactly this —
  "pick your battles" rather than engineering flexibility nothing yet
  needs). Revisit when a real UI/view layer becomes a requirement —
  likely alongside or after Iteration 3's reporting work, which is the
  next point a second "consumer" of Sale's state naturally appears.

**Final test count:** 78/78 passing on a fresh install.

## Iteration 3 — Intermediate Topics (in progress)

- ✅ Persistence: `ProductCatalog` is now backed by SQLite for the
  first entity (`ProductDescription`), via `PersistenceFacade` +
  `ProductDescriptionMapper` (Larman Ch.38 — Facade, Database Mapper,
  Object Identifier). `ProductDescription`/`ProductCatalog` remain
  completely persistence-ignorant; `Store` coordinates loading at
  Start Up and saving via the new `Store.add_product()`. See
  [ARCHITECTURE.md § Persistent product catalog](ARCHITECTURE.md#persistent-product-catalog).
- ✅ Sale history persistence: completed sales now survive a restart
  via `CompletedSaleMapper`, following Ch.38.19's one-to-many table
  design for line items. Deliberately persists a read-only
  `CompletedSaleRecord` snapshot rather than reconstructing the live
  `Sale`/`Payment` object graph — `Payment` subclasses hold a live
  gateway-adapter collaborator with no persisted equivalent, and
  Larman's book doesn't cover inheritance-to-table mapping at all. New
  `Store.sale_history()` is the durable, cross-session view; the
  existing `Store.completed_sales` is untouched (still this session's
  live `Sale` objects only). See
  [ARCHITECTURE.md § Sale history persistence](ARCHITECTURE.md#sale-history-persistence).
- Handle Returns use case.
- Reporting for Manager/Owner (sales and stock summaries) — will read
  from `Store.sale_history()`, not yet built.
- Manage Inventory / Manage Users use cases.

**Current test count:** 108/108 passing on a fresh install (as of the
sale-history persistence slice).
