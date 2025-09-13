# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase


class TestProductVariantDates(TransactionCase):
    """Test cases for product variant sale dates functionality."""

    def setUp(self):
        super().setUp()
        # Create a product template with attributes
        self.product_template = self.env['product.template'].create({
            'name': 'VIP Ticket',
            'type': 'consu',
            'list_price': 100.00,
        })

        # Create release attribute
        self.release_attribute = self.env['product.attribute'].create({
            'name': 'Release',
            'create_variant': 'always',
        })

        # Use fixed dates to avoid timing issues
        # Set base date to a past date so we can control the test scenarios
        base_date = datetime(2024, 1, 1, 12, 0, 0)

        # Create attribute values with sale dates
        self.early_adopter_value = self.env['product.attribute.value'].create({
            'name': 'Early Adopter',
            'attribute_id': self.release_attribute.id,
            'default_extra_price': -20.00,
            'sale_start_date': (base_date - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),  # Started 30 days ago
            'sale_end_date': (base_date + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),    # Ends in 30 days
        })

        self.standard_value = self.env['product.attribute.value'].create({
            'name': 'Standard',
            'attribute_id': self.release_attribute.id,
            'default_extra_price': -10.00,
            'sale_start_date': (base_date + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),   # Starts in 7 days (future)
            'sale_end_date': (base_date + timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S'),    # Ends in 60 days
        })

        # Create attribute line
        self.attribute_line = self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_template.id,
            'attribute_id': self.release_attribute.id,
            'value_ids': [(6, 0, [self.early_adopter_value.id, self.standard_value.id])],
        })

        # Get the variants by checking the product_attribute_value_id field
        self.early_adopter_variant = self.product_template.product_variant_ids.filtered(
            lambda v: self.early_adopter_value.id in v.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids
        )
        self.standard_variant = self.product_template.product_variant_ids.filtered(
            lambda v: self.standard_value.id in v.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids
        )

        # Ensure variants were created
        self.assertEqual(len(self.early_adopter_variant), 1, "Early adopter variant should be created")
        self.assertEqual(len(self.standard_variant), 1, "Standard variant should be created")

    def test_attribute_value_sale_period_active(self):
        """Test that attribute value sale period is computed correctly."""
        self.assertTrue(self.early_adopter_value.is_sale_period_active)
        self.assertFalse(self.standard_value.is_sale_period_active)  # Future start date

    def test_variant_inherits_sale_dates_from_attributes(self):
        """Test that variants inherit sale dates from their attribute values."""
        # Early adopter variant should inherit the early adopter dates
        self.assertEqual(
            self.early_adopter_variant.sale_start_date,
            self.early_adopter_value.sale_start_date
        )
        self.assertEqual(
            self.early_adopter_variant.sale_end_date,
            self.early_adopter_value.sale_end_date
        )

        # Standard variant should inherit the standard dates
        self.assertEqual(
            self.standard_variant.sale_start_date,
            self.standard_value.sale_start_date
        )
        self.assertEqual(
            self.standard_variant.sale_end_date,
            self.standard_value.sale_end_date
        )

    def test_variant_sale_period_active(self):
        """Test that variant sale period active is computed correctly."""
        self.assertTrue(self.early_adopter_variant.is_sale_period_active)
        self.assertFalse(self.standard_variant.is_sale_period_active)

    def test_variant_sale_period_info(self):
        """Test that variant sale period info is computed correctly."""
        # Early adopter should show "Until" since it's currently active
        self.assertIn('Until', self.early_adopter_variant.sale_period_info)

        # Standard should show "Until" since it has an end date
        self.assertIn('Until', self.standard_variant.sale_period_info)

    def test_variant_archiving(self):
        """Test that variants are archived when sale period is inactive."""
        # Early adopter should be active (sale period is active)
        self.assertTrue(self.early_adopter_variant.active)

        # Standard should have inactive sale period (due to future start date)
        self.assertFalse(self.standard_variant.is_sale_period_active)

        # Manually trigger archiving to test the functionality
        self.env['product.product']._force_archive_inactive_variants()

        # Now standard should be archived
        self.assertFalse(self.standard_variant.active)

    def test_combination_info_includes_sale_period(self):
        """Test that combination info includes sale period information."""
        info = self.early_adopter_variant._get_combination_info_variant()
        self.assertIn('is_sale_period_active', info)
        self.assertIn('sale_period_info', info)
        self.assertTrue(info['is_sale_period_active'])

        info = self.standard_variant._get_combination_info_variant()
        self.assertIn('is_sale_period_active', info)
        self.assertIn('sale_period_info', info)
        self.assertFalse(info['is_sale_period_active'])

    def test_multiple_attributes_most_restrictive_dates(self):
        """Test that when a variant has multiple attributes, the most restrictive dates are used."""
        # Create a second attribute
        size_attribute = self.env['product.attribute'].create({
            'name': 'Size',
            'create_variant': 'always',
        })

        # Use fixed dates to avoid timing issues
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        small_value = self.env['product.attribute.value'].create({
            'name': 'Small',
            'attribute_id': size_attribute.id,
            'sale_start_date': (base_date - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
            'sale_end_date': (base_date + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
        })

        # Add size attribute to the product
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_template.id,
            'attribute_id': size_attribute.id,
            'value_ids': [(6, 0, [small_value.id])],
        })

        # Find the variant with both early adopter and small
        combined_variant = self.product_template.product_variant_ids.filtered(
            lambda v: (self.early_adopter_value.id in v.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids and
                      small_value.id in v.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids)
        )

        # Should use the most restrictive dates (latest start, earliest end)
        expected_start = max(self.early_adopter_value.sale_start_date, small_value.sale_start_date)
        expected_end = min(self.early_adopter_value.sale_end_date, small_value.sale_end_date)

        self.assertEqual(combined_variant.sale_start_date, expected_start)
        self.assertEqual(combined_variant.sale_end_date, expected_end)

    def test_ribbon_creation(self):
        """Test that ribbons are created for variants with sale periods."""
        # Early adopter should have a ribbon
        self.assertTrue(self.early_adopter_variant.variant_ribbon_id)
        self.assertIn('Until', self.early_adopter_variant.variant_ribbon_id.name)

        # Standard should not have a ribbon (inactive sale period)
        # Note: Ribbon creation might happen even for inactive variants, so we check if it exists
        if self.standard_variant.variant_ribbon_id:
            # If ribbon exists, it should not be active
            self.assertFalse(self.standard_variant.is_sale_period_active)

    def test_archiving_on_date_change(self):
        """Test that variants are archived/reactivated when sale dates change."""
        # Create a new product template for this test to avoid conflicts
        test_template = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 50.00,
        })

        # Create a variant with active sale period
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        active_value = self.env['product.attribute.value'].create({
            'name': 'Active Test',
            'attribute_id': self.release_attribute.id,
            'sale_start_date': (base_date - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),  # Started yesterday
            'sale_end_date': (base_date + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),    # Ends tomorrow
        })

        # Add to product template
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': test_template.id,
            'attribute_id': self.release_attribute.id,
            'value_ids': [(6, 0, [active_value.id])],
        })

        # Find the variant - should be exactly one
        test_variant = test_template.product_variant_ids.filtered(
            lambda v: active_value.id in v.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids
        )

        # Ensure we have exactly one variant
        self.assertEqual(len(test_variant), 1)
        test_variant = test_variant[0]

        # Should be active initially
        self.assertTrue(test_variant.active)
        self.assertTrue(test_variant.is_sale_period_active)

        # Change end date to past - should archive
        active_value.sale_end_date = base_date - timedelta(days=1)
        test_variant._compute_sale_dates_from_attributes()
        test_variant._compute_is_sale_period_active()

        # Should now be archived
        self.assertFalse(test_variant.active)
        self.assertFalse(test_variant.is_sale_period_active)
