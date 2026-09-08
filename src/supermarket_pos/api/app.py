"""Thin FastAPI layer that exposes Store / Register to the web UI.

The domain layer remains completely unaware of HTTP / FastAPI.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.payment_declined_error import PaymentDeclinedError
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store


# ---------- Request / Response models ----------

class EnterItemRequest(BaseModel):
    item_id: str
    quantity: int = Field(gt=0, default=1)


class CashPaymentRequest(BaseModel):
    amount_tendered: str


class MobileMoneyPaymentRequest(BaseModel):
    provider: str          # "mtn" or "airtel"
    phone_number: str
    amount: Optional[str] = None   # defaults to current total


class CardPaymentRequest(BaseModel):
    card_reference: str
    amount: Optional[str] = None


class LineItemOut(BaseModel):
    item_id: str
    description: str
    quantity: int
    unit_price: str
    subtotal: str


class SaleStateOut(BaseModel):
    is_complete: bool
    item_count: int
    subtotal: str
    total: str
    line_items: List[LineItemOut]


# ---------- Application factory ----------

def create_app(store: Store | None = None) -> FastAPI:
    if store is None:
        store = _create_demo_store()

    app = FastAPI(title="Supermarket POS", version="0.2.0")
    register = store.register

    # ----- Sale endpoints -----

    @app.post("/api/sale/new")
    def new_sale():
        register.make_new_sale()
        return {"status": "ok", "message": "New sale started"}

    @app.post("/api/sale/enter-item", response_model=SaleStateOut)
    def enter_item(body: EnterItemRequest):
        try:
            register.enter_item(body.item_id, body.quantity)
        except ProductNotFoundError:
            raise HTTPException(status_code=404, detail=f"Product '{body.item_id}' not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _sale_state(register)

    @app.post("/api/sale/end", response_model=SaleStateOut)
    def end_sale():
        sale = register.current_sale
        if sale is None or not sale.line_items:
            raise HTTPException(status_code=400, detail="No items in current sale")
        if not sale.is_complete():
            register.end_sale()
        return _sale_state(register)

    @app.get("/api/sale/current", response_model=SaleStateOut)
    def current_sale():
        return _sale_state(register)

    # ----- Payment endpoints -----

    @app.post("/api/payment/cash")
    def pay_cash(body: CashPaymentRequest):
        _ensure_complete_sale(register)
        try:
            change = register.make_cash_payment(Money(body.amount_tendered))
            return {
                "status": "ok",
                "message": "Cash payment successful",
                "change_due": str(change),
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/payment/mobile-money")
    def pay_mobile_money(body: MobileMoneyPaymentRequest):
        _ensure_complete_sale(register)
        amount = Money(body.amount) if body.amount else register.current_sale.get_total()
        try:
            register.make_mobile_money_payment(body.provider, body.phone_number, amount)
            return {"status": "ok", "message": f"{body.provider.upper()} payment approved"}
        except PaymentDeclinedError as exc:
            raise HTTPException(status_code=402, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/payment/card")
    def pay_card(body: CardPaymentRequest):
        _ensure_complete_sale(register)
        amount = Money(body.amount) if body.amount else register.current_sale.get_total()
        try:
            register.make_card_payment(body.card_reference, amount)
            return {"status": "ok", "message": "Card payment approved"}
        except PaymentDeclinedError as exc:
            raise HTTPException(status_code=402, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # ----- Catalog helper -----

    @app.get("/api/products")
    def list_products():
        products = []
        for desc in store.catalog.all_products():
            products.append({
                "item_id": desc.item_id,
                "description": desc.description,
                "price": str(desc.price),
                "stock": store.inventory.get_stock_level(desc.item_id),
            })
        return products

    # ----- Serve the simple frontend -----

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTML_PAGE

    return app


def _sale_state(register) -> SaleStateOut:
    sale = register.current_sale
    if sale is None:
        return SaleStateOut(
            is_complete=False,
            item_count=0,
            subtotal="0.00",
            total="0.00",
            line_items=[],
        )

    lines = []
    total_qty = 0
    for line in sale.line_items:
        total_qty += line.quantity
        lines.append(LineItemOut(
            item_id=line.description.item_id,
            description=line.description.description,
            quantity=line.quantity,
            unit_price=str(line.description.price),
            subtotal=str(line.get_subtotal()),
        ))

    return SaleStateOut(
        is_complete=sale.is_complete(),
        item_count=total_qty,
        subtotal=str(sale.get_subtotal()),
        total=str(sale.get_total()),
        line_items=lines,
    )


def _ensure_complete_sale(register) -> None:
    sale = register.current_sale
    if sale is None or not sale.line_items:
        raise HTTPException(status_code=400, detail="No active sale with items")
    if not sale.is_complete():
        register.end_sale()


def _create_demo_store() -> Store:
    store = Store("Pick n Pay POS — Demo Branch", "Lusaka, Zambia")
    products = [
        ("SKU-001", "2kg Mealie Meal", "85.00"),
        ("SKU-002", "1L Cooking Oil", "65.50"),
        ("SKU-003", "Loaf of Bread", "18.00"),
        ("SKU-004", "500g Sugar", "32.00"),
        ("SKU-005", "1L Fresh Milk", "22.50"),
        ("SKU-006", "Bar of Soap", "15.00"),
        ("SKU-007", "Pack of Eggs (12)", "45.00"),
        ("SKU-008", "2L Soft Drink", "28.00"),
    ]
    for item_id, desc, price in products:
        store.catalog.add_product(ProductDescription(item_id, desc, Money(price)))
        store.inventory.receive_stock(item_id, 50)
    return store


# ---------- Simple single-page frontend ----------

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pick n Pay POS</title>
  <style>
    :root {
      --primary: #e30613;
      --dark: #1a1a1a;
      --bg: #f5f5f5;
      --card: #ffffff;
      --border: #ddd;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--dark);
      min-height: 100vh;
    }
    header {
      background: var(--primary);
      color: white;
      padding: 1rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    header h1 { font-size: 1.4rem; }
    #status { font-size: 0.9rem; opacity: 0.9; }
    .container {
      display: grid;
      grid-template-columns: 1fr 320px;
      gap: 1.25rem;
      max-width: 1100px;
      margin: 1.25rem auto;
      padding: 0 1rem;
    }
    .card {
      background: var(--card);
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      padding: 1.25rem;
    }
    h2 { font-size: 1rem; margin-bottom: 0.75rem; color: #555; }
    .entry-row {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    input, select, button {
      font: inherit;
      padding: 0.55rem 0.75rem;
      border-radius: 6px;
      border: 1px solid var(--border);
    }
    input { flex: 1; }
    button {
      background: var(--primary);
      color: white;
      border: none;
      cursor: pointer;
      font-weight: 600;
    }
    button:hover { filter: brightness(1.08); }
    button.secondary { background: #444; }
    button.ghost { background: transparent; color: var(--dark); border: 1px solid var(--border); }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.55rem 0.4rem; text-align: left; border-bottom: 1px solid #eee; }
    th { font-size: 0.8rem; color: #777; }
    td:last-child, th:last-child { text-align: right; }
    .totals { margin-top: 1rem; }
    .totals .row { display: flex; justify-content: space-between; margin: 0.3rem 0; }
    .totals .grand { font-size: 1.5rem; font-weight: 700; margin-top: 0.5rem; }
    .pay-section { margin-top: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; }
    .pay-section input { width: 100%; }
    .msg { margin-top: 0.75rem; padding: 0.6rem; border-radius: 6px; font-size: 0.9rem; display: none; }
    .msg.ok { background: #e6f7e9; color: #0a7a2f; display: block; }
    .msg.err { background: #fde8e8; color: #b00020; display: block; }
    @media (max-width: 800px) {
      .container { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Pick n Pay POS</h1>
    <span id="status">Ready</span>
  </header>

  <div class="container">
    <!-- Left: cart -->
    <div class="card">
      <h2>Cart</h2>
      <div class="entry-row">
        <input id="itemId" placeholder="Item ID (e.g. SKU-001)" list="productList" />
        <input id="qty" type="number" value="1" min="1" style="width:70px" />
        <button onclick="addItem()">Add</button>
      </div>
      <datalist id="productList"></datalist>

      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Description</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Subtotal</th>
          </tr>
        </thead>
        <tbody id="cartBody"></tbody>
      </table>
      <div id="msg" class="msg"></div>
    </div>

    <!-- Right: totals + payment -->
    <div class="card">
      <h2>Totals</h2>
      <div class="totals">
        <div class="row"><span>Items</span><span id="itemCount">0</span></div>
        <div class="row"><span>Subtotal</span><span id="subtotal">K 0.00</span></div>
        <div class="row grand"><span>TOTAL</span><span id="total">K 0.00</span></div>
      </div>

      <div class="pay-section">
        <button class="secondary" onclick="endSale()">End Sale / Ready for Payment</button>
        <input id="tendered" placeholder="Amount tendered (cash)" />
        <button onclick="payCash()">Pay Cash</button>
        <button onclick="payMobile('mtn')">Pay MTN MoMo</button>
        <button onclick="payMobile('airtel')">Pay Airtel Money</button>
        <button onclick="payCard()">Pay Card</button>
        <button class="ghost" onclick="newSale()">New Sale</button>
      </div>
    </div>
  </div>

  <script>
    async function api(path, opts = {}) {
      const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...opts,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || res.statusText);
      return data;
    }

    function showMsg(text, ok = true) {
      const el = document.getElementById("msg");
      el.textContent = text;
      el.className = "msg " + (ok ? "ok" : "err");
    }

    function render(state) {
      const body = document.getElementById("cartBody");
      body.innerHTML = "";
      (state.line_items || []).forEach(l => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${l.item_id}</td>
          <td>${l.description}</td>
          <td>${l.quantity}</td>
          <td>${l.unit_price}</td>
          <td>${l.subtotal}</td>`;
        body.appendChild(tr);
      });
      document.getElementById("itemCount").textContent = state.item_count;
      document.getElementById("subtotal").textContent = "K " + state.subtotal;
      document.getElementById("total").textContent = "K " + state.total;
      document.getElementById("status").textContent =
        state.is_complete ? "Sale complete — choose payment" : "Sale in progress";
    }

    async function refresh() {
      const state = await api("/api/sale/current");
      render(state);
    }

    async function newSale() {
      await api("/api/sale/new", { method: "POST" });
      document.getElementById("tendered").value = "";
      showMsg("New sale started");
      await refresh();
    }

    async function addItem() {
      const item_id = document.getElementById("itemId").value.trim();
      const quantity = parseInt(document.getElementById("qty").value || "1", 10);
      if (!item_id) return;
      try {
        const state = await api("/api/sale/enter-item", {
          method: "POST",
          body: JSON.stringify({ item_id, quantity }),
        });
        document.getElementById("itemId").value = "";
        document.getElementById("qty").value = "1";
        showMsg(`Added ${item_id} × ${quantity}`);
        render(state);
      } catch (e) {
        showMsg(e.message, false);
      }
    }

    async function endSale() {
      try {
        const state = await api("/api/sale/end", { method: "POST" });
        showMsg("Sale ended. Total: K " + state.total);
        render(state);
      } catch (e) {
        showMsg(e.message, false);
      }
    }

    async function payCash() {
      let amount = document.getElementById("tendered").value.trim();
      if (!amount) {
        const state = await api("/api/sale/current");
        amount = state.total;
      }
      try {
        const res = await api("/api/payment/cash", {
          method: "POST",
          body: JSON.stringify({ amount_tendered: amount }),
        });
        showMsg(res.message + " — Change: " + res.change_due);
        await newSale();
      } catch (e) {
        showMsg(e.message, false);
      }
    }

    async function payMobile(provider) {
      const phone = prompt("Customer phone number:", "0977123456");
      if (!phone) return;
      try {
        const res = await api("/api/payment/mobile-money", {
          method: "POST",
          body: JSON.stringify({ provider, phone_number: phone }),
        });
        showMsg(res.message);
        await newSale();
      } catch (e) {
        showMsg(e.message, false);
      }
    }

    async function payCard() {
      const ref = prompt("Card / reference number:", "4111111111111111");
      if (!ref) return;
      try {
        const res = await api("/api/payment/card", {
          method: "POST",
          body: JSON.stringify({ card_reference: ref }),
        });
        showMsg(res.message);
        await newSale();
      } catch (e) {
        showMsg(e.message, false);
      }
    }

    // Load products for autocomplete + start a sale
    (async () => {
      try {
        const products = await api("/api/products");
        const list = document.getElementById("productList");
        products.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.item_id;
          opt.label = `${p.description} (${p.price})`;
          list.appendChild(opt);
        });
        await newSale();
      } catch (e) {
        showMsg("Failed to load: " + e.message, false);
      }
    })();

    // Enter key support
    document.getElementById("itemId").addEventListener("keydown", e => {
      if (e.key === "Enter") addItem();
    });
    document.getElementById("qty").addEventListener("keydown", e => {
      if (e.key === "Enter") addItem();
    });
  </script>
</body>
</html>
"""