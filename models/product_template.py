# -*- coding: utf-8 -*-

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _cron_archive_inactive_variants(self):
        """Cron job to archive variants with inactive sale periods and reactivate those with active periods."""
        try:
            # Use the dedicated method in product.product
            result = self.env['product.product']._force_archive_inactive_variants()
            _logger.info(f"Cron job completed: {result['archived']} archived, {result['reactivated']} reactivated")
        except Exception as e:
            _logger.error(f"Error in _cron_archive_inactive_variants: {e}")
