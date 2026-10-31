# Brightloop Subscription Management System — Task 2: Plans, Quotations & Lifecycle Engine

## 🎯 Architecture & Responsibility
- **Lead Architect**: Ritesh Tiwari (`riteshtiwari8586@gmail.com`)
- **Assigned Scope**: Task 2 — Subscription Plans Matrix, Quotation Engine & Lifecycle State Machine
- **Git Branch**: `feature/plans-and-quotations`
- **Event**: Odoo x FLUX Lucknow Hackathon '26

---

## ⚡ Key Implemented Deliverables

### 1. Subscription Plans Matrix & Governance Policies
- **Recurrence Frequencies**: Daily Nano (1 Day), Agile Sprint (Weekly, 7 Days), Mid-Market Growth (Monthly, 30 Days), and Enterprise Cloud Core (Yearly, 365 Days).
- **Seat Limit Controls**: Dynamically validates and enforces minimum committed seat rules (e.g. Min 5 or 10 seats required for Enterprise tiers).
- **Contract Policies**:
  - `auto_close_on_end`: Automatic termination upon expiration.
  - `allow_early_close`: Early cancellation with calculated proration credits.
  - `allow_pause`: Customer pause/resume lifecycle locks.
  - `allow_renew`: Frictionless renewal mechanisms.

### 2. Dynamic Quotation Studio & Smart Pass
- **Live Variant Surcharges**: Core Cloud ERP (,200/yr) with real-time toggle for **Odoo Enterprise Variant Surcharge (+ .00 / seat)**.
- **Enterprise Add-On Line Items**: 24/7 Mission-Critical SLA Support (+/mo) and Cloud Hot-Failover (+/mo).
- **Dynamic Volume Discount Curve**: 5% off (10+ seats), 10% off (25+ seats), 15% off (50+ seats).
- **Tax Engine**: Strict 18% GST (CGST 9% + SGST 9% / IGST 18%).
- **Digital Document Pass**: 30-day validity verification countdown, cryptographic hash seal, and barcode.
- **One-Click Activation**: Instant conversion into active subscription with confetti celebration and state transition.

### 3. Subscription Lifecycle State Machine
- Strict deterministic states:
  `Draft` ➔ `Quotation` ➔ `Confirmed` ➔ `Active` ⮂ `Paused` ➔ `Closed`
- Policy-governed safeguards preventing unauthorized state jumps.
- Automated proration credit calculation on early contract closure.

### 4. Interactive Simulation & Odoo 18 Wire Protocol Inspector
- **Time-Travel Console**: Advance virtual system clock by `+1 Day`, `+7 Days`, or `+30 Days Full Cycle` to simulate lifecycle progression and recurring invoicing.
- **Odoo 18 RPC Wire Drawer**: Real-time simulated JSON-RPC/XML-RPC call logs mirroring Odoo 18 backend conventions (`sale.subscription.create`, `cron.recurring_invoicing_cron`).
- **Command Palette (`Cmd + K`)**: Floating spotlight command hub.
- **Tactile Web Audio API Feedback**: Subtle click and success chimes.
- **In-App Theme Switcher**: 3 distinctive organic luxury themes (Deep Olive Luxe, Forest Noir, Nordic Sage).

---

## 🚀 Quick Start
To launch and inspect the interactive Studio:
```bash
open index.html
```

## 📂 Backend Odoo Models
Located under `models/`:
- `subscription_plan.py`: `brightloop.subscription.plan`
- `quotation_template.py`: `brightloop.quotation.template`
- `subscription.py`: `brightloop.subscription`
