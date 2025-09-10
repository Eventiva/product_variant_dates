# -*- coding: utf-8 -*-
{
    'name': 'Product Variant Sale Dates',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Add start and end sale dates to product variants',
    'description': """
Product Variant Sale Dates
==========================

This module allows you to set start and end sale dates for product variants.
After the end date passes, the variant will be hidden from the website and
cannot be purchased anymore.

Features:
---------
* Set start and end sale dates for product variants
* Display sale dates on product pages
* Automatically hide variants after end date
* Prevent purchase of expired variants
* Show sale period information to customers

Technical Details:
------------------
* Extends product.product model to add sale date fields
* Updates product views to show sale dates
* Modifies website templates to display sale information
* Implements automatic variant hiding logic
* Maintains compatibility with existing e-commerce functionality
    """,
    'author': 'Eventiva',
    'website': 'www.eventiva.com',
    'depends': [
        'product',
        'website_sale',
    ],
    'data': [
        'views/product_views.xml',
        'views/website_sale_templates.xml',
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
    'license': 'Other OSI approved license',
}
