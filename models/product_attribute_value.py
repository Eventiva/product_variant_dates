# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    sale_start_date = fields.Datetime(
        string='Sale Start Date',
        help='Date from which this attribute value can be sold. Leave empty for no restriction.'
    )
    sale_end_date = fields.Datetime(
        string='Sale End Date',
        help='Date after which this attribute value cannot be sold. Leave empty for no restriction.'
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

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_is_sale_period_active(self):
        """Compute whether the attribute value is currently within its sale period."""
        now = fields.Datetime.now()
        for attr_value in self:
            if attr_value.sale_start_date and attr_value.sale_start_date > now:
                attr_value.is_sale_period_active = False
            elif attr_value.sale_end_date and attr_value.sale_end_date < now:
                attr_value.is_sale_period_active = False
            else:
                attr_value.is_sale_period_active = True

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_sale_period_info(self):
        """Compute human readable sale period information."""
        for attr_value in self:
            info_parts = []
            if attr_value.sale_start_date:
                info_parts.append(_('Available from %s') % attr_value.sale_start_date.strftime('%Y-%m-%d'))
            if attr_value.sale_end_date:
                info_parts.append(_('Until %s') % attr_value.sale_end_date.strftime('%Y-%m-%d'))
            attr_value.sale_period_info = ' | '.join(info_parts) if info_parts else ''

    @api.constrains('sale_start_date', 'sale_end_date')
    def _check_sale_dates(self):
        """Validate that start date is before end date."""
        for attr_value in self:
            if attr_value.sale_start_date and attr_value.sale_end_date:
                if attr_value.sale_start_date >= attr_value.sale_end_date:
                    raise ValidationError(_('Sale start date must be before sale end date for attribute value %s.') % attr_value.display_name)
