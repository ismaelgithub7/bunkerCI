#############################################################################
#
#    Copyright (C) 2020 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    validator = fields.Many2one('res.users', 'Validated by',
                                readonly=True, copy=False)

    @api.multi
    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        self.write({'validator': self.env.user.id})
        return res
