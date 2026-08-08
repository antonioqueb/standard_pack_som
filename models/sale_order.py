# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_pack_lines = fields.Boolean(
        string='Tiene líneas con empaque',
        compute='_compute_has_pack_lines',
        help='True si alguna línea vende un producto con empaque estándar. '
             'Gobierna la visibilidad de la columna Pack en las líneas: una '
             'orden de puras placas no muestra la columna.',
    )

    @api.depends('order_line.has_standard_pack')
    def _compute_has_pack_lines(self):
        for order in self:
            order.has_pack_lines = any(
                order.order_line.mapped('has_standard_pack'))

    def action_confirm(self):
        """Valida la regla de empaque estándar antes de confirmar."""
        for order in self:
            order.order_line._enforce_pack_compliance()
        return super().action_confirm()
