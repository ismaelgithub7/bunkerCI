# (c) 2014 Jesús Ventosinos Mayor - Comunitea Servicios Tecnológicos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ProductCustomer(models.Model):

    _name = 'product.customer'
    _description = "Customer's product names"

    name = fields.Char('Name', size=64)
    code = fields.Char('Code', size=64)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    product_id = fields.Many2one('product.template', 'Reference')


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    product_customer_ids = fields.One2many('product.customer', 'product_id',
                                           'Customer name')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    def get_product_ref(self, partner):
        self.ensure_one()
        if not partner:
            return self.default_code or '', self.name
        if isinstance(partner, (int)):
            partner = self.env['res.partner'].browse(partner)
        custom_prod = self.env['product.customer'].search(
            [('product_id', '=', self.product_tmpl_id.id),
             ('customer_id', '=', partner.id)])
        if not custom_prod:
            top_partner_id = partner.commercial_partner_id
            custom_prod = self.env['product.customer'].search(
                [('product_id', '=', self.product_tmpl_id.id),
                 ('customer_id', '=', top_partner_id.id)])
        return custom_prod and custom_prod[0].code or '', custom_prod and \
            custom_prod[0].name or ''
