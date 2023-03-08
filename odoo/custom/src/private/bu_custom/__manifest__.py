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

{
    'name': "BU customizations",
    'version': '12.0.1.0.0',
    'category': '',
    'description': """""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['sale_stock', 'technical_office', 'purchase_force_invoiced',
                'mrp_bom_cost', 'sale_commission', 'product_brand',
                'stock_available_unreserved',
                'stock_inventory_valuation_location'],
    "data": ['views/sale_view.xml', 'views/stock_view.xml',
             'data/cron.xml',
             'wizard/recompute_price_from_bom.xml',
             'views/product_view.xml',
             'views/partner_language_contact_view.xml',
             'views/invoice_view.xml',
             'views/mrp_production_view.xml'],
    "installable": True
}
