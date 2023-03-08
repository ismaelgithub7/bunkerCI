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


class ProductProduct(models.Model):

    _inherit = 'product.product'

    tech_office_code = fields.Char('Technical office code')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        recs = self.browse()
        if name:
            recs = self.search([('tech_office_code', operator, name)])

        if not recs:
            return super().name_search(name, args=args, operator=operator,
                                       limit=limit)
        else:
            records = super().name_search(name, args=args, operator=operator,
                                          limit=limit)
            records = [x[0] for x in records]
            records = self.browse(records)
            recs |= records
            return recs.name_get()


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    tech_office_code = fields.\
        Char('Technical office code', readonly=False,
             related="product_variant_ids.tech_office_code")
