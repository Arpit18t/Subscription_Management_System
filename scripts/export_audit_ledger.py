#!/usr/bin/env python3
"""
=============================================================================
Brightloop Subscription Engine — Financial Reconciliation & Audit Ledger Exporter
Odoo x FLUX Lucknow Hackathon '26 (Member 2 / Task 2)
Author: Ritesh Tiwari
=============================================================================
This production CLI script generates full compliance audit ledgers (CSV & JSON)
for all active, paused, closed, and quotation-stage subscriptions.
Verifies:
  - 18% GST Compliance (CGST 9% + SGST 9%)
  - Odoo Enterprise Variant Surcharges (+$560/seat)
  - Proration Credits & Net Recognized Revenue
  - MRR & ARR Breakdown
=============================================================================
"""

import csv
import json
import os
import sys
from datetime import datetime, timedelta

SAMPLE_SUBSCRIPTIONS = [
    {
        "id": "SUB-2026-001",
        "partner_name": "Nexus Global Corp",
        "partner_gstin": "09AAACN1234F1Z5",
        "plan_name": "Enterprise Cloud Core",
        "billing_cycle": "365-day",
        "seats": 25,
        "base_rate": 4999.00,
        "variant": "Odoo Enterprise Edition",
        "variant_surcharge_per_seat": 560.00,
        "core_erp_fee": 1200.00,
        "state": "active",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "prorated_credit": 0.00
    },
    {
        "id": "SUB-2026-002",
        "partner_name": "Kinetix Technologies",
        "partner_gstin": "07BBBPK9876E1Z2",
        "plan_name": "Mid-Market Growth",
        "billing_cycle": "30-day",
        "seats": 12,
        "base_rate": 599.00,
        "variant": "Odoo Enterprise Edition",
        "variant_surcharge_per_seat": 560.00,
        "core_erp_fee": 0.00,
        "state": "active",
        "start_date": "2026-02-01",
        "end_date": "2026-03-03",
        "prorated_credit": 0.00
    },
    {
        "id": "SUB-2026-003",
        "partner_name": "Apex Logistics Ltd",
        "partner_gstin": "27AABCA4321D1ZM",
        "plan_name": "Agile Sprint",
        "billing_cycle": "7-day",
        "seats": 8,
        "base_rate": 199.00,
        "variant": "Standard Community",
        "variant_surcharge_per_seat": 0.00,
        "core_erp_fee": 0.00,
        "state": "paused",
        "start_date": "2026-02-15",
        "end_date": "2026-02-22",
        "prorated_credit": 0.00
    },
    {
        "id": "SUB-2026-004",
        "partner_name": "Vortex Dynamics Inc",
        "partner_gstin": "09CCCVD5432G1Z8",
        "plan_name": "Enterprise Cloud Core",
        "billing_cycle": "365-day",
        "seats": 50,
        "base_rate": 4999.00,
        "variant": "Odoo Enterprise Edition",
        "variant_surcharge_per_seat": 560.00,
        "core_erp_fee": 1200.00,
        "state": "active",
        "start_date": "2026-01-15",
        "end_date": "2027-01-14",
        "prorated_credit": 0.00
    },
    {
        "id": "SUB-2026-005",
        "partner_name": "Solaria Analytics",
        "partner_gstin": "29DDDPS1111H1Z0",
        "plan_name": "Daily Elastic",
        "billing_cycle": "1-day",
        "seats": 4,
        "base_rate": 49.00,
        "variant": "Standard Community",
        "variant_surcharge_per_seat": 0.00,
        "core_erp_fee": 0.00,
        "state": "closed",
        "start_date": "2026-02-20",
        "end_date": "2026-02-21",
        "prorated_credit": 49.00
    },
    {
        "id": "SUB-2026-006",
        "partner_name": "Zenith Mediaworks",
        "partner_gstin": "06EEEZM8888K1Z4",
        "plan_name": "Mid-Market Growth",
        "billing_cycle": "30-day",
        "seats": 15,
        "base_rate": 599.00,
        "variant": "Odoo Enterprise Edition",
        "variant_surcharge_per_seat": 560.00,
        "core_erp_fee": 0.00,
        "state": "quotation",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "prorated_credit": 0.00
    }
]

def calculate_financials(sub):
    total_surcharge = sub["seats"] * sub["variant_surcharge_per_seat"]
    subtotal = sub["base_rate"] + total_surcharge + sub["core_erp_fee"]
    cgst = round(subtotal * 0.09, 2)
    sgst = round(subtotal * 0.09, 2)
    total_tax = cgst + sgst
    gross_total = round(subtotal + total_tax, 2)
    net_revenue = round(gross_total - sub["prorated_credit"], 2)
    
    # Calculate MRR / ARR contribution
    if sub["billing_cycle"] == "365-day":
        mrr = round(subtotal / 12, 2)
        arr = subtotal
    elif sub["billing_cycle"] == "30-day":
        mrr = subtotal
        arr = subtotal * 12
    elif sub["billing_cycle"] == "7-day":
        mrr = round(subtotal * 4.33, 2)
        arr = round(subtotal * 52, 2)
    else:  # 1-day
        mrr = round(subtotal * 30, 2)
        arr = round(subtotal * 365, 2)
        
    return {
        "subtotal": subtotal,
        "total_surcharge": total_surcharge,
        "cgst_9": cgst,
        "sgst_9": sgst,
        "total_tax_18": total_tax,
        "gross_total": gross_total,
        "net_revenue": net_revenue,
        "mrr": mrr,
        "arr": arr
    }

def generate_ledger():
    os.makedirs("exports", exist_ok=True)
    csv_file = os.path.join("exports", "subscriptions_audit_ledger.csv")
    json_file = os.path.join("exports", "subscriptions_audit_ledger.json")
    
    records = []
    total_active_mrr = 0.0
    total_active_arr = 0.0
    total_surcharge_collected = 0.0
    total_gst_collected = 0.0
    total_gross = 0.0
    
    for sub in SAMPLE_SUBSCRIPTIONS:
        fin = calculate_financials(sub)
        record = {**sub, **fin}
        records.append(record)
        
        if sub["state"] in ["active", "paused"]:
            total_active_mrr += fin["mrr"]
            total_active_arr += fin["arr"]
        
        total_surcharge_collected += fin["total_surcharge"]
        total_gst_collected += fin["total_tax_18"]
        total_gross += fin["gross_total"]

    # Write CSV
    headers = [
        "id", "partner_name", "partner_gstin", "plan_name", "billing_cycle",
        "seats", "base_rate", "variant", "variant_surcharge_per_seat",
        "total_surcharge", "core_erp_fee", "subtotal", "cgst_9", "sgst_9",
        "total_tax_18", "gross_total", "prorated_credit", "net_revenue",
        "state", "mrr", "arr", "start_date", "end_date"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)

    # Write JSON
    summary_data = {
        "generated_at": datetime.now().isoformat() + "Z",
        "author": "Ritesh Tiwari",
        "hackathon_scope": "Odoo x FLUX Lucknow Hackathon '26 (Task 2)",
        "metrics": {
            "total_subscriptions": len(records),
            "active_subscriptions": sum(1 for r in records if r["state"] == "active"),
            "paused_subscriptions": sum(1 for r in records if r["state"] == "paused"),
            "closed_subscriptions": sum(1 for r in records if r["state"] == "closed"),
            "quotations_pending": sum(1 for r in records if r["state"] == "quotation"),
            "total_active_mrr_usd": round(total_active_mrr, 2),
            "total_active_arr_usd": round(total_active_arr, 2),
            "total_odoo_variant_surcharges_usd": round(total_surcharge_collected, 2),
            "total_gst_collected_usd": round(total_gst_collected, 2),
            "total_gross_portfolio_value_usd": round(total_gross, 2)
        },
        "subscriptions": records
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Print Terminal Visual Audit
    print("=" * 82)
    print(" BRIGHTLOOP SUBSCRIPTION ENGINE — RECONCILIATION AUDIT LEDGER")
    print(" Author: Ritesh Tiwari | Task 2: Plans, Quotations & Lifecycle State Machine")
    print("=" * 82)
    print(f" {'ID':<14} | {'Plan':<22} | {'Seats':<5} | {'Subtotal':<11} | {'GST (18%)':<10} | {'Status':<9}")
    print("-" * 82)
    for r in records:
        print(f" {r['id']:<14} | {r['plan_name']:<22} | {r['seats']:<5} | ${r['subtotal']:<10.2f} | ${r['total_tax_18']:<9.2f} | {r['state'].upper():<9}")
    print("=" * 82)
    print(" FINANCIAL RECONCILIATION SUMMARY:")
    print(f"   • Total Portfolio Gross Value:      ${total_gross:,.2f}")
    print(f"   • Total Active MRR (Monthly Run):   ${total_active_mrr:,.2f}")
    print(f"   • Total Active ARR (Annualized):    ${total_active_arr:,.2f}")
    print(f"   • Odoo Surcharge (+$560/seat):      ${total_surcharge_collected:,.2f}")
    print(f"   • GST Output Liability (18%):       ${total_gst_collected:,.2f}")
    print("-" * 82)
    print(f" [SUCCESS] CSV Ledger written to:  {csv_file}")
    print(f" [SUCCESS] JSON Ledger written to: {json_file}")
    print("=" * 82)

if __name__ == '__main__':
    generate_ledger()
