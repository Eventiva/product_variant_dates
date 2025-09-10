# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_possible_variants_sorted(self):
        """Override to filter out variants that are not within their sale period."""
        variants = super()._get_possible_variants_sorted()
        # Filter out variants that are not within their sale period
        return variants.filtered(lambda v: v.is_sale_period_active)

    def _get_combination_info(self, combination=None, product_id=None, add_qty=1, pricelist=None, parent_combination=None, only_template=False):
        """Override to include sale period information in combination info."""
        info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template
        )

        if not only_template and product_id:
            variant = self.env['product.product'].browse(product_id)
            info['is_sale_period_active'] = variant.is_sale_period_active
            info['sale_period_info'] = variant.sale_period_info

        return info
