# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Computed fields that inherit from attribute values
    sale_start_date = fields.Datetime(
        string='Sale Start Date',
        compute='_compute_sale_dates_from_attributes',
        store=True,
        help='Date from which this variant can be sold (inherited from attribute values).'
    )
    sale_end_date = fields.Datetime(
        string='Sale End Date',
        compute='_compute_sale_dates_from_attributes',
        store=True,
        help='Date after which this variant cannot be sold (inherited from attribute values).'
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

    @api.depends('product_template_attribute_value_ids.product_attribute_value_id.sale_start_date', 'product_template_attribute_value_ids.product_attribute_value_id.sale_end_date')
    def _compute_sale_dates_from_attributes(self):
        """Compute sale dates from the most restrictive attribute value dates."""
        for variant in self:
            # Get all attribute values for this variant
            attr_values = variant.product_template_attribute_value_ids

            if not attr_values:
                variant.sale_start_date = False
                variant.sale_end_date = False
                continue

            # Get dates from the underlying product.attribute.value records
            start_dates = []
            end_dates = []

            for ptav in attr_values:
                if ptav.product_attribute_value_id:
                    if ptav.product_attribute_value_id.sale_start_date:
                        start_dates.append(ptav.product_attribute_value_id.sale_start_date)
                    if ptav.product_attribute_value_id.sale_end_date:
                        end_dates.append(ptav.product_attribute_value_id.sale_end_date)

            # Use the latest start date (most restrictive)
            variant.sale_start_date = max(start_dates) if start_dates else False

            # Use the earliest end date (most restrictive)
            variant.sale_end_date = min(end_dates) if end_dates else False

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_is_sale_period_active(self):
        """Compute whether the variant is currently within its sale period."""
        now = fields.Datetime.now()
        for variant in self:
            if variant.sale_start_date and variant.sale_start_date > now:
                variant.is_sale_period_active = False
            elif variant.sale_end_date and variant.sale_end_date < now:
                variant.is_sale_period_active = False
            else:
                variant.is_sale_period_active = True

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_sale_period_info(self):
        """Compute human readable sale period information."""
        for variant in self:
            info_parts = []
            if variant.sale_start_date:
                info_parts.append(_('Available from %s') % variant.sale_start_date.strftime('%Y-%m-%d'))
            if variant.sale_end_date:
                info_parts.append(_('Until %s') % variant.sale_end_date.strftime('%Y-%m-%d'))
            variant.sale_period_info = ' | '.join(info_parts) if info_parts else ''

    def _is_add_to_cart_possible(self):
        """Override to check if variant is within sale period."""
        res = super()._is_add_to_cart_possible()
        if not res:
            return res

        # Check if variant is within sale period
        if not self.is_sale_period_active:
            return False

        return True

    def _get_combination_info_variant(self):
        """Override to include sale period information."""
        info = super()._get_combination_info_variant()
        info['is_sale_period_active'] = self.is_sale_period_active
        info['sale_period_info'] = self.sale_period_info
        return info
