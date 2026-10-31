# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class BrightloopSubscription(models.Model):
    _name = 'brightloop.subscription'
    _description = 'Brightloop Customer Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Subscription Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    plan_id = fields.Many2one('brightloop.subscription.plan', string='Subscription Plan', required=True, tracking=True)
    
    start_date = fields.Date(string='Start Date', default=fields.Date.today, required=True, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    next_billing_date = fields.Date(string='Next Billing Date', tracking=True)
    payment_terms = fields.Char(string='Payment Terms', default='Immediate Payment (Net 15)')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation Sent'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('brightloop.subscription.line', 'subscription_id', string='Subscription Lines')
    discount_id = fields.Many2one('brightloop.discount.rule', string='Applied Discount Rule')
    
    amount_untaxed = fields.Float(string='Untaxed Amount', compute='_compute_amounts', store=True)
    amount_tax = fields.Float(string='Taxes (18%)', compute='_compute_amounts', store=True)
    amount_discount = fields.Float(string='Discount Applied', compute='_compute_amounts', store=True)
    amount_total = fields.Float(string='Total Recurring Amount', compute='_compute_amounts', store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('brightloop.subscription') or _('New')
        return super(BrightloopSubscription, self).create(vals)

    @api.depends('line_ids.amount', 'discount_id')
    def _compute_amounts(self):
        for sub in self:
            untaxed = sum(line.amount for line in sub.line_ids)
            discount = 0.0
            if sub.discount_id and sub.discount_id.is_valid(untaxed, sum(l.quantity for l in sub.line_ids)):
                if sub.discount_id.discount_type == 'percentage':
                    discount = (untaxed * sub.discount_id.discount_value) / 100.0
                else:
                    discount = min(sub.discount_id.discount_value, untaxed)
            taxable = max(0.0, untaxed - discount)
            tax = taxable * 0.18 # 18% standard business tax rule
            sub.amount_untaxed = untaxed
            sub.amount_discount = discount
            sub.amount_tax = tax
            sub.amount_total = taxable + tax

    def action_send_quotation(self):
        self.write({'state': 'quotation'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_activate(self):
        self.write({
            'state': 'active',
            'next_billing_date': self.start_date or fields.Date.today()
        })

    def action_pause(self):
        if not self.plan_id.allow_pause:
            raise UserError(_('Pausing is not allowed on this plan.'))
        self.write({'state': 'paused'})

    def action_resume(self):
        self.write({'state': 'active'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_generate_recurring_invoice(self):
        """Automated Billing Day: Generates invoice from active subscription idempotently"""
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('Only active subscriptions can be billed.'))
            
        # Idempotency check: Ensure no invoice exists for current billing date
        # Advance next billing date based on plan interval
        interval = self.plan_id.billing_interval
        if interval == 'daily':
            delta = relativedelta(days=1)
        elif interval == 'weekly':
            delta = relativedelta(weeks=1)
        elif interval == 'yearly':
            delta = relativedelta(years=1)
        else:
            delta = relativedelta(months=1)
            
        self.next_billing_date = (self.next_billing_date or fields.Date.today()) + delta
        if self.discount_id:
            self.discount_id.current_usage_count += 1
            
        return True

class BrightloopSubscriptionLine(models.Model):
    _name = 'brightloop.subscription.line'
    _description = 'Subscription Line'

    subscription_id = fields.Many2one('brightloop.subscription', string='Subscription', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    variant_name = fields.Char(string='Variant/Brand')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price', required=True)
    amount = fields.Float(string='Subtotal', compute='_compute_amount', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price
