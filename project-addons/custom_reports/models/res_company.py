# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_header_message = fields.Text()
    report_sales_footer_message = fields.Text()
    report_purchases_footer_message = fields.Text()
    report_sales_email = fields.Char()
    report_purchases_email = fields.Char()