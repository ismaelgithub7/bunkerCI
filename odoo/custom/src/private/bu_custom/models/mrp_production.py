from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    @api.depends('bom_id.routing_id', 'bom_id.routing_id.operation_ids')
    def _compute_routing(self):
        for production in self:
            if production.bom_id.routing_id:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False
