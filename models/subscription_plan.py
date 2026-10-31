# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SubscriptionPlan(models.Model):
    _name = 'brightloop.subscription.plan'
    _description = 'Subscription Plan Matrix'

    name = fields.Char(string='Plan Name', required=True)
    code = fields.Char(string='Plan Code', required=True)
    billing_interval = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Billing Frequency', default='monthly', required=True)
    cost = fields.Float(string='Base Plan Cost', required=True)
    min_quantity = fields.Integer(string='Minimum Quantity', default=1)
    start_date = fields.Date(string='Available From', default=fields.Date.today)
    end_date = fields.Date(string='Available Until')
    
    auto_close_on_end = fields.Boolean(string='Auto-Close When Ended', default=False)
    allow_early_close = fields.Boolean(string='Allow Early Close', default=True)
    allow_pause = fields.Boolean(string='Allow Pause', default=True)
    allow_renew = fields.Boolean(string='Allow Renew', default=True)
    active = fields.Boolean(string='Active', default=True)
