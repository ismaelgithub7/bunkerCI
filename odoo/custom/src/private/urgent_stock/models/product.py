##############################################################################
#
#    Copyright (C) 2014 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields
import odoo.addons.decimal_precision as dp


class ProductProduct(models.Model):

    _inherit = 'product.product'

    urgent_stock = fields.Float('Urgent stock', compute='_get_urgent_stock',
                                store=False,
                                digits=dp.
                                get_precision('Product Unit of Measure'))

    def _get_urgent_stock(self):
        """
            Calculo del stock necesario para cubrir los albaranes de salida.
        """
        for prod in self:
            new_context = self.env.context
            move_domain = [('state', 'in', ['waiting', 'confirmed',
                                            'partially_available']),
                           ('product_id', '=', prod.id),
                           ('picking_type_id.code', '=', 'outgoing')]
            if not self.env.context.get('warehouse', False):
                warehouse = self.env['stock.warehouse'].search(
                    [('show_material_stock', '=', True)])
                if warehouse:
                    new_context = dict(self.env.context)
                    new_context['warehouse'] = warehouse.ids
                    move_domain += [('warehouse_id', 'in', warehouse.ids)]

            moves_out = self.with_context(new_context).\
                env['stock.move'].search(move_domain)
            total_qty = 0
            for move in moves_out:
                if move.product_uom.category_id == prod.uom_id.category_id:
                    total_qty += move.product_qty
                    total_qty -= move.product_uom.\
                        _compute_quantity(move.reserved_availability,
                                          prod.uom_id)
            if total_qty > prod.with_context(new_context).qty_available:
                prod.urgent_stock = total_qty - \
                    prod.with_context(new_context).qty_available
            else:
                prod.urgent_stock = 0


class ProductTemplate(models.Model):

    _inherit = "product.template"

    urgent_stock = fields.Float('Urgent stock', compute='_get_urgent_stock',
                                store=False,
                                digits=dp.
                                get_precision('Product Unit of Measure'))

    def _get_urgent_stock(self):
        """
            Calculo del stock necesario para cubrir los albaranes de salida.
        """
        for prod in self:
            prod.urgent_stock = sum(prod.product_variant_ids.
                                    mapped('urgent_stock'))
