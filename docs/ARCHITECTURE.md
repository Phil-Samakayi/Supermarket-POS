# Architecture Decisions

This is a running Software Architecture Document (SAD), in the sense
Larman describes in *Applying UML and Patterns* Ch.39: a small set of
"architectural views" plus one **technical memo** per significant design
decision, added iteration by iteration as decisions are actually made —
not written up retroactively at the end of the project.

Each memo follows Larman's own template (Ch.39, Section 39.1):

> Issue → Solution Summary → Factors → Solution → Motivation →
> Unresolved Issues → Alternatives Considered

The point of a memo isn't the code (that's in `src/` and covered by
tests) — it's the *why*: what problem this solved, what else was
considered, and what trade-off was accepted. That's the part that stops
existing once a pull request is merged, unless it's written down.

For the full domain model, use-case text, SSDs, and design class
diagrams, see
[`Supermarket_POS_UseCase_UML.docx`](Supermarket_POS_UseCase_UML.docx).
For iteration-level scope and status, see
[`ITERATIONS.md`](ITERATIONS.md).

---

## Iteration 1

No architecturally significant decisions were made in Iteration 1 —
it's a straightforward layered domain model with no external
integrations or variation points yet (see Larman Ch.33: architectural
analysis is about identifying and resolving *non-functional*
requirements; Iteration 1 has none of consequence). The first real
architectural decisions arrive in Iteration 2, once external payment
providers are in scope.

---

## Iteration 2

### Pricing (discounts)

**Issue:** `Sale.get_total()` was a plain summation of line items. The
requirements now call for a storewide or customer-specific discount
policy that changes over time (e.g. a promotional period), without
hard-coding a percentage into `Sale`.

**Solution Summary:** GoF Strategy — `ISalePricingStrategy`, with
`FullPricingStrategy` (no discount, the default) and
`PercentageDiscountPricingStrategy` as concrete implementations.

**Factors:**
- Pricing policy needs to vary independently of `Sale` itself.
- Existing callers and all Iteration-1 tests must be unaffected by
  default.

**Solution:** `Sale` holds a reference to an `ISalePricingStrategy`,
defaulting to `FullPricingStrategy`. `get_total()` delegates to
`self._pricing_strategy.get_total(self)` — the context object passes
itself into the strategy so the strategy can ask for whatever it needs
(currently just `Sale.get_subtotal()`), per Larman's Strategy/context
collaboration guidance (Ch.26.7). A new `get_subtotal()` method was
added to `Sale` as the pre-discount sum, keeping `Sale` the
Information Expert for that figure while the strategy owns the
discount math.

**Motivation:** Discount policy is exactly the kind of thing Larman
flags as a Strategy candidate — "related algorithms that vary" — and
keeping it out of `Sale` avoids `Sale` accumulating conditional logic
per policy type as more discount rules are added later.

**Unresolved Issues:** No policy for *combining* multiple simultaneous
discounts (e.g. senior + promotional) yet — Larman's own worked
example for this (Ch.26.8, Composite over Strategy) is a candidate if
that requirement appears.

**Alternatives Considered:** A discount percentage field directly on
`Sale` — rejected because it can't express "no discount" vs. "0%
discount" cleanly, and would need conditional logic to grow into
multiple policy types.

---

### Payment gateway integration

**Issue:** UC1 extensions 9b/9c require accepting mobile money (MTN,
Airtel) and card payments, each via a different external provider API.

**Solution Summary:** GoF Adapter (`IPaymentGatewayAdapter` +
`MTNMoMoAdapter` / `AirtelMoneyAdapter` / `CardProcessorAdapter`),
selected via a GoF Factory (`PaymentGatewayFactory`, Singleton-accessed).

**Factors:**
- Three providers, three different response shapes (MTN:
  `status`/`financialTransactionId`; Airtel: numeric `resultCode`;
  card: `approved`/`declineReason`).
- `Register` (the Controller) must not be coupled to any concrete
  provider class or client library.
- A legitimate business decline (insufficient funds) must be
  distinguishable from a technical failure to reach the provider at
  all — these need different handling (see Offline payment failover,
  below).

**Solution:** Each adapter implements `IPaymentGatewayAdapter.authorize
(amount, payer_reference) -> AuthorizationResult` and is solely
responsible for translating its provider's raw response into that
neutral shape. `PaymentGatewayFactory` owns adapter construction and
provider-name resolution (`get_mobile_money_adapter("mtn")`), so
`Register` only ever asks the factory for "the mtn adapter," never
constructs one. `PaymentDeclinedError` (business decline) and
`GatewayUnavailableError` (technical failure) are kept as distinct
exception types from the start — see Larman Ch.35 ("Handling
Failure") on why conflating these is a design smell.

Payment authorization itself is polymorphic: `ElectronicPayment`
(superclass of `MobileMoneyPayment` / `CardPayment`) authorizes itself
via its injected adapter, following Larman's "Do It Myself" pattern
(Ch.35.8) rather than `Register` branching on payment type.

**Motivation:** This is the direct analogue of Larman's own NextGen
POS case study problem — multiple external services with varying
interfaces (Ch.26.1, "Adapter (GoF)"; Ch.26.4, "Factory"). Following
the book's solution here means a fourth provider (e.g. Zamtel Kwacha)
is addable by editing only `payment_gateway_factory.py`.

**Unresolved Issues:** No retry/backoff policy for a provider that is
merely slow rather than fully unreachable — currently a slow response
either eventually returns normally or the underlying client raises
(treated as unavailable). Not needed yet since the simulated clients
are synchronous and instantaneous.

**Alternatives Considered:** A single `PaymentGateway` class with an
`if provider == "mtn": ...` branch — rejected immediately as the
textbook case Polymorphism/Adapter exists to avoid; adding a provider
would mean editing a growing conditional instead of adding a class.

---

### Offline payment failover

**Issue:** Unreliable power/internet is this project's top-ranked
risk (see the risk list in
[`Supermarket_POS_UseCase_UML.docx`](Supermarket_POS_UseCase_UML.docx)).
A mobile money gateway being briefly unreachable should not force the
sale to fail outright — "retailers really don't want to stop making
sales" (Larman, Ch.35.2, motivating the same problem for NextGen POS).

**Solution Summary:** GoF Proxy (`PaymentServiceProxy`, the
Redirection/Failover Proxy variant from Larman Ch.35.4) + GoF Command
(`OfflinePaymentCommand`, queued in an `OfflineSyncQueue`).

**Factors:**
- The failure must be distinguished from a legitimate decline (see
  Payment gateway integration, above) — a declined payment must still
  stop the sale; an unreachable gateway must not.
- `Register` and `Payment` should not need to change to gain this
  behavior — it should be transparent, which is the entire point of
  Proxy.
- Card payments have no real-world equivalent of "trust now, verify
  later" — accepting a card payment requires real-time authorization,
  full stop. This trade-off must NOT apply uniformly to every payment
  type.

**Solution:** `PaymentServiceProxy` implements
`IPaymentGatewayAdapter`, wrapping a real adapter. On
`GatewayUnavailableError` it captures an `OfflinePaymentCommand`
(the request, ready to be re-executed later) into a shared
`OfflineSyncQueue`, and returns a *provisional* `AuthorizationResult`
(`approved=True, pending=True`) so the sale completes now.
`PaymentGatewayFactory` wraps only the MTN and Airtel adapters in this
Proxy; `CardProcessorAdapter` is deliberately left unwrapped, so a
card `GatewayUnavailableError` still propagates and fails the payment.
`OfflineSyncQueue.replay_all()` re-executes every queued command and
reports three distinct outcomes: `confirmed`, `failed` (declined *on
replay* — the money genuinely never moved, flagged for manual
follow-up rather than silently dropped), and `still_pending`.
`Store.sync_offline_payments()` is the manager-triggered "try to
reconnect now" action that calls this.

**Motivation:** This is Larman's own worked solution to the identical
problem (Ch.35.4), applied to a market-specific reality: Zambian
mobile money agent transactions are commonly trusted verbally/by SMS
at the point of sale and confirmed once connectivity returns, which is
not true of card payments. Keeping `Register` untouched by this change
(it only gained an `offline_queue` property) is a direct demonstration
of Larman's Protected Variations principle — the failover behavior is
entirely contained behind the `IPaymentGatewayAdapter` interface.

**Unresolved Issues:**
- Nothing triggers `sync_offline_payments()` automatically yet — it's
  a manually-callable capability with no scheduling/session layer
  behind it. Revisit once Iteration 3 introduces a reporting/session
  layer.
- A `still_pending` sale currently shows as a completed, paid sale in
  `Store.completed_sales` with no visible flag distinguishing it from
  a fully confirmed one at the `Store` level (the flag exists on
  `Payment.authorization_result.pending`, but nothing surfaces it yet
  in a report). Deferred to Iteration 3's reporting scope.

**Alternatives Considered:**
- *A simple retry loop inside the adapter* (retry N times, then fail)
  — rejected: doesn't address the actual problem (an outage that
  outlasts a few retries), and still fails the sale.
- *Applying the same offline-queue treatment to card payments* — 
  rejected on domain grounds (see Factors above), not a technical
  limitation.

---

## Iteration 3

### Persistent product catalog

**Issue:** `ProductCatalog` was an in-memory dict, seeded manually at
every Start Up. Products need to survive a restart.

**Solution Summary:** Larman's own persistence design (Ch.38) applied
to one entity first: `PersistenceFacade` (Ch.38.9, Facade) delegating
to a `ProductDescriptionMapper` (Ch.38.10, Database Mapper), keyed by
an `OID` (Ch.38.8, Object Identifier), backed by SQLite.

**Factors:**
- `ProductDescription` and `ProductCatalog` (domain layer) must not
  become coupled to SQL or any particular storage technology.
- Existing tests and call sites — `store.catalog.add_product(...)`
  used directly with no persistence involved — must keep working
  unchanged.
- Iteration 3 will eventually need to persist `Sale` too, which has
  real object relationships (line items, payment); the design for one
  entity now shouldn't make that harder later.

**Solution:** All SQL for `ProductDescription` lives in exactly one
class, `ProductDescriptionMapper` (Ch.38.15, "Consolidating and Hiding
SQL Statements in One Class"). `PersistenceFacade` holds a
`{class: mapper}` dict and delegates — a direct translation of
Larman's own sketch in 38.9:

```java
class PersistenceFacade {
    public Object get(OID oid, Class persistenceClass) {
        IMapper mapper = (IMapper) mappers.get(persistenceClass);
        return mapper.get(oid);
    }
}
```

`OID` wraps `item_id` directly rather than a synthetic surrogate key —
`item_id` (e.g. "SKU-001") is already a natural, stable, unique
business key, and Larman's own OID discussion (38.8) doesn't mandate a
generated value, only "a consistent way to relate objects to records."

Crucially, neither `ProductDescription` nor `ProductCatalog` were
touched. `Store` is the coordinator: it optionally takes a
`PersistenceFacade`, loads every saved product into the catalog at
construction, and `Store.add_product()` is the new persistence-aware
entry point that saves through the facade after adding to the
in-memory catalog. `store.catalog.add_product()` still works exactly
as before — it just doesn't persist, which is documented as
deliberate, not a gap.

**Motivation:** This directly implements Larman's own argument against
the alternative (Ch.17, Information Expert contraindications; Ch.38.10)
— had `ProductDescription` saved itself, or inherited from a
`PersistentObject` superclass, it would gain "complex responsibilities
in a new and unrelated area to what the object was previously
responsible for," coupling it to SQL/JDBC-equivalent knowledge and
violating both Low Coupling and High Cohesion. Larman's own words:
"the class no longer focuses on just the pure application logic of
'being a [product]'." Keeping `ProductCatalog`/`ProductDescription`
persistence-ignorant means the domain layer's Iteration-1/2 tests
required zero changes.

**Unresolved Issues:**
- Only `ProductDescription` is persisted so far; `Sale` (with its line
  items and payment) needs its own mapper(s) and will have to address
  Ch.38.19 ("How to Represent Relationships in Tables") — deferred to
  a follow-up Iteration-3 slice.
- No caching layer (Ch.38.14) — every `get`/`get_all` call hits SQLite
  directly. Not a problem yet at this data volume; revisit if it
  becomes one.
- No lazy materialization / virtual proxy (Ch.38.18) — the whole
  catalog loads at Start Up. Reasonable for a single-branch catalog;
  would need revisiting for a much larger product range.

**Alternatives Considered:**
- *Direct mapping* (`ProductDescription` saves itself) — the option
  Larman explicitly develops and then rejects (Ch.38.10); rejected
  here for the same reasons.
- *A `PersistentObject` superclass* that `ProductDescription` inherits
  from for automatic persistence behavior — also explicitly discussed
  and rejected by Larman (Ch.17.12, Ch.38.20): "highly couples domain
  objects to a particular technical service and mixes different
  architectural concerns."
- *A class-based `PersistenceFactory`* mirroring `PaymentGatewayFactory`
  — rejected as unnecessary: `PaymentGatewayFactory` earns its
  Singleton/class shape by resolving between several runtime-selectable
  providers; wiring one SQLite connection to one mapper is a fixed,
  one-time assembly, so a plain function (`build_sqlite_persistence_facade`)
  is enough. Introducing a class here would be pattern-for-pattern's
  sake.

---

### Sale history persistence

**Issue:** Following on from the product catalog, `Sale` (with its
line items and payment) needed to survive a restart too — but `Sale`
is a much bigger step than `ProductDescription`: it has a one-to-many
relationship (line items) and a polymorphic `Payment`
(`CashPayment` / `MobileMoneyPayment` / `CardPayment`), and Larman's
Ch.38 covers the former (38.19) but never actually addresses the
latter — 38.19 is titled "How to Represent Relationships in Tables"
and covers one-to-one / one-to-many / many-to-many associations only;
inheritance-to-table mapping isn't in this book at all.

**Solution Summary:** Persist a read-only historical *snapshot*
(`CompletedSaleRecord`) rather than attempt to reconstruct the live
`Sale`/`Payment` object graph. One-to-many line items follow Larman's
own 38.19 prescription exactly (a foreign-key associative table).
Payment polymorphism is handled by a small, explicitly-scoped
`isinstance` dispatch confined to the one mapper class responsible for
all of this entity's SQL (consistent with 38.15).

**Factors:**
- `MobileMoneyPayment`/`CardPayment` hold a live
  `IPaymentGatewayAdapter` collaborator (a runtime dependency, not
  data) — there is no meaningful way to "reconstruct" one from a
  database row, so attempting a full live-object round trip for
  `Payment` doesn't just lack book guidance, it doesn't actually make
  sense.
- What Iteration 3's reporting requirement (still upcoming) actually
  needs is historical, read-only sales data — not a resumable live
  transaction.
- `Store.completed_sales` (this session's live `Sale` objects, existing
  since Iteration 1) must not change shape or behavior.

**Solution:** `CompletedSaleRecord` / `CompletedSaleLineItemRecord` are
new, persistence-facing value types — deliberately distinct from the
domain's `Sale`/`SalesLineItem`. `CompletedSaleMapper.save(sale)` takes
the live domain `Sale` (as `ProductDescriptionMapper.save()` takes a
live `ProductDescription`) and translates it into two tables:
`completed_sales` (one row per sale, `date_time`/`total`/
`payment_method`/`payment_reference`/`amount_tendered`/`change_due`)
and `completed_sale_line_items` (one row per line item, carrying a
`sale_oid` foreign key back to its parent — exactly Larman's 38.19
one-to-many prescription: "create an associative table that records
the OIDs of each object in relationship"). `get()`/`get_all()` return
`CompletedSaleRecord`, not a resurrected `Sale` — an intentional
asymmetry with `save()`'s input type, so `CompletedSaleMapper` isn't
forced into `ProductDescriptionMapper`'s symmetric `IMapper[T]` shape
just for consistency's sake.

Since `Sale` has no natural business key (unlike `ProductDescription`'s
`item_id`), its `OID` is a generated `uuid.uuid4()` hex string — Larman
explicitly allows this ("database sequence generators... to globally
unique... and others" — 38.8).

`Store` keeps `completed_sales` completely untouched (still this
session's live `Sale` objects, in memory, reset on restart) and adds a
clearly distinct `sale_history()` — the durable, persisted,
cross-session view, sourced from `CompletedSaleMapper.get_all()`.
`Store.log_completed_sale()` (already the single place a completed
sale gets logged, since Iteration 1) now also calls
`sale_history_mapper.save(sale)` when a mapper is present.

**Motivation:** Naming the asymmetry rather than hiding it is more
honest design than contorting `CompletedSaleMapper` to fit
`ProductDescriptionMapper`'s shape, or worse, trying to make `Payment`
reconstructible when its whole reason for existing (authorizing
against a live adapter) has already happened and can't be replayed
from stored data. This mirrors a judgment call Larman himself makes
throughout the book: match the design to what the persisted data is
actually *for*, not to an abstract ideal of full object-graph fidelity.

**Unresolved Issues:**
- The `isinstance` dispatch in `_payment_method_of()` /
  `_payment_reference_of()` works cleanly for 3 known payment types.
  A 4th type means editing this mapper directly. If payment types grow
  substantially, a `PaymentSnapshot`-per-type value object (each
  `Payment` subclass producing its own snapshot without knowing about
  SQL) would scale better — not needed yet.
- No reporting layer reads `sale_history()` yet — this slice only
  proves the data survives and is retrievable; Iteration 3's actual
  Reporting work is still a separate, not-yet-started item.
- `CompletedSaleRecord` currently has no `get_by_date_range` or similar
  query — `get_all()` returns everything, ordered by date. Fine at
  current data volume; a reporting slice will likely need to add
  filtered queries to the mapper.

**Alternatives Considered:**
- *Reconstruct a live `Sale` with a live `Payment` from storage* —
  rejected: `Payment` subclasses need a live gateway adapter reference
  that has no persisted equivalent; even setting that aside,
  re-inflating a "completed" sale as though it were still open invites
  bugs (could someone call `.make_payment()` on it again?).
- *A `PersistentObject`-style base for `Sale`* — rejected for the same
  reasons as the product catalog slice (Ch.17.12, Ch.38.20).
- *Folding `CompletedSaleMapper` into `PersistenceFacade`'s
  `{class: mapper}` dict* — rejected: the Facade's contract implies
  `get_all(X)` returns things shaped like `X`; registering `Sale` to a
  mapper that returns `CompletedSaleRecord` would violate that
  implicit contract silently. Two small, honestly-scoped wiring
  functions (`build_sqlite_persistence_facade`,
  `build_sqlite_sale_history_mapper`) are clearer than one that lies
  about its return shape.
