# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        context = dict(self.env.context)
        context['stock_without_phantom'] = True
        self.env.context = context

        return super().open_table()
