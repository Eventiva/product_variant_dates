# -*- coding: utf-8 -*-
{
    'name': 'Product Variant Sale Dates',
    'version': '1.3.2',
    'category': 'Sales/Sales',
    'summary': 'Add start and end sale dates to product variants',
    'description': """
Product Variant Sale Dates
==========================

This module allows you to set start and end sale dates for product variants.
Variants are automatically activated/deactivated based on their sale dates,
and ribbons are set based on the sale period.

Features:
---------
* Set start and end sale dates for product variants (via attribute values)
* Automatically activate/deactivate variants based on sale dates
* Set ribbons on variants based on sale period dates
* Cron job to automatically update variant status

Technical Details:
------------------
* Extends product.attribute.value to add sale date fields
* Extends product.product to inherit dates and manage activation/ribbons
* Implements automatic variant archiving/reactivation logic
* Creates ribbons automatically based on sale period information
    """,
    'author': 'Eventiva',
    'website': 'www.eventiva.com',
    'depends': [
        'product',
        'website_sale',
    ],
    'data': [
        'data/cron_data.xml',
        'views/product_views.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
        'tests/test_product_variant_dates.py',
    ],
    'demo': [
        'demo/product_variant_dates_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'Other proprietary',
}
