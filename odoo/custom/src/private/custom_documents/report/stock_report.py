# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from odoo import models, api


class PackingrReport(models.AbstractModel):
    _name = 'report.custom_documents.report_packing'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        docs = []
        lines = {}
        totals = {}
        for picking in self.env['stock.picking'].browse(docids):
            totals[picking.id] = {'boxes': 0.0, 'qty': 0.0, 'weight': 0.0}
            docs.append(picking)
            pack_ops = {}
            line_pick = []
            for op in picking.move_line_ids:
                if op.result_package_id not in pack_ops.keys():
                    pack_ops[op.result_package_id] = self.env['stock.move']
                pack_ops[op.result_package_id] |= op.move_id
            pack_merged = []
            for packing in pack_ops.keys():
                prod_list = []
                for move in pack_ops[packing]:
                    prod_list.append([move.product_id.id,
                                      move.quantity_done or
                                      move.product_uom_qty])
                measure_package = packing
                measures = measure_package.packaging_id and \
                    measure_package.packaging_id.measures_str or \
                    measure_package.measures
                new_pack = [1, prod_list, measures, pack_ops[packing], packing]
                added = False
                for line in range(len(pack_merged)):
                    eq = False
                    for prod in new_pack[1]:
                        for o_prod in pack_merged[line][1]:
                            if o_prod == prod:
                                eq = True
                    if new_pack[2] == pack_merged[line][2] and eq:
                        pack_merged[line][0] += 1
                        added = True
                if not added:
                    pack_merged.append(new_pack)
            for packing in pack_merged:
                first = True
                for move in packing[3]:
                    code, name = move.product_id.get_product_ref(
                        move.picking_id.partner_id)
                    if not code:
                        code = move.product_id.default_code or ''
                    ref = code or move.product_id.name
                    if first:
                        size = ''
                        weight = 0
                        if packing[4]:
                            weight = packing[4].weight
                            size = packing[2]

                        line_pick.append(
                            {'prod': ref,
                             'boxes': packing[0],
                             'qty': (move.quantity_done or
                                     move.product_uom_qty) * packing[0],
                             'weight': weight,
                             'size': size, 'span': len(packing[3])})
                        totals[picking.id]['boxes'] += packing[0]
                        totals[picking.id]['qty'] += (move.quantity_done or
                                                      move.product_uom_qty) * \
                            packing[0]
                        totals[picking.id]['weight'] += weight * packing[0]
                        first = False
                    else:
                        line_pick.append(
                            {'prod': ref,
                             'boxes': None,
                             'qty': (move.quantity_done or
                                     move.product_uom_qty) * packing[0],
                             'weight': None,
                             'size': None})
                        totals[picking.id]['qty'] += (move.quantity_done or
                                                      move.product_uom_qty) * \
                            packing[0]
            lines[picking.id] = line_pick
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': dict(
                data,
                totals=totals,
                lines=lines
            ),
        }


class picking_report(models.AbstractModel):
    _name = 'report.custom_documents.report_picking_'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        packs = {}
        for picking in self.env['stock.picking'].browse(docids):
            my_ctxt = dict(self.env.context)
            my_ctxt['lang'] = picking.partner_id.lang
            packs[picking.id] = self.env['sale.order.line'].\
                with_context(my_ctxt)
            if not picking.sale_id:
                continue
            for line in picking.sale_id.order_line.\
                    filtered(lambda x: x.pack_components):
                if line not in picking.move_lines.mapped('sale_line_id'):
                    continue
                packs[picking.id] |= line
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].browse(docids),
            'data': dict(
                data,
                packs=packs
            ),
        }


class picking_without_company_report(models.AbstractModel):
    _name = 'report.custom_documents.report_picking_final'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        packs = {}
        for picking in self.env['stock.picking'].browse(docids):
            my_ctxt = dict(self.env.context)
            my_ctxt['lang'] = picking.partner_id.lang
            packs[picking.id] = self.env['sale.order.line'].\
                with_context(my_ctxt)
            if not picking.sale_id:
                continue
            for line in picking.sale_id.order_line.\
                    filtered(lambda x: x.pack_components):
                if line not in picking.move_lines.mapped('sale_line_id'):
                    continue
                packs[picking.id] |= line
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].browse(docids),
            'data': dict(
                data,
                packs=packs
            ),
        }


class picking_internal_report(models.AbstractModel):
    _name = 'report.custom_documents.report_internal_picking'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        packs = {}
        '''
            Estructura
            lin_: linea de venta de producto pack, si no forma parte de un
                  pack es False
            mv*: movimientos
            [(lin_, [mv1, mv2, mv3])]
        '''
        for picking in self.env['stock.picking'].browse(docids):
            packs[picking.id] = []
            packs_dict = {}
            for line in picking.move_lines:
                if line.state == 'cancel':
                    continue
                if line.phantom_bom_component:
                    pack_top = line.sale_line_id
                    if not pack_top and line.move_dest_ids:
                        pack_top = line.move_dest_ids[0].sale_line_id
                    if not packs_dict.get(pack_top.id, False):
                        packs_dict[pack_top.id] = []
                    packs_dict[pack_top.id].append(line)
                else:
                    packs[picking.id].append((False, [line]))
            for sale_line_id in packs_dict.keys():
                sale_line = self.env['sale.order.line'].browse(sale_line_id)
                packs[picking.id].append((sale_line, packs_dict[sale_line_id]))
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].browse(docids),
            'data': dict(
                data,
                moves=packs
            ),
        }
