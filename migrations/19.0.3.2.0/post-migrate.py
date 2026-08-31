# -*- coding: utf-8 -*-
"""Empaques estándar: de "una compañía por default" a catálogo compartido.

Con una sola compañía, el default `env.company` marcaba TODOS los empaques
con esa compañía sin que nadie lo decidiera. Al abrir multiempresa eso los
haría invisibles (ir.rule) para las compañías nuevas mientras el flag
`has_standard_pack` del producto (sudo) seguiría diciendo que sí hay
empaque. Se vacía la compañía para conservar el comportamiento actual:
empaque por producto, compartido. Corre una sola vez (migración de
versión); a partir de aquí el administrador puede fijar compañía a mano.
"""


def migrate(cr, version):
    cr.execute("UPDATE standard_pack SET company_id = NULL WHERE company_id IS NOT NULL")
