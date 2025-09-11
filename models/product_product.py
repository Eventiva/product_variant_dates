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
        """Compute sale dates from attribute value dates."""
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

            # Use the earliest start date and latest end date (least restrictive for variant)
            variant.sale_start_date = min(start_dates) if start_dates else False
            variant.sale_end_date = max(end_dates) if end_dates else False

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_is_sale_period_active(self):
        """Compute whether the variant is currently within its sale period."""
        now = fields.Datetime.now()
        for variant in self:
            was_active = variant.is_sale_period_active
            if variant.sale_start_date and variant.sale_start_date > now:
                variant.is_sale_period_active = False
            elif variant.sale_end_date and variant.sale_end_date < now:
                variant.is_sale_period_active = False
            else:
                variant.is_sale_period_active = True

            # Archive or reactivate variant based on sale period change
            if was_active != variant.is_sale_period_active:
                if not variant.is_sale_period_active and variant.active:
                    # Archive variant if sale period became inactive
                    variant.write({'active': False})
                elif variant.is_sale_period_active and not variant.active:
                    # Reactivate variant if sale period became active
                    variant.write({'active': True})

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_sale_period_info(self):
        """Compute human readable sale period information."""
        for variant in self:
            if variant.sale_end_date:
                # Format date as "1st Jul" style
                day = variant.sale_end_date.day
                month = variant.sale_end_date.strftime('%b')
                if day in (1, 21, 31):
                    suffix = 'st'
                elif day in (2, 22):
                    suffix = 'nd'
                elif day in (3, 23):
                    suffix = 'rd'
                else:
                    suffix = 'th'
                variant.sale_period_info = _('Until %d%s %s') % (day, suffix, month)
            else:
                variant.sale_period_info = ''


    def _get_combination_info_variant(self):
        """Override to include sale period information."""
        info = super()._get_combination_info_variant()
        # Only include sale period info for active variants
        if self.active:
            info['is_sale_period_active'] = self.is_sale_period_active
            info['sale_period_info'] = self.sale_period_info
        return info
