##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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
from odoo import api, models, fields


class ProductProduct(models.Model):

    _inherit = 'product.product'

    manual_minimum_stock = fields.Float('Manual minimum stock')
    reordering_min_qty = fields.Float(string="Min. qty for purchase")
    is_pack = fields.Boolean("Is pack", compute="_get_is_pack", store=True)

    @api.depends('bom_ids.type')
    @api.multi
    def _get_is_pack(self):
        for prod in self:
            if prod.bom_ids.filtered(lambda r: r.type == 'phantom'):
                prod.is_pack = True
            else:
                prod.is_pack = False

    def _compute_quantities_dict(self, lot_id, owner_id, package_id,
                                 from_date=False, to_date=False):
        res = super()._compute_quantities_dict(lot_id, owner_id, package_id,
                                               from_date=from_date,
                                               to_date=to_date)
        if not self.env.context.get('stock_without_phantom'):
            for prod in self.filtered('bom_ids'):
                for bom in prod.bom_ids.filtered(lambda r: r.type == 'phantom'):
                    res_components = bom.bom_line_ids.mapped('product_id').\
                        _compute_quantities_dict(False, False, False)
                    res[prod.id]['qty_available'] = \
                        min([res_components[x]['qty_available']
                            for x in res_components])
                    res[prod.id]['incoming_qty'] = \
                        min([res_components[x]['incoming_qty']
                            for x in res_components])
                    res[prod.id]['outgoing_qty'] = \
                        min([res_components[x]['outgoing_qty']
                            for x in res_components])
                    res[prod.id]['virtual_available'] = \
                        min([res_components[x]['virtual_available']
                            for x in res_components])

        return res


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    miami = fields.Boolean('Miami')
    reordering_min_qty = fields.Float(string="Min. qty for purchase")
    manual_minimum_stock = fields.\
        Float('Manual minimum stock', readonly=True,
              related="product_variant_ids.manual_minimum_stock")
