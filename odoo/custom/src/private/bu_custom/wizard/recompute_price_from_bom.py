# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api


class RecomputePriceFromBom(models.TransientModel):

    _name = 'recompute.price.from.bom'

    @api.multi
    def recompute_price_from_bom(self):
        bom_objs = self.env['mrp.bom'].search([])
        # Get all diferent product.template objs in the all the BoM
        bom_objs.mapped('product_tmpl_id').action_bom_cost()

    @api.model
    def _do_cron(self):
        self.create({}).recompute_price_from_bom()
