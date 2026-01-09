# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """Override website sale controller to use cheapest variant price in template_price_vals."""

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Override to use cheapest variant price in template_price_vals."""
        values = super()._prepare_product_values(product, category, search, **kwargs)
        
        # Update template_price_vals with cheapest variant price if it exists
        if 'template_price_vals' in values and product:
            pricelist = values.get('pricelist')
            if not pricelist:
                try:
                    website = request.website
                    pricelist = website.get_current_pricelist()
                except:
                    pricelist = None
            
            # Get the cheapest variant price
            cheapest_price = product._get_cheapest_variant_price(pricelist=pricelist)
            
            # Get base price (original price before discount)
            base_price = product.list_price
            
            # Compute price_reduce (with pricelist if available)
            if pricelist:
                try:
                    # Use template for pricelist calculation, but with cheapest price
                    price_reduce = pricelist._get_product_price(product, 1.0)
                    # If pricelist returns template price, use cheapest variant price instead
                    if price_reduce == base_price:
                        price_reduce = cheapest_price
                except:
                    price_reduce = cheapest_price
            else:
                price_reduce = cheapest_price
            
            # Update template_price_vals
            values['template_price_vals'] = {
                'price_reduce': price_reduce,
                'base_price': base_price,
                'has_discounted_price': base_price > price_reduce,
            }
        
        return values

