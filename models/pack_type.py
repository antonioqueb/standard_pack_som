# -*- coding: utf-8 -*-
from odoo import models, fields


class PackType(models.Model):
    _name = 'standard.pack.type'
    _description = 'Tipo de Empaque'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Descripción', translate=True)
    icon = fields.Char(
        string='Icono',
        help='Clase CSS del icono (p. ej. fa-cubes, fa-archive)',
        default='fa-cube',
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del tipo de empaque debe ser único.'),
    ]
