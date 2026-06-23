# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Valida la regla de empaque estándar antes de confirmar."""
        for order in self:
            order.order_line._enforce_pack_compliance()
        return super().action_confirm()
