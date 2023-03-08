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

from odoo import models, api, exceptions, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        for order in self:
            if not order.partner_id.commercial_partner_id.vat:
                raise exceptions.Warning(_('The partner %s not have VAT.') %
                                         order.partner_id.
                                         commercial_partner_id.name)
        return super().action_confirm()
