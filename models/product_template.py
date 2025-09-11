# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Computed fields that inherit from variant attribute values
    sale_start_date = fields.Datetime(
        string='Sale Start Date',
        compute='_compute_sale_dates_from_variants',
        store=True,
        help='Date from which this template can be sold (inherited from variant attribute values).'
    )
    sale_end_date = fields.Datetime(
        string='Sale End Date',
        compute='_compute_sale_dates_from_variants',
        store=True,
        help='Date after which this template cannot be sold (inherited from variant attribute values).'
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

    @api.depends('product_variant_ids.sale_start_date', 'product_variant_ids.sale_end_date')
    def _compute_sale_dates_from_variants(self):
        """Compute sale dates from variant attribute values."""
        for template in self:
            # Get all variants with sale dates, not just active ones
            variants = template.product_variant_ids

            if not variants:
                template.sale_start_date = False
                template.sale_end_date = False
                continue

            # Get dates from all variants (including inactive ones)
            start_dates = [v.sale_start_date for v in variants if v.sale_start_date]
            end_dates = [v.sale_end_date for v in variants if v.sale_end_date]

            # Use the earliest start date and latest end date from ALL variants
            template.sale_start_date = min(start_dates) if start_dates else False
            template.sale_end_date = max(end_dates) if end_dates else False

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_is_sale_period_active(self):
        """Compute whether the template is currently within its sale period."""
        now = fields.Datetime.now()
        for template in self:
            if template.sale_start_date and template.sale_start_date > now:
                template.is_sale_period_active = False
            elif template.sale_end_date and template.sale_end_date < now:
                template.is_sale_period_active = False
            else:
                template.is_sale_period_active = True

            # Unpublish product if sale period is not active
            if not template.is_sale_period_active and template.website_published:
                template.website_published = False

    @api.depends('sale_start_date', 'sale_end_date')
    def _compute_sale_period_info(self):
        """Compute human readable sale period information."""
        for template in self:
            if template.sale_end_date:
                # Format date as "1st Jul" style
                day = template.sale_end_date.day
                month = template.sale_end_date.strftime('%b')
                if day in (1, 21, 31):
                    suffix = 'st'
                elif day in (2, 22):
                    suffix = 'nd'
                elif day in (3, 23):
                    suffix = 'rd'
                else:
                    suffix = 'th'
                template.sale_period_info = _('Until %d%s %s') % (day, suffix, month)
            else:
                template.sale_period_info = ''

    def _get_possible_variants_sorted(self):
        """Override to filter out variants that are not within their sale period."""
        variants = super()._get_possible_variants_sorted()
        # Filter out variants that are not within their sale period
        return variants.filtered(lambda v: v.is_sale_period_active)

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1.0, parent_combination=False, only_template=False):
        """Override to include sale period information in combination info."""
        info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            parent_combination=parent_combination,
            only_template=only_template
        )

        if not only_template and product_id:
            variant = self.env['product.product'].browse(product_id)
            info['is_sale_period_active'] = variant.is_sale_period_active
            info['sale_period_info'] = variant.sale_period_info

        return info
