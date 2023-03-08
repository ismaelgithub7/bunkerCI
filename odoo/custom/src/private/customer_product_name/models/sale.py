# (c) 2014 Jesús Ventosinos Mayor - Comunitea Servicios Tecnológicos S.L.
# (c) 2020 Omar Castiñeira Saavedra - Comunitea Servicios Tecnológicos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    def get_sale_order_line_multiline_description_sale(self, product):
        if self.order_id.partner_id and product:
            code, name = product.get_product_ref(self.order_id.partner_id)
            if code or name:
                if not name:
                    name = product.name
                if not code:
                    code = product.default_code or ''
                ref = '[' + code + '] ' if code else ''
                return ref + name

        return super().get_sale_order_line_multiline_description_sale(product)
