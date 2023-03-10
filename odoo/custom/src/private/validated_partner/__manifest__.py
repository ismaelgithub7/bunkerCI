##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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

{
    'name': "Validated partners",
    'version': '12.0.1.0.0',
    'category': 'stock',
    'description': """Allow to mark partners as validated, invoices to this
partners can be approved by anyone""",
    'author': 'Comunitea',
    'website': 'www.comunitea.com',
    "depends": ['account'],
    "data": ['views/partner_view.xml',
             'data/validated_partner_groups.xml'],
    "installable": True
}
