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
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class ProductProduct(models.Model):

    _inherit = 'product.product'

    used_stock = fields.Float('Used stock', compute='_get_used_stock',
                              store=False,
                              digits=dp.
                              get_precision('Product Unit of Measure'),
                              help="Quantity available + stock used in "
                                   "manufacturing")

    def _get_used_stock(self):
        """
            Calculo del stock usado en producciones en stock.
        """
        for prod in self:
            total_qty = 0.0
            if prod.show_used_stock or \
                    self.env.context.get('show_used_stock'):
                new_context = self.env.context
                if not self.env.context.get('warehouse', False):
                    warehouse = self.env['stock.warehouse'].search(
                        [('show_material_stock', '=', True)])
                    if warehouse:
                        new_context = dict(self.env.context)

                        new_context['warehouse'] = warehouse.ids
                bom_lines = self.with_context(new_context).\
                    env['mrp.bom.line'].search([('product_id', '=', prod.id)])
                total_qty = prod.with_context(new_context).qty_available
                for line in bom_lines:
                    if line.product_uom_id.category_id == \
                            prod.uom_id.category_id:
                        line_qty = line.product_uom_id.\
                            _compute_quantity(line.product_qty, prod.uom_id)
                        product_ids = line.bom_id.product_id or \
                            line.bom_id.product_tmpl_id.product_variant_ids
                        for variant in product_ids:
                            bom_prod_qty = line.bom_id.product_uom_id.\
                                _compute_quantity(line.bom_id.product_qty,
                                                  variant.uom_id)
                            total_qty += (line_qty / (bom_prod_qty or 1.0)) * \
                                (variant.used_stock != 0 and
                                 variant.used_stock or
                                 variant.qty_available)

            prod.used_stock = total_qty


class ProductTemplate(models.Model):

    _inherit = "product.template"

    used_stock = fields.Float('Used stock', compute='_get_used_stock',
                              store=False,
                              digits=dp.
                              get_precision('Product Unit of Measure'),
                              help="Quantity available + stock used in "
                                   "manufacturing")
    show_used_stock = fields.Boolean('Show used stock')

    @api.depends('show_used_stock')
    def _get_used_stock(self):
        """
            Calculo del stock usado en producciones en stock.
        """
        for prod in self:
            prod.used_stock = sum(prod.product_variant_ids.
                                  mapped('used_stock'))
