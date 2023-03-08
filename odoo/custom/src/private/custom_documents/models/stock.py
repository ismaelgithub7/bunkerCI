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


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    weight_edit = fields.Float('Weight', compute='compute_weight', store=True,
                               readonly=False)

    @api.depends('weight')
    def compute_weight(self):
        for pick in self:
            pick.weight_edit = pick.weight


class ProductPackaging(models.Model):

    _inherit = 'product.packaging'

    measures_str = fields.Char('Measures', compute='_get_measures')

    def _get_measures(self):
        for pack in self:
            pack.measures_str = str(pack.height) + 'x' + str(pack.width) + \
                'x' + str(pack.length)


class StockQuantPackage(models.Model):

    _inherit = 'stock.quant.package'

    measures = fields.Char('Measures')
    weight = fields.Float('Weight', compute=None)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _compute_phantom_bom_component(self):
        for move in self:
            phantom_component = False
            if move.sale_line_id and \
                    move.sale_line_id.product_id != move.product_id:
                phantom_component = True
            elif move.move_dest_ids and move.move_dest_ids[0].\
                    sale_line_id and move.move_dest_ids[0].\
                    sale_line_id.product_id != move.product_id:
                phantom_component = True
            move.phantom_bom_component = phantom_component

    def _action_confirm(self, merge=True, merge_into=False):
        if not merge_into:
            merge = False
        return super()._action_confirm(merge=merge, merge_into=merge_into)
