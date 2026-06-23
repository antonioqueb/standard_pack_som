# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MassAssignPack(models.TransientModel):
    _name = 'mass.assign.pack.wizard'
    _description = 'Asignación Masiva de Empaque Estándar'

    pack_type_id = fields.Many2one(
        'standard.pack.type',
        string='Tipo de Empaque',
        required=True,
    )
    qty_per_pack = fields.Float(
        string='Cantidad por Empaque',
        required=True,
        digits='Product Unit of Measure',
    )
    is_default = fields.Boolean(
        string='Marcar como Predeterminado',
        default=True,
    )
    product_tmpl_ids = fields.Many2many(
        'product.template',
        string='Productos',
        help='Vacío = aplica a todos los productos seleccionados en la lista.',
    )
    overwrite_existing = fields.Boolean(
        string='Sobrescribir Existentes',
        default=False,
        help='Si se marca, los empaques existentes del mismo tipo se actualizan.',
    )
    preview_count = fields.Integer(
        string='Productos a Actualizar',
        compute='_compute_preview_count',
    )

    @api.depends('product_tmpl_ids')
    def _compute_preview_count(self):
        for wiz in self:
            if wiz.product_tmpl_ids:
                wiz.preview_count = len(wiz.product_tmpl_ids)
            else:
                wiz.preview_count = len(self.env.context.get('active_ids', []))

    def action_assign(self):
        self.ensure_one()
        product_ids = self.product_tmpl_ids or self.env['product.template'].browse(
            self.env.context.get('active_ids', [])
        )

        created = 0
        updated = 0

        for product in product_ids:
            existing = self.env['standard.pack'].search([
                ('product_tmpl_id', '=', product.id),
                ('pack_type_id', '=', self.pack_type_id.id),
                ('qty_per_pack', '=', self.qty_per_pack),
            ], limit=1)

            if existing:
                if self.overwrite_existing:
                    existing.write({'is_default': self.is_default})
                    updated += 1
                continue

            if self.overwrite_existing:
                old_packs = self.env['standard.pack'].search([
                    ('product_tmpl_id', '=', product.id),
                    ('pack_type_id', '=', self.pack_type_id.id),
                ])
                old_packs.unlink()

            if self.is_default:
                product.standard_pack_ids.filtered('is_default').write(
                    {'is_default': False}
                )

            self.env['standard.pack'].create({
                'product_tmpl_id': product.id,
                'pack_type_id': self.pack_type_id.id,
                'qty_per_pack': self.qty_per_pack,
                'is_default': self.is_default,
            })
            created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Asignación de Empaques Completada'),
                'message': _(
                    '%(created)s empaques creados, %(updated)s actualizados.',
                    created=created,
                    updated=updated,
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
