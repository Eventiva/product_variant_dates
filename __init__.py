# -*- coding: utf-8 -*-

from . import models


def post_init_hook(cr, registry):
    """
    Clean up orphaned product_variant_dates_display_price module record.
    This module was removed during Odoo 19 upgrade but may still exist in database.
    """
    cr.execute("""
        DELETE FROM ir_module_module
        WHERE name = 'product_variant_dates_display_price'
    """)

    # Also remove any module dependencies referencing it
    cr.execute("""
        DELETE FROM ir_module_module_dependency
        WHERE name = 'product_variant_dates_display_price'
    """)

    # Remove any external IDs that might reference it
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'product_variant_dates_display_price'
    """)
