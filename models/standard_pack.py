# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StandardPack(models.Model):
    _name = 'standard.pack'
    _description = 'Definición de Empaque Estándar'
    _order = 'product_tmpl_id, sequence'
    _rec_name = 'display_name'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    pack_type_id = fields.Many2one(
        'standard.pack.type',
        string='Tipo de Empaque',
        required=True,
        ondelete='restrict',
    )
    qty_per_pack = fields.Float(
        string='Cantidad por Empaque',
        required=True,
        digits='Product Unit of Measure',
        help='Número de unidades/piezas/m² por empaque estándar.',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        related='product_tmpl_id.uom_id',
        store=True,
        readonly=True,
    )
    is_default = fields.Boolean(
        string='Empaque por Defecto',
        default=False,
        help='Si se marca, este empaque se preselecciona en las líneas de venta.',
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )

    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('pack_type_id.name', 'qty_per_pack', 'product_tmpl_id.name', 'uom_id.name')
    def _compute_display_name(self):
        for rec in self:
            if rec.pack_type_id and rec.qty_per_pack:
                rec.display_name = f"{rec.pack_type_id.name} x {rec.qty_per_pack:g} {rec.uom_id.name or ''}"
            else:
                rec.display_name = 'Nuevo'

    _sql_constraints = [
        ('qty_positive', 'CHECK(qty_per_pack > 0)',
         'La cantidad por empaque debe ser mayor a cero.'),
        ('product_type_qty_uniq',
         'unique(product_tmpl_id, pack_type_id, qty_per_pack, company_id)',
         'Ya existe un empaque estándar con el mismo tipo y cantidad para este producto.'),
    ]
