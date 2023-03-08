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

from odoo import api, models, fields
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

BINARYPOSITION = {'product_id': 0, 'location_id': 1, 'lot_id': 2, 'package_id': 3, 'location_dest_id': 4, 'result_package_id': 5, 'qty_done': 6}
FLAG_PROP = {'view': 1, 'req': 2, 'done': 4};


class StockMove(models.Model):
    _inherit = 'stock.move'

    order = 'picking_id, sequence, id'

    @api.multi
    def auto_cancel_duplicate_serial(self):

        _logger.info("Anulando lotes ....")
        if self.state != 'done':
            raise ValidationError ('Solo en movimientos realizados')
        _logger.info("Anulando lotes ....")
        for lot_id in self.move_line_ids.mapped('lot_id'):
            new_name = '{} - Cancelado {}'.format(lot_id.name, self.id)
            _logger.info(">>>> {}  ->  {}".format(lot_id.name, new_name))
            lot_id.name = new_name

    @api.multi
    def _compute_move_lines_count(self):
        for sm in self:
            sm.move_lines_count = len(sm.move_line_ids)

    tracking = fields.Selection(related='product_id.tracking')
    wh_code = fields.Char(related='product_id.wh_code')
    sale_id = fields.Many2one(related='picking_id.sale_id')
    move_lines_count = fields.Integer("# Moves", compute="_compute_move_lines_count")
    default_location = fields.Selection(related='picking_type_id.group_code.default_location')
    barcode_re = fields.Char(related='picking_type_id.warehouse_id.barcode_re')
    product_re = fields.Char(related='picking_type_id.warehouse_id.product_re')
    removal_priority = fields.Integer(compute='_compute_move_line_location_id', store=True)
    active_location_id = fields.Many2one('stock.location', copy=False, help ="Situanció actual en el recorrido por el almacén")
    move_line_location_id = fields.Many2one('stock.location', compute="_compute_move_line_location_id", store=True)
    wh_location = fields.Char(related="move_line_location_id.name")
    apk_filter_by_qty = fields.Char(compute="_compute_apk_filter_by_qty")
    apk_order = fields.Integer(string="Apk order", default=0)
    batch_id = fields.Many2one(related='picking_id.batch_id')
    total_qty_done = fields.Integer(related="batch_id.total_qty_done")
    view_move_fields = fields.Char(string='Status', compute="_compute_view_move_fields", store=True)

    @api.multi
    @api.depends('picking_type_id')
    def _compute_view_move_fields(self):
        picking_type_id = self.mapped('picking_type_id')
        if picking_type_id:
            view_move_fields = picking_type_id[0].group_code.view_move_fields
        else:
            ##Muestro ubiación de origen solo
            view_move_fields = "1000"
        for move in self:
            move.view_move_fields = view_move_fields

    def get_move_fields_status(self):
        return {
                'show_location_id': self.picking_type_id.group_code.view_move_fields[:1] == '1',
                'show_location_dest_id': self.picking_type_id.group_code.view_move_fields[1:2] == '1',
                'done_location_id': self.required_move_fields[:1] == '1',
                'done_location_dest_id': self.required_move_fields[1:2] == '1',
                'done_qty_done': self.required_move_fields[6:7] == '1'
        }

    @api.multi
    def _compute_apk_filter_by_qty(self):
        for sm in self:
            if sm.quantity_done < sm.reserved_availability:
                sm.apk_filter_by_qty = 'Pendientes'
            elif sm.quantity_done >= sm.reserved_availability:
                sm.apk_filter_by_qty = 'Hechos'

    @api.multi
    @api.depends('move_line_ids', 'move_line_ids.location_id', 'move_line_ids.location_dest_id')
    def _compute_move_line_location_id(self):
        for sm in self:
            _logger.info("Aplico _compute_move_line_location_id a {}".format(sm.display_name))
            default_location = sm.default_location or 'location_id'
            move_line_location_id = False
            removal_priority = 9999
            if sm.move_line_ids:
                loc_ids = sm.mapped('move_line_ids').mapped(default_location)
                move_line_location_id = loc_ids[:1]
                removal_priority = min([x.removal_priority for x in sm.move_line_ids.mapped(default_location)])
            if not move_line_location_id:
                move_line_location_id = sm[default_location]
            sm.move_line_location_id = move_line_location_id
            sm.removal_priority = removal_priority
            _logger.info(
                "Aplico _compute_move_line_location_id a {}: Move_line_location_id: {}, Removal prioroiyt: {}".format(
                    sm.display_name, move_line_location_id, removal_priority))

    def action_show_details(self):
        res = super().action_show_details()
        res['context']['show_lots_m2o'] = self.has_tracking != 'none'
        return res

    def find_model_object(self, domain=[], search_str='', ids=[]):
        product_domain = domain
        if ids:
            product_domain += [('id', 'in', ids)]
        product_domain += ['|', ('product_id.barcode', '=', search_str), ('product_id.wh_code', '=', search_str)]
        res = self.search_read(product_domain, ['id', 'apk_name'], order ='apk_order')
        if res:
            return [x['id'] for x in res]
            ## Busco en los lotes:
        lot_domain = [('move_id', 'in', ids), ('lot_id.name', '=', search_str)]
        res = self.env['stock.move.line'].search_read(lot_domain, ['move_id'])
        if res:
            return [x['move_id'][0] for x in res]
        location_domain = ['|', ('location_id.barcode', '=', search_str), ('location_dest_id.barcode', '=', search_str)]
        res = self.env['stock.move.line'].search_read(location_domain, ['move_id'])
        if res:
            return [x['move_id'][0] for x in res]
        return False

    def get_default_location(self):
        if self.active_location_id:
            return self.active_location_id.get_model_object()[0]
        elif self.move_line_ids:
            return self.move_line_ids[0][self['default_location']].get_model_object()[0]
        else:
            return self[self['default_location']].get_model_object()[0]

    def get_model_object(self, values={}):

        values.update(order='apk_order asc')
        res = super().get_model_object(values=values)
        if values.get('view', 'tree') == 'tree':
            return res
        move_id = self
        if not move_id:
            domain = values.get('domain', [])
            limit = values.get('limit', 1)
            move_id = self.search(domain, limit, order="apk_order")
            if not move_id or len(move_id) != 1:
                return res
        res['product_id']['image'] = move_id.product_id.image_medium
        values.update(view='form', model='stock.move.line')
        domain = [('move_id', '=', move_id.id)]
        filter = values.get('filter_move_lines', 'Todos')

        ##TODO revisar el filtro realizados
        if filter == 'Pendientes':
            domain += [('qty_done', '=', 0)]
        elif filter == 'Realizados':
            domain += [('qty_done', '!=', 0)]

        limit = 10#
        limit = values.get('sml_limit', 10)
        offset = 0
        offset = max(values.get('sml_offset', 0), 0)
        sml_ids = self.env['stock.move.line'].search(
            domain,
            limit=limit,
            offset=offset,
            order= 'lot_id desc, qty_done desc')
        sml_count = len(sml_ids)
        res['offset'] = offset + sml_count
        res['limit_reached'] = limit > sml_count
        res['sml_count'] = sml_count
        res['sml_count_no_limit'] = self.env['stock.move.line'].search_count(domain)
        if sml_ids:
            res['move_line_ids'] = sml_ids.get_model_object()
        else:
            res['move_line_ids'] = []
        return res

    def return_fields(self, view='tree'):
        fields = ['id', 'product_id', 'product_uom_qty', 'reserved_availability', 'quantity_done', 'tracking', 'state',
                   'move_lines_count', 'wh_code', 'move_line_location_id', 'total_qty_done',
                  'location_id', 'location_dest_id']
        if view == 'form':
            fields += ['apk_order','batch_id', 'picking_id', 'barcode_re', 'default_location', 'sale_id' , 'product_uom', 'active_location_id', 'move_lines_count', 'view_move_fields']
        return fields

    @api.model
    def force_set_qty_done_apk(self, vals):
        move = self.browse(vals.get('id', False))
        if not move:
            return {'err': True, 'error': "No se ha encontrado el movimiento."}
        for move_line in move.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        if not move.picking_type_id.allow_overprocess and move.quantity_done > move.reserved_availability:
            raise ValidationError("No puedes procesar más cantidad de lo reservado para el movimiento")
        return True

    def compute_active_location_id(self, field_location, move):
        move = move or self
        domain = [('id', '=', move[field_location].id), ('putaway_strategy_id.product_id', '=', move.product_id.id)]
        loc_id = self.env['stock.location'].seach(domain, limit=1) or move[field_location]
        return loc_id

    @api.model
    def create_new_sml_id(self, values):
        if self:
            move_id = self
        else:
            move_id = values['id']
            move_id = self.env['stock.move'].browse(move_id)
        if not move_id:
            return False

        location = move_id.active_location_id or move_id[move_id.default_location] or self.env['stock.location']
        location_field = move_id.default_location

        move_vals = move_id._prepare_move_line_vals()
        sml_id = self.env['stock.move.line']
        if location != move_id[location_field]:
            move_vals[location_field] = move_id.active_location_id.id
        move_vals['qty_done'] = max(move_id.product_uom_qty - move_id.quantity_done, 0)
        new_sml_id = sml_id.create(move_vals)
        move_id._recompute_state()
        if self:
            values = {'id': move_id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': values.get('filter_move_lines', 'Todos')}
            return move_id.get_model_object(values)
        return new_sml_id

    @api.model
    def delete_move_line(self, vals):
        sml_id = vals.get('sml_id', False)
        sml_id = self.env['stock.move.line'].browse(sml_id)
        move_id = sml_id.move_id
        qty = sml_id.qty_done
        if False:
            sml_id.unlink()
            move_id._update_reserved_quantity(qty, qty, move_id.location_id, lot_id=False, strict=False)
            move_id._recompute_state()
        else:
            sml_id.qty_done = 0
            sml_id.lot_id = False

        #values.update({'id': move_id.id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': vals.get('filter_move_lines', 'Todos')})
        if not move_id.picking_type_id.allow_overprocess and move_id.quantity_done > move_id.product_uom_qty:
            raise ValidationError("No puedes procesar más cantidad de lo reservado para el movimiento")
        return self.env['info.apk'].get_apk_object(vals)

    @api.model
    def load_eans(self, values):
        ean_ids = values.get('ean_ids', '')
        if not ean_ids:
            return self.create_move_lots(values)
        location_id = values.get('location_id', False)
        ean_ids = values.get('ean_ids').split()
        values.update({'lot_names': ean_ids,
                       'active_location_id': location_id,
                       })
        return self.create_move_lots(values)

    @api.model
    def move_assign_apk(self, values):
        move = self.browse(values.get('id'))
        if move:
            move._action_assign()
        values = {'id': move.id, 'model': 'stock.move', 'view': 'form'}
        return self.env['info.apk'].get_apk_object(values)

    @api.model
    def move_unreserve_apk(self, values):
        move = self.browse(values.get('id'))
        if move:
            move._do_unreserve()
        values = {'id': move.id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': values.get('filter_move_lines', 'Todos')}
        return self.env['info.apk'].get_apk_object(values)

    @api.model
    def clean_lots(self, values):
        move = self.browse(values.get('id'))
        if move:
            move.move_line_ids.write({'lot_name': '', 'lot_id': False, 'qty_done': 0})
        values = {'id': move.id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': values.get('filter_move_lines', 'Todos')}
        return self.env['info.apk'].get_apk_object(values)

    @api.model
    def set_qty_done_from_apk(self, vals):
        move_id = vals.get('move_id', False)
        quantity_done = vals.get('quantity_done', False)
        inc = vals.get('inc', False)
        filter = vals.get('filter_moves', 'Todos')
        if not move_id or not (quantity_done or inc):
            raise ValidationError(u'No se ha enviado la línea o la cantidad a modificar.')
        move = self.browse(move_id)
        if not move:
            raise ValidationError(u'La línea introducida no existe.')
        if inc:
            move.quantity_done += inc
        else:
            move.quantity_done = quantity_done
        if move:
            move._recompute_state()
            if not move.picking_type_id.allow_overprocess and move.quantity_done > move.reserved_availability:
                raise ValidationError("No puedes procesar más cantidad de lo reservado para el movimiento")
            return move.get_model_object()
        return False

    @api.model
    def assign_location_id(self, values):

        move = self.browse(values.get('id'))
        location_field = values.get('location_field')
        if location_field == move.default_location:
            return False
        location_id = values.get('location_id')
        ## Filtro los move_lines por los que no tenga el move.default_location
        smls = move.move_lines###.filtered(lambda x: not x.read_status(move.default_location, 'done'))
        #for move in smls:
        #    move.write_status(move.default_location, 'done')
        smls.write({move.default_location: location_id})
        #values = {'id': move.id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': values.get('filter_move_lines', 'Todos')}
        return self.env['info.apk'].get_apk_object(values)

    @api.model
    def get_move_info_apk(self, vals):
        move_id = vals.get('id', False)
        index = vals.get('index', 0)
        if index:
            picking_id = self.search_read([('id', '=', move_id)], ['picking_id'])
            if not picking_id:
                return False
        if not move_id:
            return False
        move = self.browse(move_id)
        move_lines = move.picking_id.move_lines
        if index != 0:
            if index == -1:
                move_lines = reversed(move_lines)
            is_index = False
            for new_move in move_lines:
                if is_index:
                    break
                is_index = new_move == move
            if is_index:
                move = new_move
        product_id = move.product_id.with_context(location=move.location_id.id)
        data = {'id': move.id,
                'display_name': product_id.display_name,
                'state': move.state,
                'image': product_id.image_medium,
                'barcode': product_id.barcode,
                'picking_id': {'id': move.picking_id.id,
                                'display_name': move.picking_id.display_name,
                                'code': move.picking_id.picking_type_code},
                'tracking': product_id.tracking,
                'default_code': product_id.default_code,
                'qty_available': product_id.qty_available,
                'location_id': {'id': move.location_id.id,
                                'display_name': move.location_id.display_name,
                                'barcode': move.location_id.barcode},
                'location_dest_id': {'id': move.location_dest_id.id,
                                     'display_name': move.location_dest_id.display_name,
                                     'barcode': move.location_dest_id.barcode},
                'product_uom_qty': move.product_uom_qty,
                'uom_move': {'uom_id': move.product_uom.id, 'name': move.product_uom.name},
                'quantity_done': move.quantity_done,
                'ready_to_validate': sum(line.qty_done for line in move.picking_id.move_line_ids) == sum(line.product_uom_qty for line in move.picking_id.move_line_ids)
                }
        lot_id = []
        lot_ids = move.move_line_ids.mapped("lot_id")
        lot_names = move.move_line_ids.mapped("lot_name")
        for lot in lot_ids:
            lot_id.append({
                'id': lot.id,
                'name': lot.name
            })
        for lot_name in lot_names:
            lot_id.append({
                'id': False,
                'name': lot_name
            })
        data['lot_ids'] = lot_id
        return data


    def update_sml_ids(self, move, sml_ids_to_update):
        _logger.info(u'-->> Actualizo los movimientos con lotes: %s' % sml_ids_to_update.mapped('lot_id.name'))
        vals = {}
        ##para no llamar a write_status para todos llamo a uno y escribo al resto
        sml_id = sml_ids_to_update[0]
        if move.tracking == 'serial':
            sml_id.qty_done = 1
            vals['qty_done'] = 1

        if len(sml_ids_to_update)>1:
            sml_ids_to_update[1:].write(vals)
        return


    @api.model
    def create_move_lots(self, vals):
        _logger.info("APK. Stock_move. create_move_lots con {}".format(vals))


        move_id = vals.get('id', False)
        lot_names = vals.get('lot_names', False)
        if not lot_names:
            raise ValidationError(u"No has enviado ningún lote valido")
        move = self.browse(move_id)
        if not move:
            raise ValidationError(u"No has enviado ningún movimiento válido")
        if move.product_id.default_code in lot_names:
            raise ValidationError(u"Verifica que no has leido el codigo del producto")
        #Recupero la ubicación activa o la establezco por defecto
        active_location_id = vals.get('active_location', False)
        move_lot_names = move.move_line_ids.mapped('lot_id.name')
        if lot_names:
            lot_ids = self.env['stock.production.lot']
            for lot in lot_names:
                if lot in move_lot_names:
                    _logger.info("APK. El lote {} ya está en la lista".format(lot))
                    continue
                lot_id = lot_ids.find_or_create_lot(lot.upper(), move.product_id, not move.picking_type_id.use_existing_lots)
                if lot_id:
                    lot_ids |= lot_id

        move.update_move_lot_apk(move, lot_ids, active_location=False)
        move._recompute_state()
        ## Devuelvo la información del moviemitno para ahorrar una llamada desde la apk

        if not move.picking_type_id.allow_overprocess and move.quantity_done > move.reserved_availability:
            raise ValidationError(u"No puedes procesar más cantidad de lo reservado para el movimiento")
        ## values = {'id': move.id, 'model': 'stock.move', 'view': 'form', 'filter_move_lines': vals.get('filter_move_lines', 'Todos')}
        return self.env['info.apk'].get_apk_object(vals)


    def update_move_lot_apk(self, move, lot_ids, active_location=False, sql=True):
        if move.product_id.tracking != 'serial':
            raise ValidationError(u'El producto %s no tiene tracking por número de serie'% move.product_id.display_name)
        if not active_location:
            active_location = move.active_location_id or move.move_line_location_id

        sml_ids_to_update = self.env['stock.move.line']

        ## Quito los lotes que ya han sido leidos
        confirmed_lots = move.move_line_ids.filtered(lambda x: x.qty_done and x.lot_id in lot_ids)
        lot_ids -= confirmed_lots.mapped('lot_id')

        move_ids = move.move_line_ids.filtered(lambda x: not x.qty_done) - confirmed_lots

        ## Filtro los moviminetos que tienen lotes que el isuairo introduce. Si qty_done = 0 , los actualizo, si no los ignoro
        sml_with_lot_ids = move_ids.filtered(lambda x: x.lot_id in lot_ids)

        ## Los lotes que están en los movimeintos los saco del conjunto
        lot_ids -= sml_with_lot_ids.mapped('lot_id')

        # Los que no tienen qty_done, los meto to update
        sml_ids_to_update += sml_with_lot_ids.filtered(lambda x: x.qty_done == 0)

        # Me quedan los siguientes movimientos "libres" por estudiar
        move_ids = move_ids - sml_with_lot_ids
        if not lot_ids:
            if sml_ids_to_update:
                self.update_sml_ids(move, sml_ids_to_update)
            return move
        ## Es una entrada  ono requiere reservas
        if move.location_id.should_bypass_reservation() \
                or move.product_id.type == 'consu':
            while move_ids and lot_ids:
                move_id = move_ids[0]
                lot_id = lot_ids[0]
                move_id.lot_id = lot_id
                lot_ids -= lot_id
                move_ids -= move_id
                sml_ids_to_update += move_id

        else:
            ## Intercambio los lotes en los movimientos
            update_sml_ids, lot_ids = self.reserve_not_free_lots(move, move_ids, lot_ids)
            #Devuelve un listado de moviemitnos y lotes que tendo que actualizar y o no tocar mas, ademas, lot_ids le ha quitado unidades
            sml_ids_to_update += update_sml_ids
            move_ids -= update_sml_ids

            ## Pongo los lotes libres en los movimientos tengan un lote no leido
            update_sml_ids, lot_ids = self.reserve_free_lots(move, move_ids, lot_ids)
            # Devuelve un listado de moviemitnos y lotes que tendo que actualizar y o no tocar mas, ademas, lot_ids le ha quitado unidades
            sml_ids_to_update += update_sml_ids
            move_ids -= update_sml_ids
            #Si aun me quedan lotes ....
            if lot_ids and move_ids:
                msg = u'Error. No deberías de tener lotes y movimeintos'
                _logger.info (msg)
                raise (msg)

        if lot_ids and move.picking_type_id.allow_overprocess:
            _logger.info(u'-->> Creamos nuevos movimientos para los lotes %s' % lot_ids.mapped('name'))
            for lot_id in lot_ids:
                if move.quantity_done >= move.reserved_availability:
                    break
                reserved = move._update_reserved_quantity(1, 1, move.location_id, lot_id=lot_id, strict=False)
                if reserved:
                    sml_with_lot_ids += move.move_line_ids[-1]

        if sml_ids_to_update:
            self.update_sml_ids(move, sml_ids_to_update)


        return move


    def reserve_not_free_lots(self, move, move_ids, lot_ids):
        ### BUSCO DE LOS LOTES QUE QUEDAN, LOS QUE NO ESTÁN RESERVADOS
        _logger.info(u"Busco en otros movimeintos que ya estén resevados para intercambiarlos")

        sml_ids_to_update = self.env['stock.move.line']
        sml_no_lot_ids = move_ids.filtered(lambda x: x.qty_done == 0 and x.lot_id not in lot_ids)
        domain = [('state', '=', 'assigned'),
                  ('move_id', '!=', move.id),
                  ('move_id.product_id', '=', move.product_id.id),
                  ('location_id', 'child_of', move.location_id.id),  # No tienen porque estar en la misma estanteria
                  ('lot_id', 'in', lot_ids.ids)]
        sml_ids =  self.env['stock.move.line'].search(domain)
        ## Si hay alguno ya hecho, entonces error
        done_sml_ids = sml_ids.filtered(lambda x: x.qty_done)
        if done_sml_ids:
            msg = u'Estos lotes están hechos: '
            for done_sml_id in done_sml_ids:
                msg = u'{} {} en {}, '.format(msg, done_sml_id.lot_id.name, done_sml_id.picking_id.name)
            _logger.info(u"No hay lotes ocupados")
            raise ValidationError(msg)
        ## Están todos con qty_done a 0
        sml_ids_to_unreserve = sml_ids
        if not  sml_ids_to_unreserve:
            _logger.info(u"No hay lotes ocupados")
            return sml_ids_to_update, lot_ids

        if sml_ids_to_unreserve:
            msg = u"Los lotes {} están en otros movimientos y se intercambiarán".format(sml_ids_to_unreserve.mapped('lot_id.name'))
        else:
            msg = u"No se ha encontrado nngún lote asignado fuera de este movimiento"
        _logger.info(msg)
        execute_sql = False
        for to_unreserve in sml_ids_to_unreserve:
            sml_id = sml_no_lot_ids[0]
            lot_id = to_unreserve.lot_id
            ##Intercambio los lotes de 2 movimientos
            sql = "update stock_move_line set location_id = %d,location_dest_id = %d,lot_id = %d where id = %d; " \
                  "update stock_move_line set location_id = %d,location_dest_id = %d,lot_id = %d where id = %d; " \
                  % (sml_id.location_id.id,
                     sml_id.location_dest_id.id,
                     sml_id.lot_id.id,
                     to_unreserve.id,
                     to_unreserve.location_id.id,
                     to_unreserve.location_dest_id.id,
                     to_unreserve.lot_id.id,
                     sml_id.id,
                     )
            msg = u"Libero el lote {} en el movimiento, y lo traigo al movimiento {} con lote {}".format(lot_id.name, to_unreserve.id, sml_id.id, sml_id.lot_id.name)
            _logger.info(msg)
            self._cr.execute(sql)
            execute_sql = True
            sml_ids_to_update += sml_id
            sml_no_lot_ids -= sml_id
            lot_ids -= lot_id
        if execute_sql:
            self._cr.commit()
        return sml_ids_to_update, lot_ids

    def reserve_free_lots(self, move, move_ids, lot_ids):
        _logger.info(u"Busco en otros movimeintos que no estén resevados")
        sml_ids_to_update = self.env['stock.move.line']
        ### BUSCO DE LOS LOTES QUE QUEDAN, LOS QUE NO ESTÁN RESERVADOS
        while move_ids and lot_ids:
            move_id = move_ids[0]
            move_ids -= move_id
            lot_id = lot_ids[0]
            msg = u"Libero el lote {} en el movimiento {}, y le asigno el  lote {}".format(move_id.lot_id.name, move_id.id, lot_id.name)
            _logger.info(msg)
            move_id.unlink()
            reserved = move._update_reserved_quantity(1, 1, move.location_id, lot_id=lot_id, strict=False)
            if not reserved:
                ## Esto a continuación es solo para ayudar a identificar el problema
                _logger.info (u'No se ha podido reservar el lote {} poara el movimiento {}'.format(lot_id.name, move.display_name))
                domain = [('location_id', 'child_of', move.location_id.id),
                          ('product_id', '=', move.product_id.id),
                          ('lot_id', '=', lot_id.id)]
                quant = self.env['stock.quant'].search(domain)
                if not quant:
                    msg = '>>> No hay stock en {} para {} con serie {}'.format(
                        move.location_id.name, move.product_id.default_code, lot_id.name)
                    _logger.info(msg)
                    raise ValidationError(msg)

                elif quant.reserved_quantity != 0:
                    ## Busco el movimiento que lo está reservando
                    domain = [('location_id', 'child_of', move.location_id.id),
                              ('lot_id', '=', lot_id.id),
                              ('move_id.product_id', '=', move.product_id.id),
                              ('state', '=', 'assigned')]
                    moves = self.env['stock.move.line'].search(domain).mapped('move_id.display_name')
                    if not moves:
                        msg = '>>>No hay movimeito con origen {} para {} con serie {}'.format(move.location_id.name,
                                                                               move.product_id.default_code,
                                                                               lot_id.name)
                        _logger.info(msg)
                        raise ValidationError(msg)
                    msg = 'El stock en {} para {} con serie {} ya esta reservado y hecho para otro movimiento {}'.format(
                            move.location_id.name, move.product_id.default_code, lot_id.name, moves)
                    _logger.info(msg)
                    raise ValidationError(msg)
                else:
                    raise ValidationError('No se ha podido reservar. Causa desconocida')

            sml_ids_to_update += move.move_line_ids.filtered(lambda x: x.lot_id == lot_id)
            lot_ids -= lot_id
        return sml_ids_to_update, lot_ids