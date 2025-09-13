# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


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

    # Override the variant_ribbon_id to be editable but with default based on sale period
    variant_ribbon_id = fields.Many2one(
        string="Variant Ribbon",
        comodel_name='product.ribbon',
        help='Ribbon displayed on the website. Leave empty for automatic sale period ribbon.'
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
            # Store previous state for comparison
            was_sale_period_active = variant.is_sale_period_active

            if variant.sale_start_date and variant.sale_start_date > now:
                variant.is_sale_period_active = False
            elif variant.sale_end_date and variant.sale_end_date < now:
                variant.is_sale_period_active = False
            else:
                variant.is_sale_period_active = True

            # Trigger archiving if sale period status changed and we're not already in archiving context
            if (was_sale_period_active != variant.is_sale_period_active and
                not self.env.context.get('skip_archiving') and
                variant.id):  # Only for existing variants, not during creation
                variant._update_variant_archiving()

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

    def _get_default_variant_ribbon(self):
        """Get or create a default ribbon based on variant sale period."""
        if self.sale_end_date:
            # Create a unique ribbon name for this variant
            variant_ribbon_name = f"Variant: {self.sale_period_info}"

            # Create or get a ribbon for the variant sale period
            ribbon = self.env['product.ribbon'].search([
                ('name', '=', variant_ribbon_name)
            ], limit=1)

            if not ribbon:
                # Create a new ribbon for this variant sale period
                ribbon = self.env['product.ribbon'].create({
                    'name': variant_ribbon_name,
                    'bg_color': '#28a745',  # Green color to distinguish from product ribbon
                    'text_color': '#ffffff',
                    'position': 'right'
                })

            return ribbon
        return False

    @api.model
    def create(self, vals):
        """Override create to set default ribbon."""
        variant = super().create(vals)
        if not variant.variant_ribbon_id:
            variant.variant_ribbon_id = variant._get_default_variant_ribbon()
        return variant

    def write(self, vals):
        """Override write to update ribbon when sale dates change."""
        result = super().write(vals)
        # Update ribbon if sale dates changed and no manual ribbon is set
        if not self.variant_ribbon_id and self.sale_end_date:
            self.variant_ribbon_id = self._get_default_variant_ribbon()
        return result

    def update_variant_ribbons(self):
        """Manually update variant ribbons for existing variants."""
        for variant in self:
            if variant.sale_end_date:
                variant.variant_ribbon_id = variant._get_default_variant_ribbon()
            else:
                variant.variant_ribbon_id = False


    def _update_variant_archiving(self):
        """Update variant archiving based on sale period status."""
        try:
            if not self.is_sale_period_active and self.active:
                # Archive variant if sale period is inactive
                self.with_context(skip_archiving=True).write({'active': False})
                _logger.info(f"Archived variant {self.id} (sale period inactive)")
            elif self.is_sale_period_active and not self.active:
                # Reactivate variant if sale period is active
                self.with_context(skip_archiving=True).write({'active': True})
                _logger.info(f"Reactivated variant {self.id} (sale period active)")
        except Exception as e:
            _logger.warning(f"Error updating variant {self.id} archiving: {e}")

    def _get_combination_info_variant(self):
        """Override to include sale period information."""
        info = super()._get_combination_info_variant()
        # Only include sale period info for active variants
        if self.active:
            info['is_sale_period_active'] = self.is_sale_period_active
            info['sale_period_info'] = self.sale_period_info
        return info

    @api.model
    def _force_archive_inactive_variants(self):
        """Force archiving of variants with inactive sale periods."""
        _logger.info("Forcing archive of inactive variants...")

        # Find all variants that need to be checked
        variants = self.env['product.product'].search([
            ('product_tmpl_id', '!=', False),
        ])

        archived_count = 0
        reactivated_count = 0

        for variant in variants:
            try:
                # Force recomputation of sale period active with skip_archiving context
                variant.with_context(skip_archiving=True)._compute_is_sale_period_active()

                # Check if variant should be archived/reactivated
                if not variant.is_sale_period_active and variant.active:
                    variant.with_context(skip_archiving=True).write({'active': False})
                    archived_count += 1
                    _logger.info(f"Archived variant {variant.id} - {variant.display_name}")
                elif variant.is_sale_period_active and not variant.active:
                    variant.with_context(skip_archiving=True).write({'active': True})
                    reactivated_count += 1
                    _logger.info(f"Reactivated variant {variant.id} - {variant.display_name}")

            except Exception as e:
                _logger.warning(f"Error processing variant {variant.id}: {e}")
                continue

        _logger.info(f"Archive complete: {archived_count} archived, {reactivated_count} reactivated")
        return {
            'archived': archived_count,
            'reactivated': reactivated_count
        }
