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

from odoo import models, api, _


class ReportMrpProduction(models.AbstractModel):
    _name = 'report.custom_documents.mrp_production'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        docs = {
            _('with minimun stock'): {},
            _('without minimun stock'): {}
        }
        totals = {
            _('with minimun stock'): {},
            _('without minimun stock'): {},
            'total': {},
        }
        with_totals = totals[_('with minimun stock')]
        without_totals = totals[_('without minimun stock')]
        for production in self.env['mrp.production'].\
                with_context(warehouse=1).browse(docids):
            rules = self.env['stock.warehouse.orderpoint'].search(
                [('product_id', '=', production.product_id.id)])
            if production.routing_id.name not in \
                    docs[_('with minimun stock')].keys() and rules:
                docs[_('with minimun stock')][production.routing_id.name] = []
                with_totals[production.routing_id.name] = 0.0
            if production.routing_id.name not in \
                    docs[_('without minimun stock')].keys() and not rules:
                docs[_('without minimun stock')][production.routing_id.name] =\
                    []
                without_totals[production.routing_id.name] = 0.0
            if production.routing_id.name not in totals['total'].keys():
                totals['total'][production.routing_id.name] = 0.0
            if rules:
                key = _('with minimun stock')
            else:
                key = _('without minimun stock')
            docs[key][production.routing_id.name].append(production)
            totals[key][production.routing_id.name] += production.product_qty
            totals['total'][production.routing_id.name] += \
                production.product_qty
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'product.pricelist',
            'docs': docs,
            'data': dict(
                data,
                totals=totals
            ),
        }
