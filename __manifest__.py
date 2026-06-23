# -*- coding: utf-8 -*-
{
    'name': 'Empaque Estándar',
    'version': '19.0.1.0.0',
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
    ],
    'data': [
        'security/standard_pack_security.xml',
        'security/ir.model.access.csv',
        'data/pack_type_data.xml',
        'views/pack_type_views.xml',
        'views/standard_pack_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'wizard/mass_assign_pack_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
