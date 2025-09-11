# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'


    sale_start_date = fields.Datetime(
        string='Sale Start Date',
        compute='_compute_sale_dates_from_attribute_value',
        store=True,
        help='Date from which this attribute value can be sold (inherited from product.attribute.value).'
    )
    sale_end_date = fields.Datetime(
        string='Sale End Date',
        compute='_compute_sale_dates_from_attribute_value',
        store=True,
        help='Date after which this attribute value cannot be sold (inherited from product.attribute.value).'
    )
    is_sale_period_active = fields.Boolean(
        string='Sale Period Active',
        compute='_compute_is_sale_period_active',
        store=True,
        help='True if the current date is within the sale period'
    )
    sale_period_info = fields.Char(
        string='Sale Period Info',
        compute='_compute_sale_period_info',
        help='Human readable information about the sale period'
    )

    @api.depends('product_attribute_value_id.sale_start_date', 'product_attribute_value_id.sale_end_date')
    def _compute_sale_dates_from_attribute_value(self):
        """Compute sale dates from the related product.attribute.value."""
        for ptav in self:
            if ptav.product_attribute_value_id:
                ptav.sale_start_date = ptav.product_attribute_value_id.sale_start_date
                ptav.sale_end_date = ptav.product_attribute_value_id.sale_end_date
            else:
                ptav.sale_start_date = False
                ptav.sale_end_date = False

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_is_sale_period_active(self):
        """Compute whether the attribute value is currently within its sale period."""
        now = fields.Datetime.now()
        for ptav in self:
            if ptav.sale_start_date and ptav.sale_start_date > now:
                ptav.is_sale_period_active = False
            elif ptav.sale_end_date and ptav.sale_end_date < now:
                ptav.is_sale_period_active = False
            else:
                ptav.is_sale_period_active = True

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_sale_period_info(self):
        """Compute human readable sale period information."""
        for ptav in self:
            if ptav.sale_end_date:
                # Format date as "1st Jul" style
                day = ptav.sale_end_date.day
                month = ptav.sale_end_date.strftime('%b')
                if day in (1, 21, 31):
                    suffix = 'st'
                elif day in (2, 22):
                    suffix = 'nd'
                elif day in (3, 23):
                    suffix = 'rd'
                else:
                    suffix = 'th'
                ptav.sale_period_info = _('Until %d%s %s') % (day, suffix, month)
            else:
                ptav.sale_period_info = ''


