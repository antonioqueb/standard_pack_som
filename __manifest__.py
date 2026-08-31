# -*- coding: utf-8 -*-
{
    'name': 'StandardPack',
    'version': '19.0.3.3.1',
    'category': 'Sales',
    'summary': 'Venta por empaque estándar con cálculo vaivén paquetes ↔ cantidad',
    'description': """
        Empaque Estándar
        ================
        - Define empaques estándar por producto (tarima, caja, bulto, saco, contenedor).
        - En la orden de venta, junto a la unidad del producto, se elige el empaque y el
          número de paquetes con cálculo vaivén: paquetes ↔ cantidad (m²/piezas).
        - Cuando el producto tiene empaque estándar, SOLO puede venderse por empaque
          (múltiplos exactos). Cuando no lo tiene, se vende libremente.
        - Sin autorizaciones ni excepciones: la regla es dura.
        - Solo el Administrador de Empaques puede dar de alta los estándares;
          los demás usuarios únicamente los consumen.
    """,
    'author': 'Alphaqueb Consulting SAS',
    'website': 'https://alphaqueb.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'product',
        # Integra el empaque con el modo de cantidad (Asignar / Mandar a pedir)
        # del flujo de asignación: define por_asignar/auto_transit_assign y la
        # restricción de edición de 'Solicitado'.
        'stock_transit_allocation',
        # Fija la posición en la cadena de action_confirm: sin declararlo, el
        # orden real dependía del grafo de módulos y _enforce_pack_compliance
        # podía correr sobre respaldos de cotización o no correr nunca en
        # re-confirmaciones.
        'sale_stone_selection',
        # Empaque también en la reserva/hold (columnas + vaivén + regla dura
        # al confirmar): el modelo y la vista del hold viven en estos módulos.
        'stock_lot_dimensions',
        'inventory_shopping_cart',
    ],
    'data': [
        'security/standard_pack_security.xml',
        'security/ir.model.access.csv',
        'security/multi_company_rules.xml',
        'data/pack_type_data.xml',
        'views/pack_type_views.xml',
        'views/standard_pack_views.xml',
        'views/hold_order_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'wizard/mass_assign_pack_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'standard_pack_som/static/src/sale_line_resequence_fix.js',
            'standard_pack_som/static/src/sale_order_lines.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
