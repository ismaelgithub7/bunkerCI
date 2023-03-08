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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MaterialCategory(models.Model):

    _name = 'product.material.category'

    name = fields.Char('Name', size=64, required=True)
    complete_name = fields.Char(string='Name', compute='_get_complete_name',
                                store=True)

    parent_id = fields.Many2one('product.material.category', 'Parent Category',
                                index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('product.material.category', 'parent_id',
                               string='Child Categories')

    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    @api.depends('name', 'parent_id')
    def _get_complete_name(self):
        for categ in self:
            if categ.parent_id:
                categ.complete_name = '%s / %s' % \
                    (categ.parent_id.complete_name, categ.name)
            else:
                categ.complete_name = categ.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    material_categ_id = fields.Many2one('product.material.category',
                                        'Material category')
