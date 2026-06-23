# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # === Selección de empaque ===
    standard_pack_id = fields.Many2one(
        'standard.pack',
        string='Empaque',
        domain="[('product_tmpl_id', '=', product_template_id), ('active', '=', True)]",
        help='Empaque estándar con el que se vende este producto.',
    )
    pack_qty = fields.Float(
        string='Pack',
        digits='Product Unit of Measure',
        help='Número de paquetes a vender. La cantidad se calcula como '
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
        related='product_template_id.has_standard_pack',
        readonly=True,
    )

    # =========================================================================
    # CÁLCULO VAIVÉN: Pack ↔ Cantidad
    # =========================================================================

    @api.onchange('standard_pack_id')
    def _onchange_standard_pack_id(self):
        """Al elegir empaque, fija la cantidad a partir del # de paquetes."""
        for line in self:
            pack = line.standard_pack_id
            if pack and pack.qty_per_pack:
                if not line.pack_qty:
                    line.pack_qty = 1.0
                line.product_uom_qty = line.pack_qty * pack.qty_per_pack
                line._standard_pack_set_assignment_mode(pack.qty_per_pack)

    def _standard_pack_set_assignment_mode(self, qty_per_pack):
        """Define el modo de cantidad cuando un material nace/recibe empaque.

        La cantidad 'Solicitado' solo es editable en modo 'Asignar' (por_asignar)
        o 'Mandar a pedir' (auto_transit_assign). Como el empaque hace nacer la
        línea con cantidad por defecto, hay que dejarla en un modo editable:

        - Stock libre >= un paquete  -> 'Asignar'.
        - Stock 0 o menor a un paquete -> 'Mandar a pedir'.

        Se apoya en los campos del flujo de asignación (módulo
        stock_transit_allocation); si no estuvieran presentes, no hace nada.
        """
        self.ensure_one()

        if 'por_asignar' not in self._fields or 'auto_transit_assign' not in self._fields:
            return

        if not qty_per_pack or qty_per_pack <= 0:
            return

        if hasattr(self, '_tc_get_free_internal_qty'):
            stock = self._tc_get_free_internal_qty() or 0.0
        else:
            stock = getattr(self, 'tc_available_internal_qty', 0.0) or 0.0

        if stock >= qty_per_pack:
            # 'Asignar': hay stock suficiente para al menos un paquete. Su propio
            # onchange apaga 'Mandar a pedir' (mutuamente excluyentes).
            if not self.por_asignar:
                self.por_asignar = True
        else:
            # Stock 0 o menor a un paquete -> 'Mandar a pedir'. Su onchange apaga
            # 'Asignar'.
            if not self.auto_transit_assign:
                self.auto_transit_assign = True

    @api.onchange('pack_qty')
    def _onchange_pack_qty(self):
        """Pack → Cantidad."""
        for line in self:
            pack = line.standard_pack_id
            if pack and pack.qty_per_pack:
                line.product_uom_qty = line.pack_qty * pack.qty_per_pack

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_packs(self):
        """Cantidad → Pack (vaivén inverso)."""
        for line in self:
            pack = line.standard_pack_id
            if pack and pack.qty_per_pack:
                line.pack_qty = line.product_uom_qty / pack.qty_per_pack

    @api.onchange('product_id')
    def _onchange_product_id_set_default_pack(self):
        """Al elegir producto con empaque, preselecciona el empaque por defecto."""
        for line in self:
            tmpl = line.product_template_id
            if tmpl and tmpl.has_standard_pack and tmpl.default_pack_id:
                pack = tmpl.default_pack_id
                line.standard_pack_id = pack
                line.pack_qty = 1.0
                line.product_uom_qty = pack.qty_per_pack
                # Nace en modo editable (Asignar / Mandar a pedir) según el stock,
                # para no chocar con la restricción de edición de 'Solicitado'.
                line._standard_pack_set_assignment_mode(pack.qty_per_pack)
            elif not (tmpl and tmpl.has_standard_pack):
                # Producto sin empaque: limpia cualquier selección previa.
                line.standard_pack_id = False
                line.pack_qty = 0.0

    # =========================================================================
    # ENFORCEMENT: venta solo por empaque cuando el producto lo tenga
    # =========================================================================

    def _enforce_pack_compliance(self):
        """Regla dura (sin excepciones): un producto con empaque estándar SOLO
        puede venderse por empaque, en múltiplos exactos. Los productos sin
        empaque se venden libremente."""
        for line in self:
            if line.display_type or not line.product_id:
                continue

            tmpl = line.product_template_id
            if not tmpl or not tmpl.has_standard_pack:
                continue

            rounding = line.product_uom_id.rounding or 0.01
            if float_is_zero(line.product_uom_qty, precision_rounding=rounding):
                continue

            if not line.standard_pack_id:
                raise ValidationError(_(
                    'El producto "%(product)s" solo puede venderse por empaque. '
                    'Selecciona un empaque estándar en la línea.',
                    product=line.product_id.display_name,
                ))

            qty_per_pack = line.standard_pack_id.qty_per_pack
            if qty_per_pack <= 0:
                continue

            packs = line.product_uom_qty / qty_per_pack
            packs_rounded = round(packs)

            # Debe ser un número entero y positivo de paquetes.
            if packs_rounded <= 0 or abs(packs - packs_rounded) > 1e-6:
                nearest = float_round(
                    max(packs_rounded, 1) * qty_per_pack,
                    precision_rounding=rounding,
                )
                raise ValidationError(_(
                    'El producto "%(product)s" solo se vende por empaque completo '
                    '(%(pack)s = %(qpp)s %(uom)s). La cantidad %(qty)s no es un '
                    'múltiplo exacto. Ajusta el número de paquetes (cantidad válida '
                    'más cercana: %(nearest)s).',
                    product=line.product_id.display_name,
                    pack=line.standard_pack_id.display_name,
                    qpp=f"{qty_per_pack:g}",
                    uom=line.product_uom_id.name or '',
                    qty=f"{line.product_uom_qty:g}",
                    nearest=f"{nearest:g}",
                ))
