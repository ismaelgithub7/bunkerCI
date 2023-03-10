# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2019 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
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

from odoo import _, api, models, fields
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import time
import pprint
import logging

_logger = logging.getLogger(__name__)


from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockPicking(models.Model):

    _inherit = ['info.apk', 'stock.picking']
    _name = 'stock.picking'

    @api.multi
    def compute_apk_name(self):
        for obj in self:
            obj.apk_name = obj.name

    @api.multi
    def compute_move_line_count(self):
        for pick in self:
            pick.move_line_count = len(pick.move_line_ids)

    team_id = fields.Many2one("crm.team")
    batch_id = fields.Many2one(domain="[('state', 'in', ('assigned', 'draft'))]")
    app_integrated = fields.Boolean(related='picking_type_id.app_integrated')
    move_line_count = fields.Integer('# Operaciones', compute="compute_move_line_count")
    default_location = fields.Selection(related='picking_type_id.group_code.default_location')
    group_code = fields.Selection(related='picking_type_id.group_code.code')
    barcode_re = fields.Char(related='picking_type_id.warehouse_id.barcode_re')
    product_re = fields.Char(related='picking_type_id.warehouse_id.product_re')

    def return_fields(self, mode='tree'):
        res = ['id', 'apk_name', 'location_id', 'location_dest_id', 'scheduled_date', 'state',
               'purchase_id', 'sale_id', 'move_line_count', 'picking_type_id', 'default_location',
               'priority', 'partner_id', 'carrier_id', 'team_id']
        if mode == 'form':
            res += ['field_status', 'group_code', 'barcode_re', 'product_re', 'carrier_weight', 'carrier_packages']
        return res

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

    @api.model
    def get_picking_list(self, values):
        _logger.debug("get_picking_list")
        domain = []
        if values.get('picking_type_id', False):
            domain += [('picking_type_id', '=', values['picking_type_id'])]
        if values.get('domain_name', False):
            domain += self._compute_picking_count_domains()[values['domain_name']]
        if values.get('search', False):
            domain += [('name', 'ilike', values['search'] )]
        if values.get('state', False):
            domain += [('state', '=', values['state']['value'])]
        if not domain and values.get('active_ids'):
            domain += [('id', 'in', values.get('active_ids'))]
        values['domain'] = domain
        return self.get_model_object(values)


    def get_move_domain_for_picking(self, picking_id):
        return  [('picking_id', '=', picking_id.id)]


    def get_model_object(self, values={}):
        res = super().get_model_object(values=values)
        if values.get('view', 'tree') == 'tree':
            return res
        picking_id = self
        if not picking_id:
            domain = values.get('domain', [])
            limit = values.get('limit', 1)
            move_id = self.search(domain, limit)
            if not picking_id or len(picking_id) != 1:
                return res

        values = {'domain': self.get_move_domain_for_picking(picking_id)}
        res['move_lines'] = self.env['stock.move'].get_model_object(values)
        #print ("------------------------------Move lines")
        #pprint.PrettyPrinter(indent=2).pprint(res['move_lines'])
        res.update(picking_id.picking_type_id.group_code.get_move_fields_status())

        return res



    @api.model
    def action_done_apk(self, values):
        return self.button_validate_apk(values)

    @api.model
    def action_assign_apk(self, vals):
        picking = self.browse(vals.get('id', False))
        if not picking:
            raise ValidationError(u"No se ha encontrado el albarán")
        res = picking.action_assign()
        return res

    @api.model
    def do_unreserve_apk(self, vals):

        picking = self.browse(vals.get('id', False))
        if not picking:
            raise ValidationError(u"No se ha encontrado el albarán")
        res = picking.do_unreserve()
        return True


    @api.model
    def button_validate_apk(self, vals):
        picking_id = self.browse(vals.get('id', False))
        if not picking_id:
            raise ValidationError ('No se ha encontrado el albarán')
        if all(move_line.qty_done == 0 for move_line in picking_id.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel'))):
            raise ValidationError ('No hay ninguna cantidad hecha para validar')
        ctx = picking_id._context.copy()
        ctx.update(skip_overprocessed_check=True)
        picking_id.with_context(ctx).button_validate()
        return picking_id.get_model_object({'view': 'form'})

    @api.model
    def force_set_qty_done_apk(self, vals):
        picking = self.browse(vals.get('id', False))
        field = vals.get('field', False)
        if not picking:
            raise ValidationError(u"No se ha encontrado el albarán.")

        ctx = self._context.copy()
        ctx.update(model_dest="stock.move.line")
        ctx.update(field=field)
        res = picking.with_context(ctx).force_set_qty_done()
        return True

    @api.model
    def force_reset_qties_apk(self, vals):
        picking = self.browse(vals.get('id', False))
        if not picking:
            return {'err': True, 'error': "No se ha encontrado el albarán."}
        ctx = self._context.copy()
        ctx.update(reset=True)
        res = picking.with_context(ctx).force_set_qty_done()
        return True

    @api.model
    def process_qr_lines(self, vals):
        qr_codes = self.browse(vals.get('qr_codes', False))
        if not qr_codes:
            return {'err': True, 'error': "No se han recibido datos del código QR."}
        return True

    @api.model
    def find_pick_by_name(self, vals):
        domain = [('name', 'ilike', vals['name'])]
        res = self.search_read(domain, ['id'], limit=1)
        if res:
            return res[0]['id']
        return False

    @api.model
    def find_serial_for_move(self, vals):
        # En esta funciuón miro si es un serial, si no busco en el barcode o en el wh_code a ver si encuentro un producto
        lot_name = vals.get('lot_id', False)
        picking_id = vals.get('picking_id', False)
        remove = vals.get('remove', False)
        if not picking_id:
            return
        if not lot_name:
            return

        ## Miro si es un lote o varios
        move = False

        lot_names = lot_name.split(',')
        moves_to_recompute = self.env['stock.move']
        for lot_name in lot_names:
            lot = self.env['stock.production.lot'].search([('name', '=', lot_name)], limit=1)
            if lot:
                move = self.serial_for_move(picking_id, lot, remove)
            if move:
                moves_to_recompute |= move
        if moves_to_recompute:
            moves_to_recompute._recompute_state()
            return move.get_model_object()

        ## NO se han encontrado numeros de serie, miro si es un producto.
        domain = [('picking_id', '=', picking_id), ('product_id.tracking', '=', 'none') , '|', ('product_id.wh_code', '=', lot_name), ('product_id.barcode', '=', lot_name)]
        move_line_id = self.env['stock.move.line'].search(domain)
        if not move_line_id:
            raise ValidationError ('No se ha encontrado nada para el código {}'.format(lot_name))
        if len(move_line_id)>1:
            raise ValidationError('Se han encontrado varias opciones. No hay info suficiente para el código {}'.format(lot_name))
        values = {
            'move_id': move_line_id.move_id.id,
            'location_id': move_line_id.location_id.id,
            'inc': 1}
        return move_line_id.move_id.set_qty_done_from_apk(values)


        return False

    @api.model
    def serial_for_move(self, picking_id, lot, remove):
        lot_id = lot.id
        product_id = lot.product_id.id
        new_location_id = lot.compute_location_id()
        domain = [('picking_id', '=', picking_id), ('product_id', '=', product_id)]

        if False and remove:
            domain += [('lot_id', '=', lot_id)]
            line = self.env['stock.move.line'].search(domain, limit=1, order='lot_id desc')
            line.qty_done = 0
        else:
            # caso 1. COnfirmar el lote que hay
            lot_domain = domain + [('lot_id', '=', lot_id)]
            line = self.env['stock.move.line'].search(lot_domain, limit=1, order='lot_id desc')
            if line:
                ## si es lote +1 , si es serial = 1
                if line.product_id.tracking == 'serial':
                    line.qty_done = 1
                else:
                    line.qty_done += 1
            else:
                # Caso 2. Hay una vacía con lot_id = False:
                lot_domain = domain + [('lot_id', '=', False)]
                line = self.env['stock.move.line'].search(lot_domain, limit=1, order= 'lot_id desc')
                if not line:
                    lot_domain = domain + [('lot_id', '!=', lot_id), ('qty_done', '=', 0)]
                    line = self.env['stock.move.line'].search(lot_domain, limit=1, order='lot_id desc')
                if line:
                    move = line.move_id
                    line.unlink()
                    result = move._update_reserved_quantity(1, 1, location_id=move.location_id, lot_id=lot, strict=False)
                    if result == 0:
                        raise UserError ('No se ha podido reservar el lote {}. Comprueba que no está    en otro movimiento'.format(lot.name))
                    lot_domain = domain + [('lot_id', '=', lot_id)]
                    line = self.env['stock.move.line'].search(lot_domain, limit=1, order='lot_id desc')
                    if line:
                        line.qty_done = 1
        move = line.move_id
        ##devuelvo un objeto movimietno para actualizar la vista de la app
        if not move:
            return False
        return move



    def get_autoassign_pick_domain(self):
        domain = [
            ("picking_type_id.group_code.app_integrated", "=", True),
            ("batch_id", "=", False),
            ("state", "=", "assigned"),
        ]
        return domain

    def get_autoassign_batch_domain(self):
        batch_domain = (
            self.picking_type_id.group_code.batch_domain
            or "[('picking_type_id', '=', self.picking_type_id.id)]"
        )
        domain = eval(batch_domain)
        domain += [("state", "in", ["assigned", "draft"]), ("user_id", "=", False)]
        return domain

    @api.multi
    def action_auto_assign_batch_id(self):
        domain = self.get_autoassign_pick_domain()
        if self:
            if len(self) == 1:
                domain += [("id", "=", self.id)]
            else:
                domain += [("id", "in", self.ids)]
        self.env["stock.picking"].search(domain).auto_assign_batch_id()

    def get_new_batch_values(self):
        return {
            "picking_type_id": self.picking_type_id.id,
            "name": self.name,
            "user_id": False,
            "partner_id": self.partner_id.id,
            "carrier_id": self.carrier_id.id,
            ##"service_code": self.carrier_service and self.carrier_service or self.carrier_id.service_code.id,
            "team_id": self.team_id.id,
            "state": "draft",
            "picking_ids": [(6, 0, self.ids)],
            ## "payment_on_delivery": self.payment_on_delivery,
            "notes": "{}: {}".format(self.name, self.note) if self.note else None,
        }

    @api.multi
    def auto_assign_batch_id(self):
        for pick in self:
            if pick.state != 'assigned':
                raise ValidationError('No puedes enviar el albarán {} : Estado: {}'.format(pick.name, pick.state))
            if pick.batch_id:
                raise ValidationError(
                    "El albarán {} ya está en el lote {}".format(
                        pick.name, pick.batch_id.name
                    )
                )
            batch_id = self.env["stock.picking.batch"].search(
                pick.get_autoassign_batch_domain()
            )
            if not batch_id:
                batch_id = self.env["stock.picking.batch"].create(
                    pick.get_new_batch_values()
                )
            else:
                if pick.note and batch_id.notes:
                    batch_id.notes = "{} // {}: {}".format(
                        batch_id.notes, pick.name, pick.note
                    )
                elif pick.note and not batch_id.notes:
                    batch_id.notes = "{}: {}".format(
                        pick.name, pick.note
                    )
            if batch_id:
                pick.write({"batch_id": batch_id.id})
                batch_id.assign_order_moves()
                _logger.info(
                    "Se mete en el batch {} el albarán {}".format(
                        batch_id.name, pick.name
                    )
                )
                batch_id.verify_state('assigned')
        return

    @api.model
    def create(self, vals):
        if vals.get("origin"):
            sale_id = self.env["sale.order"].search([("name", "=", vals.get("origin"))])
            if sale_id and sale_id.note:
                vals["note"] = sale_id.note
        return super(StockPicking, self).create(vals)

    @api.multi
    def action_cancel(self):
        ## Si tiene batch picking y este está asignado no podemos cancelar
        if self.mapped('batch_id.user_id'):
            for batch_id in self.mapped('batch_id').filtered(lambda x: x.user_id):
                _logger.info("El batch {} no puede ser cancelado porque está asignado".format(batch_id.name))
            raise ValidationError("No puedes cancelar una albarán con un batch ya asignado")
        self.mapped('batch_id').unlink()
        return super().action_cancel()