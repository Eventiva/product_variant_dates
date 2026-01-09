# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Clean up orphaned product_variant_dates_display_price module record.
    This module was removed during Odoo 19 upgrade but may still exist in database.
    """
    # Delete the orphaned module record if it exists
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

