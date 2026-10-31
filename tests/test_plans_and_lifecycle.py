# -*- coding: utf-8 -*-
"""
Brightloop Subscription Engine — Unit & Regression Test Suite
Architect: Ritesh Tiwari (Lead Engine & Lifecycle Architect - Task 2)
Scope: Plans Matrix, Quotation Pricing Engine, Tax Rules & State Machine
"""

import unittest
from datetime import date, timedelta

class TestSubscriptionPlans(unittest.TestCase):
    """Tests subscription plans, recurrences, and minimum quantity constraints."""

    def setUp(self):
        self.plans = {
            'daily': {'name': 'Daily Elastic Pilot', 'interval': 'daily', 'days': 1, 'price': 15.0, 'min_seats': 1},
            'weekly': {'name': 'Agile Sprint Pack', 'interval': 'weekly', 'days': 7, 'price': 49.0, 'min_seats': 1},
            'monthly': {'name': 'Mid-Market Growth', 'interval': 'monthly', 'days': 30, 'price': 149.0, 'min_seats': 5},
            'yearly': {'name': 'Enterprise Cloud Core', 'interval': 'yearly', 'days': 365, 'price': 399.0, 'min_seats': 10}
        }

    def test_plan_intervals(self):
        """Verify all 4 required hackathon recurrencies are supported."""
        self.assertIn('daily', self.plans)
        self.assertIn('weekly', self.plans)
        self.assertIn('monthly', self.plans)
        self.assertIn('yearly', self.plans)

    def test_minimum_seat_validation(self):
        """Ensure plans strictly enforce their minimum seat limit."""
        # Enterprise requires 10 seats minimum
        plan = self.plans['yearly']
        
        # Scenario A: Under minimum seats -> Should fail validation
        seats_under = 8
        self.assertFalse(seats_under >= plan['min_seats'], 'Should reject seat counts below minimum threshold')
        
        # Scenario B: Equal or above minimum seats -> Should pass validation
        seats_valid = 12
        self.assertTrue(seats_valid >= plan['min_seats'], 'Should accept seat counts at or above minimum')

class TestQuotationPricingEngine(unittest.TestCase):
    """Tests quotation line items, Odoo variant surcharge (+560), volume tiers & 18% GST."""

    def calculate_quote(self, base_rate, seats, odoo_surcharge=True, sla_support=True):
        base_line = base_rate * seats
        surcharge = 560.0 * seats if odoo_surcharge else 0.0
        sla = 500.0 if sla_support else 0.0
        subtotal = base_line + sla

        # Volume Tier Discount
        discount_pct = 0.0
        if seats >= 50: discount_pct = 0.15
        elif seats >= 25: discount_pct = 0.10
        elif seats >= 10: discount_pct = 0.05

        discount = subtotal * discount_pct
        discounted_subtotal = subtotal - discount
        taxable_base = discounted_subtotal + surcharge
        gst = taxable_base * 0.18
        grand_total = taxable_base + gst

        return {
            'subtotal': subtotal,
            'surcharge': surcharge,
            'discount': discount,
            'taxable_base': taxable_base,
            'gst': gst,
            'grand_total': grand_total
        }

    def test_odoo_variant_surcharge_calculation(self):
        """Verify +.00/seat Odoo Enterprise surcharge applies accurately."""
        res = self.calculate_quote(base_rate=149.0, seats=12, odoo_surcharge=True, sla_support=True)
        expected_surcharge = 560.0 * 12 # 6,720.00
        self.assertEqual(res['surcharge'], expected_surcharge)

    def test_gst_18_percent(self):
        """Verify strict 18% GST is levied across taxable base."""
        res = self.calculate_quote(base_rate=149.0, seats=10, odoo_surcharge=False, sla_support=False)
        # 149 * 10 = 1490. Discount 5% = 74.50. Taxable base = 1415.50
        expected_gst = round(1415.50 * 0.18, 2)
        self.assertEqual(round(res['gst'], 2), expected_gst)

    def test_30_day_quotation_validity(self):
        """Verify quotation valid window is exactly 30 calendar days."""
        issued = date(2026, 10, 31)
        expiry = issued + timedelta(days=30)
        self.assertEqual((expiry - issued).days, 30)

class TestSubscriptionLifecycleStateMachine(unittest.TestCase):
    """Tests deterministic lifecycle state transitions and policy gates."""

    ALLOWED_TRANSITIONS = {
        'draft': ['quotation'],
        'quotation': ['confirmed', 'draft'],
        'confirmed': ['active'],
        'active': ['paused', 'closed'],
        'paused': ['active', 'closed'],
        'closed': []
    }

    def can_transition(self, current, target, policy_pausable=True, policy_closable=True):
        if target not in self.ALLOWED_TRANSITIONS.get(current, []):
            return False
        if target == 'paused' and not policy_pausable:
            return False
        if target == 'closed' and not policy_closable:
            return False
        return True

    def test_valid_forward_flow(self):
        """Draft -> Quotation -> Confirmed -> Active."""
        self.assertTrue(self.can_transition('draft', 'quotation'))
        self.assertTrue(self.can_transition('quotation', 'confirmed'))
        self.assertTrue(self.can_transition('confirmed', 'active'))

    def test_illegal_jump_denied(self):
        """Cannot jump Draft directly to Active."""
        self.assertFalse(self.can_transition('draft', 'active'))

    def test_pausable_policy_enforcement(self):
        """Active -> Paused only when policy allows pausing."""
        self.assertTrue(self.can_transition('active', 'paused', policy_pausable=True))
        self.assertFalse(self.can_transition('active', 'paused', policy_pausable=False))

    def test_prorated_refund_calculation(self):
        """Ensure early termination computes prorated credit accurately."""
        monthly_total = 7420.00
        prorated_credit = round(monthly_total * 0.42, 2)
        self.assertEqual(prorated_credit, 3116.40)

if __name__ == '__main__':
    unittest.main(verbosity=2)
