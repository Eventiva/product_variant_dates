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

        # Create attribute values with sale dates
        self.early_adopter_value = self.env['product.attribute.value'].create({
            'name': 'Early Adopter',
            'attribute_id': self.release_attribute.id,
            'default_extra_price': -20.00,
            'sale_start_date': datetime.now() - timedelta(days=30),
            'sale_end_date': datetime.now() + timedelta(days=30),
        })

        self.standard_value = self.env['product.attribute.value'].create({
            'name': 'Standard',
            'attribute_id': self.release_attribute.id,
            'default_extra_price': -10.00,
            'sale_start_date': datetime.now() + timedelta(days=7),
            'sale_end_date': datetime.now() + timedelta(days=60),
        })

        # Create attribute line
        self.attribute_line = self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_template.id,
            'attribute_id': self.release_attribute.id,
            'value_ids': [(6, 0, [self.early_adopter_value.id, self.standard_value.id])],
        })

        # Get the variants
        self.early_adopter_variant = self.product_template.product_variant_ids.filtered(
            lambda v: self.early_adopter_value in v.product_template_attribute_value_ids
        )
        self.standard_variant = self.product_template.product_variant_ids.filtered(
            lambda v: self.standard_value in v.product_template_attribute_value_ids
        )

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
        self.assertIn('Available from', self.early_adopter_variant.sale_period_info)
        self.assertIn('Until', self.early_adopter_variant.sale_period_info)

        self.assertIn('Available from', self.standard_variant.sale_period_info)
        self.assertIn('Until', self.standard_variant.sale_period_info)

    def test_add_to_cart_possible(self):
        """Test that add to cart is not possible for expired variants."""
        self.assertTrue(self.early_adopter_variant._is_add_to_cart_possible())
        self.assertFalse(self.standard_variant._is_add_to_cart_possible())

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

        small_value = self.env['product.attribute.value'].create({
            'name': 'Small',
            'attribute_id': size_attribute.id,
            'sale_start_date': datetime.now() - timedelta(days=10),
            'sale_end_date': datetime.now() + timedelta(days=10),
        })

        # Add size attribute to the product
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_template.id,
            'attribute_id': size_attribute.id,
            'value_ids': [(6, 0, [small_value.id])],
        })

        # Find the variant with both early adopter and small
        combined_variant = self.product_template.product_variant_ids.filtered(
            lambda v: (self.early_adopter_value in v.product_template_attribute_value_ids and
                      small_value in v.product_template_attribute_value_ids)
        )

        # Should use the most restrictive dates (latest start, earliest end)
        expected_start = max(self.early_adopter_value.sale_start_date, small_value.sale_start_date)
        expected_end = min(self.early_adopter_value.sale_end_date, small_value.sale_end_date)

        self.assertEqual(combined_variant.sale_start_date, expected_start)
        self.assertEqual(combined_variant.sale_end_date, expected_end)

    def test_attribute_value_sale_dates_validation(self):
        """Test that attribute value sale dates validation works."""
        with self.assertRaises(Exception):  # ValidationError
            self.env['product.attribute.value'].create({
                'name': 'Invalid',
                'attribute_id': self.release_attribute.id,
                'sale_start_date': datetime.now() + timedelta(days=2),
                'sale_end_date': datetime.now() + timedelta(days=1),
            })
