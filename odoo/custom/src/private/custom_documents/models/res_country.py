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


class ResCountry(models.Model):

    _inherit = 'res.country'

    invoice_report_with_shipping_address = fields.\
        Boolean('Invoice report with shipping address')
    invoice_report_with_validation_data = fields.\
        Boolean('Invoice report with validation data')
    not_show_type_message = fields.Boolean('Not show type of goods')
    show_intrastat = fields.Boolean("Show HS Codes in invoices")
