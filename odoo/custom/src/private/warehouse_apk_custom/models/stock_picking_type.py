# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class PickingTypeGroupCode(models.Model):
    _name = 'picking.type.group.code'
    _inherit = ['info.apk', 'picking.type.group.code']

    app_integrated = fields.Boolean('Show in app', default=False)


    default_location = fields.Selection(selection=[('location_id', 'Origen'), ('location_dest_id', 'Destino')], string="Tipo de ubicación por defecto")
    icon = fields.Char("Icono")
    allow_overprocess = fields.Boolean('Overprocess', help="Permitir realizar más cantidad que la reservada")

    batch_domain = fields.Char("Dominio para buscar batchs", help="Este dominio se aplicará", default="[('name', '=', self.name)]")
    batch_group_fields = fields.Many2many(
        "ir.model.fields", string="Agrupar por ...", domain="[('model_id.model', '=', 'stock.picking')]", help="Campo de agrupmiento de albaranes"
    )
    view_move_fields = fields.Char("Campos en Apk",
                                   help="Los campos : De, Para, Paquete Origen, Paquete Destino\n "
                                        "Un cero es no se muestra, 1 se muestra\n"
                                        "Necesita todos a 1 para validar", default="1000")
    required_move_fields = fields.Char("Campos a confirmar en Apk",
                                       help="Los campos : De, Para, Paquete Origen, Paquete Destino, Lote, Cantidad\n "
                                            "Un cero es no leido, 1 es que está leido\n"
                                            "Necesita todos a 1 para validar", default="111111")


    def return_fields(self, mode='tree'):
        return ['code', 'name', 'app_integrated', 'icon']


    def get_move_fields_status(self):
        return {
                'show_location_id': self.view_move_fields[:1] == '1',
                'show_location_dest_id': self.view_move_fields[1:2] == '1',
                'done_location_id': self.required_move_fields[:1] == '1',
                'done_location_dest_id': self.required_move_fields[1:2] == '1',
                'done_qty_done': self.required_move_fields[6:7] == '1'
        }

class StockPickingType(models.Model):

    _name = 'stock.picking.type'
    _inherit = ['info.apk', 'stock.picking.type']

    @api.multi
    def compute_apk_name(self):
        for obj in self:
            obj.apk_name = obj.barcode or obj.name

    app_integrated = fields.Boolean(related='group_code.app_integrated')
    default_location = fields.Selection(related="group_code.default_location")
    group_code_code = fields.Selection(related="group_code.code", store=True)
    allow_overprocess = fields.Boolean(related='group_code.allow_overprocess')
    count_picking_batch_ready = fields.Integer(compute='_compute_picking_batch_count')

    def get_action_picking_batch_tree_ready(self):
        action = self._get_action('stock_picking_batch_extended.action_stock_batch_picking_tree')
        action['domain'] = self.get_picking_batch_domains()['count_picking_batch_ready'] + [('picking_type_id', 'in', self.ids)]
        return action

    def get_picking_batch_domains(self):
        return {'count_picking_batch_ready': [('state', 'in', ['assigned', 'in_progress'])]}

    @api.multi
    def _compute_picking_batch_count(self):
        domains = self.get_picking_batch_domains()
        for field in domains:
            data = self.env['stock.picking.batch'].read_group(domains[field] +
                                                        [('picking_type_id', 'in', self.ids)],
                                                        ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def return_fields(self, mode='tree'):

        fields = ['id', 'apk_name', 'color', 'warehouse_id', 'code', 'name', 'count_picking_ready', 'count_picking_waiting',
                  'count_picking_late', 'count_picking_backorders', 'rate_picking_late', 'barcode', 'count_picking_batch_ready',
                  'rate_picking_backorders']

        if mode == 'form':
            fields += []
        return fields

    def _compute_picking_count_domains(self):
        # DEBE SER UNA COPIA DE LOS DOMINIOS QUE SE USAN PARA CALCULAR LOS VALORES
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        return domains