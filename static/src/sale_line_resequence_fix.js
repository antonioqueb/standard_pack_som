/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { StaticList } from "@web/model/relational_model/static_list";

/**
 * Fix defensivo del crash de Odoo 19 al crear una línea (Enter) en una lista
 * editable con campo handle (sequence).
 *
 * Causa: en `static_list.js`, `this.orderBy = this.config.orderBy`. En la lista
 * embebida de las líneas de venta ese `orderBy` puede quedar VACÍO. Al crear una
 * línea nueva, `_addNewRecordAtIndex` -> `_resequence` -> `_sort()` (sin pasar
 * orderBy, usa el vacío) -> `compareRecords` hace `orderBy[0]` y lanza:
 *   "Cannot destructure property 'name' of 'orderBy[0]' as it is undefined".
 *
 * Solución: si `_sort` recibe un orderBy vacío, se ordena por el campo handle
 * (sequence) si existe; si no hay handle ni orden, se omite el reordenamiento.
 * El parche SOLO actúa cuando hoy hay crash (orderBy vacío), por lo que no altera
 * el comportamiento de las listas que ya funcionan (orderBy no vacío -> super).
 */
patch(StaticList.prototype, {
    async _sort(currentIds = this.currentIds, orderBy = this.orderBy) {
        if ((!orderBy || !orderBy.length) && this.handleField) {
            orderBy = [{ name: this.handleField, asc: true }];
        }
        if (!orderBy || !orderBy.length) {
            // Sin criterio de orden: no se reordena, pero tampoco se revienta.
            return;
        }
        return super._sort(currentIds, orderBy);
    },
});
