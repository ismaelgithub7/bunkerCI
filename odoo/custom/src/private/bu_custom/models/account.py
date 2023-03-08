##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'
    _order = "number desc, date_invoice desc, id desc"

    sale_ref = fields.Char(string='Sale ref', compute='_get_so')
    line_agent_id = fields.Many2one('res.partner', 'Agent', store=True,
                                    related="invoice_line_ids.agents.agent",
                                    readonly=True)

    def _get_so(self):
        for invoice in self:
            refs = invoice.invoice_line_ids.\
                mapped('sale_line_ids.order_id.client_order_ref')
            invoice.sale_ref = ",".join([x for x in refs if x])

    @api.multi
    def _get_computed_reference(self):
        self.ensure_one()
        if self.company_id.invoice_reference_type == 'invoice_number' and \
                not self.reference:
            return self.invoice_number[self.invoice_number.rfind('/') + 1:]
        else:
            return super()._get_computed_reference()


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    journal_id = fields.Many2one('account.journal', 'Journal',
                                 related="invoice_id.journal_id")
    invoice_date = fields.Date(related='invoice_id.date_invoice', store=True)
    invoice_type = fields.Selection(store=True)
    line_agent_id = fields.Many2one('res.partner', 'Agent', store=True,
                                    related="agents.agent",
                                    readonly=True)


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    agent_id = fields.Many2one('res.partner', 'Agent')

    def _select(self):
        select_str = super()._select()
        select_str += """
            , sub.line_agent_id as agent_id
            """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()
        select_str += """
            , ail.line_agent_id
            """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ", ail.line_agent_id"
        return group_by_str


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def default_get(self, fields):
        rec = super(AccountMoveLine, self).default_get(fields)
        if self.env.context.get('journal_id'):
            journal = self.env['account.journal'].\
                browse(self.env.context['journal_id'])
            if rec.get('debit'):
                rec['account_id'] = journal.default_debit_account_id.id
            elif rec.get('credit'):
                rec['account_id'] = journal.default_credit_account_id.id
            else:
                rec['account_id'] = journal.default_debit_account_id.id

        if 'line_ids' not in self._context:
            return rec

        lines = self.move_id.resolve_2many_commands(
            'line_ids', self._context['line_ids'], fields=['partner_id',
                                                           'name'])
        if lines:
            if lines[-1].get('partner_id'):
                rec['partner_id'] = lines[-1]['partner_id']
            if lines[-1].get('name'):
                rec['name'] = lines[-1]['name']
        return rec

    @api.onchange('partner_id')
    def onchange_partner_id_account(self):
        if not self.account_id and self.move_id.journal_id and self.partner_id:
            part = self.partner_id
            jt = self.move_id.journal_id.type
            id1 = self.partner_id.property_account_payable_id.id
            id2 = self.partner_id.property_account_receivable_id.id

            if jt == "sale":
                self.account_id = part.property_account_position_id and \
                    part.property_account_position_id.map_account(id2) or id2
            elif jt == "purchase":
                self.account_id = part.property_account_position_id and \
                    part.property_account_position_id.map_account(id1) or id1
            elif jt in ('general', 'bank', 'cash'):
                if part.customer:
                    self.account_id = part.property_account_position_id and \
                        part.property_account_position_id.map_account(id2) or \
                        id2
                elif part.supplier:
                    self.account_id = part.property_account_position_id and \
                        part.property_account_position_id.map_account(id1) or \
                        id1
