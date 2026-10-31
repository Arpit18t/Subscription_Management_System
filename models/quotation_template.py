# -*- coding: utf-8 -*-
from odoo import models, fields, api

class QuotationTemplate(models.Model):
    _name = 'brightloop.quotation.template'
    _description = 'Subscription Quotation Template'

    name = fields.Char(string='Template Name', required=True)
    plan_id = fields.Many2one('brightloop.subscription.plan', string='Default Plan', required=True)
    validity_days = fields.Integer(string='Quotation Validity (Days)', default=30)
    line_ids = fields.One2many('brightloop.quotation.template.line', 'template_id', string='Products')

class QuotationTemplateLine(models.Model):
    _name = 'brightloop.quotation.template.line'
    _description = 'Quotation Template Line'

    template_id = fields.Many2one('brightloop.quotation.template', string='Template', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
