# Brightloop Subscription Engine — API Specification & Architecture Guide
**Odoo x FLUX Lucknow Hackathon '26**  
**Module**: Subscription Plans Matrix, Quotation Engine & Lifecycle State Machine (Task 2)  
**Author**: Ritesh Tiwari (`riteshtiwari8586@gmail.com`)  
**Target Environment**: Odoo 18 Community & Enterprise / RESTful Gateway  

---

## 1. System Architecture Overview

The **Task 2 Engine** manages multi-tiered SaaS billing lifecycles with strict Indian GST compliance (18%) and automated Odoo variant surcharging ($560/seat).

```
+-------------------------------------------------------------------------------+
|                       BRIGHTLOOP WEB STUDIO / FRONTEND                        |
|       (ZeBeyond Industrial Design Language: Obsidian Matte & Electric Green)  |
+-------------------------------------------------------------------------------+
                                      |
                           JSON-RPC / REST Gateway
                                      v
+-------------------------------------------------------------------------------+
|                         TASK 2 CORE BUSINESS LOGIC                            |
|  +-------------------------+  +----------------------+  +------------------+  |
|  | Plans Matrix & Minimum  |  | Quotation Engine &   |  | State Machine    |  |
|  | Seats Guard             |  | 18% GST + Surcharge  |  | Lifecycle Engine |  |
|  +-------------------------+  +----------------------+  +------------------+  |
+-------------------------------------------------------------------------------+
                                      |
                          Odoo 18 XML-RPC Wire Client
                                      v
+-------------------------------------------------------------------------------+
|                         ODOO 18 BACKEND MODELS                                |
|  - brightloop.subscription.plan    ->   product.template                      |
|  - brightloop.quotation.template   ->   sale.order                            |
|  - brightloop.subscription         ->   account.move & delivery records        |
+-------------------------------------------------------------------------------+
```

---

## 2. Subscription Plans Matrix

| Plan Name | Plan Code | Billing Cycle | Base Price | Min. Seats | Surcharge Eligible |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Daily Elastic** | `PLAN-DAILY` | 1 Day | $49.00 / day | 1 Seat | No |
| **Agile Sprint** | `PLAN-WEEKLY` | 7 Days | $199.00 / week | 3 Seats | No |
| **Mid-Market Growth** | `PLAN-MONTHLY` | 30 Days | $599.00 / mo | 5 Seats | Yes (+$560/seat) |
| **Enterprise Cloud Core**| `PLAN-ANNUAL` | 365 Days | $4,999.00 / yr | 10 Seats | Yes (+$560/seat + Core ERP) |

---

## 3. Financial Calculation Formula

The Quotation Engine executes deterministic multi-factor pricing:

$$\text{Subtotal} = \text{Base Price} + (\text{Seats} \times \text{Variant Surcharge}) + \text{Core ERP Fee}$$

$$\text{CGST (9\%)} = \text{round}(\text{Subtotal} \times 0.09, 2)$$
$$\text{SGST (9\%)} = \text{round}(\text{Subtotal} \times 0.09, 2)$$
$$\text{Total 18\% GST} = \text{CGST} + \text{SGST}$$
$$\text{Gross Total} = \text{Subtotal} + \text{Total 18\% GST}$$

---

## 4. State Machine Lifecycle Transitions

```
 [ Draft ] ---> [ Quotation ] ---> [ Confirmed ] ---> [ Active ] <---> [ Paused ]
     |                |                   |               |                 |
     +----------------+-------------------+---------------+-----------------+---> [ Closed ]
```

### Transition Matrix & Enforcement Rules:
1. `draft` ➔ `quotation`: Triggered upon quotation creation; sets strict 30-day expiry date.
2. `quotation` ➔ `confirmed`: Customer digital approval; converts to binding agreement.
3. `confirmed` ➔ `active`: Provisioning completed; recurring billing clock initiated.
4. `active` ⮂ `paused`: Temporary hold (maintenance/billing delay); billing clock suspended.
5. Any state ➔ `closed`: Early termination; automatically computes pro-rated refund credit.

---

## 5. 5-Minute Hackathon Demo Script (Presentation Guide)

1. **Minute 1: The Problem & Architecture**  
   - Introduce Brightloop's subscription challenges: flexible intervals, dynamic seat bounds, Indian GST (18%), and ERP variant surcharges.
   - Show high-density ZeBeyond UI inspired by modern engineering tools.

2. **Minute 2: Dynamic Quotation Generation**  
   - Select Enterprise Cloud Core with 25 seats + Odoo Enterprise Edition.
   - Highlight instant surcharge addition ($14,000) and exact CGST (9%) + SGST (9%) breakdown.
   - Demonstrate minimum seat restriction validation (e.g., trying 2 seats on Enterprise rejects immediately).

3. **Minute 3: State Machine in Action**  
   - Progress from Draft ➔ Quotation ➔ Confirmed ➔ Active.
   - Demonstrate Pause state and Resume state.
   - Demonstrate early cancellation with proration calculation.

4. **Minute 4: Odoo 18 Integration & Audit Ledger**  
   - Run `python3 scripts/odoo_sync_client.py` demonstrating XML-RPC synchronization to Odoo.
   - Show `exports/subscriptions_audit_ledger.csv` and `.json` proving compliance.

5. **Minute 5: Performance Benchmarks & Q&A**  
   - Show 3.3M ops/sec sub-microsecond latency state machine benchmark.
   - Invite judges' questions.
