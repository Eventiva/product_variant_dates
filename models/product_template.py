# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


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

    # Override the website_ribbon_id to be computed based on sale period
    website_ribbon_id = fields.Many2one(
        string="Ribbon",
        comodel_name='product.ribbon',
        compute='_compute_website_ribbon_id',
        store=True,
        help='Ribbon displayed on the website based on sale period'
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

            now = fields.Datetime.now()

            # Find the currently active period instead of using the latest end date
            active_variants = []
            for variant in variants:
                if variant.sale_start_date and variant.sale_end_date:
                    # Check if this variant's period is currently active
                    if (variant.sale_start_date <= now <= variant.sale_end_date):
                        active_variants.append(variant)

            if active_variants:
                # Use the currently active period
                start_dates = [v.sale_start_date for v in active_variants if v.sale_start_date]
                end_dates = [v.sale_end_date for v in active_variants if v.sale_end_date]
                template.sale_start_date = min(start_dates) if start_dates else False
                template.sale_end_date = min(end_dates) if end_dates else False  # Use min to get the earliest ending active period
            else:
                # No active period, use the most recent period that has ended
                past_variants = []
                for variant in variants:
                    if variant.sale_start_date and variant.sale_end_date and variant.sale_end_date < now:
                        past_variants.append(variant)

                if past_variants:
                    # Use the most recently ended period
                    start_dates = [v.sale_start_date for v in past_variants if v.sale_start_date]
                    end_dates = [v.sale_end_date for v in past_variants if v.sale_end_date]
                    template.sale_start_date = min(start_dates) if start_dates else False
                    template.sale_end_date = max(end_dates) if end_dates else False
                else:
                    # No periods at all
                    template.sale_start_date = False
                    template.sale_end_date = False

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

    @api.depends('sale_end_date', 'is_sale_period_active')
    def _compute_website_ribbon_id(self):
        """Compute ribbon based on sale period."""
        for template in self:
            if template.sale_end_date and template.is_sale_period_active:
                # Create a unique ribbon name for this product template
                product_ribbon_name = f"{template.sale_period_info}"

                # Create or get a ribbon for the product sale period
                ribbon = template.env['product.ribbon'].search([
                    ('name', '=', product_ribbon_name)
                ], limit=1)

                if not ribbon:
                    # Create a new ribbon for this product sale period
                    ribbon = template.env['product.ribbon'].create({
                        'name': product_ribbon_name,
                        'bg_color': '#17a2b8',  # Blue color for product ribbon
                        'text_color': '#ffffff',
                        'position': 'right'
                    })

                template.website_ribbon_id = ribbon
            else:
                template.website_ribbon_id = False


    def _get_combination_info(self, combination=None, product_id=None, add_qty=1, parent_combination=None, only_template=None, **kwargs):
        """Override to include sale period information in combination info."""
        # Odoo 19 parent method doesn't accept parent_combination, so we don't pass it
        info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            only_template=only_template,
            **kwargs
        )

        if not only_template and product_id:
            variant = self.env['product.product'].browse(product_id)
            # Only include sale period info for active variants
            if variant.active:
                info['is_sale_period_active'] = variant.is_sale_period_active
                info['sale_period_info'] = variant.sale_period_info

        return info

    def _get_active_sale_period_variants(self):
        """Get variants that have active sale periods."""
        self.ensure_one()
        # Get variants with active sale periods
        active_variants = self.product_variant_ids.filtered(
            lambda v: v.is_sale_period_active and v.active
        )
        # If no variants have sale dates set, return all active variants
        if not active_variants:
            variants_with_dates = self.product_variant_ids.filtered(
                lambda v: v.sale_start_date or v.sale_end_date
            )
            # If some variants have dates but none are active, return empty
            # If no variants have dates, return all active variants
            if not variants_with_dates:
                active_variants = self.product_variant_ids.filtered(lambda v: v.active)
        return active_variants

    def _get_cheapest_variant_price(self, pricelist=None):
        """Get the cheapest price from active variants."""
        # Get only active variants (archiving logic handles sale period dates)
        available_variants = self.product_variant_ids.filtered(lambda v: v.active)

        if not available_variants:
            return self.list_price

        # Debug: log available variants
        _logger.debug(f"Template {self.id} ({self.name}): Found {len(available_variants)} active variants")

        # Get pricelist if not provided
        if not pricelist:
            try:
                website = self.env['website'].get_current_website()
                pricelist = self.env.context.get('pricelist') or (website.get_current_pricelist() if website else False)
            except:
                pricelist = False

        # Compute prices for available variants
        prices = []
        for variant in available_variants:
            # Get the price from pricelist or calculate variant price
            if pricelist:
                try:
                    price = pricelist._get_product_price(variant, 1.0)
                    _logger.info(f"Template {self.id}: Variant {variant.id} price from pricelist: {price}")
                except Exception as e:
                    # Fallback: use variant.list_price if set, otherwise calculate
                    if variant.list_price and variant.list_price != self.list_price:
                        price = variant.list_price
                    else:
                        # Calculate: template price + variant extra_price
                        price = self.list_price + variant.price_extra
                    _logger.info(f"Template {self.id}: Variant {variant.id} price (fallback): {price}, list_price={variant.list_price}, price_extra={variant.price_extra}, template.list_price={self.list_price}")
            else:
                # Use variant.list_price if it's different from template (includes extra_price)
                # Otherwise calculate: template price + variant extra_price
                if variant.list_price and variant.list_price != self.list_price:
                    price = variant.list_price
                    _logger.info(f"Template {self.id}: Variant {variant.id} using list_price: {price}")
                else:
                    # Calculate: template price + variant extra_price
                    price = self.list_price + variant.price_extra
                    _logger.info(f"Template {self.id}: Variant {variant.id} calculated price: {price} = {self.list_price} + {variant.price_extra}")

            if price and price > 0:
                prices.append(price)
                _logger.info(f"Template {self.id}: Added variant {variant.id} price {price} to prices list")

        if prices:
            return min(prices)

        return self.list_price

    def _get_website_price_range(self):
        """Override to only consider active variants and return cheapest price."""
        cheapest_price = self._get_cheapest_variant_price()
        _logger.info(f"Template {self.id} ({self.name}): _get_website_price_range returning ({cheapest_price}, {cheapest_price}), template.list_price={self.list_price}")
        # Return only the cheapest price (same for both min and max)
        return (cheapest_price, cheapest_price)
    
    def _get_website_price(self, pricelist=None):
        """Override to return cheapest variant price instead of template price."""
        cheapest_price = self._get_cheapest_variant_price(pricelist=pricelist)
        _logger.info(f"Template {self.id} ({self.name}): _get_website_price returning {cheapest_price}, template.list_price={self.list_price}")
        return cheapest_price
    
    def _get_template_price_vals(self, pricelist=None):
        """Override to return template_price_vals with cheapest variant price."""
        # Get cheapest variant price
        cheapest_price = self._get_cheapest_variant_price(pricelist=pricelist)
        
        # Get pricelist if not provided
        if not pricelist:
            try:
                website = self.env['website'].get_current_website()
                pricelist = self.env.context.get('pricelist') or (website.get_current_pricelist() if website else False)
            except:
                pricelist = False
        
        # Compute base_price (list price) - use cheapest variant's list price or template price
        if pricelist:
            try:
                base_price = pricelist._get_product_price(self, 1.0, uom_id=False)
            except:
                base_price = self.list_price
        else:
            base_price = self.list_price
        
        # Ensure base_price is at least cheapest_price (for discount display)
        if base_price < cheapest_price:
            base_price = cheapest_price
        
        _logger.info(f"Template {self.id} ({self.name}): _get_template_price_vals returning price_reduce={cheapest_price}, base_price={base_price}")
        
        return {
            'price_reduce': cheapest_price,
            'base_price': base_price,
            'has_discounted_price': base_price > cheapest_price,
        }

    @api.depends('list_price', 'product_variant_ids.list_price', 'product_variant_ids.price_extra')
    def _compute_website_price(self):
        """Override to compute website price as cheapest variant price."""
        for template in self:
            cheapest_price = template._get_cheapest_variant_price()
            # Store in a field if needed, or this can be used by other methods
            _logger.info(f"Template {template.id} ({template.name}): _compute_website_price computed {cheapest_price}")

    @api.model
    def _cron_archive_inactive_variants(self):
        """Cron job to archive variants with inactive sale periods and reactivate those with active periods."""
        try:
            # Use the dedicated method in product.product
            result = self.env['product.product']._force_archive_inactive_variants()
            _logger.info(f"Cron job completed: {result['archived']} archived, {result['reactivated']} reactivated")
        except Exception as e:
            _logger.error(f"Error in _cron_archive_inactive_variants: {e}")
