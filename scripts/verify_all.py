#!/usr/bin/env python3
"""
=============================================================================
Brightloop Subscription Engine — Master Verification Runner
Odoo x FLUX Lucknow Hackathon '26 (Member 2 / Task 2)
Author: Ritesh Tiwari
=============================================================================
Runs all integration test suites, benchmarks, exporters, and sync clients.
Returns exit code 0 only if 100% of all components pass.
=============================================================================
"""

import os
import sys
import subprocess
import time

def run_step(title, command):
    print("\n" + "=" * 76)
    print(f" [RUNNING] {title}")
    print("=" * 76)
    t0 = time.time()
    res = subprocess.run(command, shell=True)
    dt = time.time() - t0
    if res.returncode == 0:
        print(f"\n [PASS] {title} completed successfully in {dt:.2f}s")
        return True
    else:
        print(f"\n [FAIL] {title} failed with code {res.returncode}")
        return False

def main():
    print("*" * 76)
    print(" BRIGHTLOOP SUBSCRIPTION ENGINE — TASK 2 FULL SYSTEM VERIFICATION")
    print(" Author: Ritesh Tiwari | Lucknow Hackathon '26")
    print("*" * 76)

    steps = [
        ("Automated Unit Test Suite", "python3 tests/test_plans_and_lifecycle.py"),
        ("Financial Audit Ledger Exporter", "python3 scripts/export_audit_ledger.py"),
        ("Odoo 18 XML-RPC Sync Client", "python3 scripts/odoo_sync_client.py"),
        ("State Machine Concurrency Benchmark", "python3 benchmarks/benchmark_state_machine.py")
    ]

    all_passed = True
    for title, cmd in steps:
        if not run_step(title, cmd):
            all_passed = False
            break

    print("\n" + "=" * 76)
    if all_passed:
        print(" [ALL 4 VERIFICATION SUITES PASSED 100%]")
        print(" Task 2: Subscription Plans, Quotations & State Machine is complete!")
        print(" Ready for final Pull Request merge.")
    else:
        print(" [VERIFICATION FAILED] Inspect logs above.")
        sys.exit(1)
    print("=" * 76)

if __name__ == "__main__":
    main()
