# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    standard_pack_ids = fields.One2many(
        'standard.pack',
        'product_tmpl_id',
        string='Empaques Estándar',
    )
    standard_pack_count = fields.Integer(
        string='Empaques',
        compute='_compute_standard_pack_count',
    )
    has_standard_pack = fields.Boolean(
        string='Tiene Empaque Estándar',
        compute='_compute_has_standard_pack',
        store=True,
        help='Indica si el producto tiene al menos un empaque estándar definido.',
    )
    default_pack_id = fields.Many2one(
        'standard.pack',
        string='Empaque por Defecto',
        compute='_compute_default_pack',
        store=True,
    )

    # Métodos de cómputo separados a propósito: 'has_standard_pack' es ALMACENADO
    # (store=True => compute_sudo=True por defecto) y 'standard_pack_count' NO lo
    # es. Odoo 19 advierte si un mismo método calcula campos con distinto 'store'
    # o 'compute_sudo', por eso cada uno tiene su propio método.
    @api.depends('standard_pack_ids', 'standard_pack_ids.active')
    def _compute_standard_pack_count(self):
        for product in self:
            product.standard_pack_count = len(product.standard_pack_ids.filtered('active'))

    @api.depends('standard_pack_ids', 'standard_pack_ids.active')
    def _compute_has_standard_pack(self):
        for product in self:
            product.has_standard_pack = bool(product.standard_pack_ids.filtered('active'))

    def _som_standard_packs_for_company(self, company=None):
        """Empaques activos que aplican a la compañía dada: compartidos
        (sin compañía) o de esa compañía. sudo: has_standard_pack es
        almacenado con sudo, así que la regla de negocio debe ver los mismos
        empaques que ese flag, no solo los visibles por ir.rule."""
        self.ensure_one()
        packs = self.sudo().standard_pack_ids.filtered('active')
        if company:
            packs = packs.filtered(
                lambda p: not p.company_id or p.company_id == company)
        return packs

    @api.depends('standard_pack_ids.is_default', 'standard_pack_ids.active')
    def _compute_default_pack(self):
        for product in self:
            default = product.standard_pack_ids.filtered(
                lambda p: p.is_default and p.active
            )
            product.default_pack_id = default[:1] if default else False
