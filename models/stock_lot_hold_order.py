# -*- coding: utf-8 -*-
import math

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class StockLotHoldOrderLine(models.Model):
    _inherit = 'stock.lot.hold.order.line'

    # Mismas columnas de empaque que la orden de venta, con vaivén
    # Pack ↔ Cantidad sobre cantidad_m2. Aplica a productos genéricos
    # (las placas por lote no se empacan).
    product_tmpl_id = fields.Many2one(
        related='product_id.product_tmpl_id', readonly=True)
    standard_pack_id = fields.Many2one(
        'standard.pack',
        string='Empaque',
        domain="[('product_tmpl_id', '=', product_tmpl_id), ('active', '=', True)]",
        help='Empaque estándar con el que se aparta este producto.',
    )
    pack_qty = fields.Float(
        string='Pack',
        digits='Product Unit of Measure',
        help='Número de paquetes. La cantidad se calcula como '
             'Pack × Cantidad por Empaque.',
    )
    qty_per_pack = fields.Float(
        string='Cant./Empaque',
        related='standard_pack_id.qty_per_pack',
        readonly=True,
    )
    pack_type_name = fields.Char(
        string='Tipo de Empaque',
        related='standard_pack_id.pack_type_id.name',
        readonly=True,
    )
    has_standard_pack = fields.Boolean(
        string='Tiene Empaque',
        related='product_id.product_tmpl_id.has_standard_pack',
        readonly=True,
    )

    @api.onchange('standard_pack_id')
    def _onchange_standard_pack_id_hold(self):
        for line in self:
            pack = line.standard_pack_id
            if pack and pack.qty_per_pack:
                if not line.pack_qty:
                    line.pack_qty = 1.0
                line.cantidad_m2 = line.pack_qty * pack.qty_per_pack

    @api.onchange('pack_qty')
    def _onchange_pack_qty_hold(self):
        for line in self:
            pack = line.standard_pack_id
            if pack and pack.qty_per_pack:
                line.cantidad_m2 = line.pack_qty * pack.qty_per_pack

    @api.onchange('cantidad_m2')
    def _onchange_cantidad_m2_packs(self):
        """Cantidad → Pack con redondeo hacia arriba (mismo vaivén que la
        orden de venta). Solo para líneas SIN lotes (las placas no llevan
        empaque y su cantidad la fijan los lotes)."""
        for line in self:
            if line.lot_ids:
                continue
            pack = line.standard_pack_id
            qpp = pack.qty_per_pack if pack else 0.0
            if not qpp:
                continue
            qty = line.cantidad_m2 or 0.0
            if qty <= 0:
                line.pack_qty = 0
                continue
            packs = qty / qpp
            packs_up = max(1, math.ceil(packs - 1e-6))
            line.pack_qty = packs_up
            if abs(packs - packs_up) > 1e-6:
                line.cantidad_m2 = float_round(packs_up * qpp,
                                               precision_rounding=0.01)

    @api.onchange('product_id')
    def _onchange_product_id_set_default_pack_hold(self):
        for line in self:
            tmpl = line.product_id.product_tmpl_id if line.product_id else False
            if tmpl and tmpl.has_standard_pack and tmpl.default_pack_id \
                    and not line.lot_ids:
                pack = tmpl.default_pack_id
                line.standard_pack_id = pack
                line.pack_qty = 1.0
                line.cantidad_m2 = pack.qty_per_pack
            elif not (tmpl and tmpl.has_standard_pack):
                line.standard_pack_id = False
                line.pack_qty = 0.0

    def _enforce_pack_compliance_hold(self):
        """Misma regla dura que la venta: producto con empaque estándar solo
        se aparta por empaques completos. Placas por lote quedan exentas."""
        for line in self:
            if not line.product_id or line.lot_ids:
                continue
            if line.product_id.type == 'service':
                continue
            tmpl = line.product_id.product_tmpl_id
            if not tmpl or not tmpl.has_standard_pack:
                continue
            if float_is_zero(line.cantidad_m2 or 0.0, precision_rounding=0.01):
                continue
            if not line.standard_pack_id:
                raise ValidationError(_(
                    'El producto "%(product)s" solo puede apartarse por '
                    'empaque. Selecciona un empaque estándar en la línea.',
                    product=line.product_id.display_name,
                ))
            qpp = line.standard_pack_id.qty_per_pack
            if qpp <= 0:
                continue
            packs = (line.cantidad_m2 or 0.0) / qpp
            packs_rounded = round(packs)
            if packs_rounded <= 0 or abs(packs - packs_rounded) > 1e-6:
                nearest = float_round(max(packs_rounded, 1) * qpp,
                                      precision_rounding=0.01)
                raise ValidationError(_(
                    'El producto "%(product)s" solo se aparta por empaque '
                    'completo (%(pack)s = %(qpp)s). La cantidad %(qty)s no '
                    'es múltiplo exacto (válida más cercana: %(nearest)s).',
                    product=line.product_id.display_name,
                    pack=line.standard_pack_id.display_name,
                    qpp=f"{qpp:g}",
                    qty=f"{(line.cantidad_m2 or 0.0):g}",
                    nearest=f"{nearest:g}",
                ))


class StockLotHoldOrder(models.Model):
    _inherit = 'stock.lot.hold.order'

    def action_confirm(self):
        self.mapped('hold_line_ids')._enforce_pack_compliance_hold()
        return super().action_confirm()
