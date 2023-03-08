# (c) 2014 Jesús Ventosinos Mayor - Comunitea Servicios Tecnológicos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': "Product name for customers",
    'version': '12.0.1.0.0',
    'category': 'product',
    'description': """Show different product name for customers""",
    'author': 'Comunitea',
    'website': 'https://comunitea.com',
    "depends": ['sale_stock'],
    "data": ['views/product_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
