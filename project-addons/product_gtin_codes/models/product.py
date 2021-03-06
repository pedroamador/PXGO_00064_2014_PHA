# -*- coding: utf-8 -*-
# © 2017-2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class ProductGtin(models.TransientModel):
    _name = 'product.gtin'
    _rec_name = 'gtin12'

    gtin = fields.Char()
    gtin12 = fields.Char(string='GTIN12', required=True)
    gtin13 = fields.Char(string='GTIN13')
    gtin14_1 = fields.Char(string='GTIN14 (1)')
    gtin14_2 = fields.Char(string='GTIN14 (2)')
    gtin14_3 = fields.Char(string='GTIN14 (3)')
    gtin14_4 = fields.Char(string='GTIN14 (4)')
    gtin14_5 = fields.Char(string='GTIN14 (5)')
    gtin14_6 = fields.Char(string='GTIN14 (6)')
    gtin14_7 = fields.Char(string='GTIN14 (7)')
    gtin14_8 = fields.Char(string='GTIN14 (8)')

    @api.onchange('gtin12')
    def onchange_gtin12(self):
        def control_code(code):
            sum = 0
            for d in range(13):
                sum += int(code[d]) * (3 if d % 2 == 0 else 1)
            return (10 - sum % 10) % 10

        def control_code13(code):
            sum = 0
            for d in range(12):
                sum += int(code[d]) * (1 if d % 2 == 0 else 3)
            return (10 - sum % 10) % 10

        gtin12 = self.gtin12
        if gtin12 and len(gtin12) == 12 and gtin12.isdigit():
            self.gtin13 = gtin12 + str(control_code13(gtin12))
            self.gtin14_1 = '1' + gtin12 + str(control_code('1' + gtin12))
            self.gtin14_2 = '2' + gtin12 + str(control_code('2' + gtin12))
            self.gtin14_3 = '3' + gtin12 + str(control_code('3' + gtin12))
            self.gtin14_4 = '4' + gtin12 + str(control_code('4' + gtin12))
            self.gtin14_5 = '5' + gtin12 + str(control_code('5' + gtin12))
            self.gtin14_6 = '6' + gtin12 + str(control_code('6' + gtin12))
            self.gtin14_7 = '7' + gtin12 + str(control_code('7' + gtin12))
            self.gtin14_8 = '8' + gtin12 + str(control_code('8' + gtin12))

    @api.model
    def get_gtin_barcode(self, code):
        return {
            'name': 'Get barcode',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/barcode/?type=Code128&humanreadable=1&value=' + code
        }

    @api.model
    def print_gtin_barcode(self, code, size='normal'):
        self.ensure_one()
        self.gtin = code
        ctx = dict(self.env.context or {}, active_ids=[self.id],
                   active_model='product.gtin')
        size = '_tiny' if size == 'tiny' else ''
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product_gtin_codes.gtin_barcode_report' + size,
            'context': ctx
        }

    @api.multi
    def action_get_gtin_barcode(self):
        bc_type = self.env.context.get('barcode_type')
        if bc_type == 'gtin12':
            return self.get_gtin_barcode(self.gtin12)
        if bc_type == 'gtin13':
            return self.get_gtin_barcode(self.gtin13)
        if bc_type == 'gtin14_1':
            return self.get_gtin_barcode(self.gtin14_1)
        if bc_type == 'gtin14_2':
            return self.get_gtin_barcode(self.gtin14_2)
        if bc_type == 'gtin14_3':
            return self.get_gtin_barcode(self.gtin14_3)
        if bc_type == 'gtin14_4':
            return self.get_gtin_barcode(self.gtin14_4)
        if bc_type == 'gtin14_5':
            return self.get_gtin_barcode(self.gtin14_5)
        if bc_type == 'gtin14_6':
            return self.get_gtin_barcode(self.gtin14_6)
        if bc_type == 'gtin14_7':
            return self.get_gtin_barcode(self.gtin14_7)
        if bc_type == 'gtin14_8':
            return self.get_gtin_barcode(self.gtin14_8)

    @api.multi
    def action_print_gtin_barcode(self):
        bc_type = self.env.context.get('barcode_type')
        size = self.env.context.get('barcode_size', 'normal')
        if bc_type == 'gtin12':
            return self.print_gtin_barcode(self.gtin12, size)
        if bc_type == 'gtin13':
            return self.print_gtin_barcode(self.gtin13, size)
        if bc_type == 'gtin14_1':
            return self.print_gtin_barcode(self.gtin14_1, size)
        if bc_type == 'gtin14_2':
            return self.print_gtin_barcode(self.gtin14_2, size)
        if bc_type == 'gtin14_3':
            return self.print_gtin_barcode(self.gtin14_3, size)
        if bc_type == 'gtin14_4':
            return self.print_gtin_barcode(self.gtin14_4, size)
        if bc_type == 'gtin14_5':
            return self.print_gtin_barcode(self.gtin14_5, size)
        if bc_type == 'gtin14_6':
            return self.print_gtin_barcode(self.gtin14_6, size)
        if bc_type == 'gtin14_7':
            return self.print_gtin_barcode(self.gtin14_7, size)
        if bc_type == 'gtin14_8':
            return self.print_gtin_barcode(self.gtin14_8, size)

    @api.multi
    def action_print_tiny_gtin_barcode(self):
        return self.with_context(barcode_size='tiny').\
            action_print_gtin_barcode()


class ProductGtin14(models.Model):
    _name = 'product.gtin14'
    _rec_name = 'gtin14'
    _order = 'log_var'

    product_id = fields.Many2one(comodel_name='product.product',
                                 ondelete='cascade', readonly=True)
    log_var = fields.Integer('Logistic variable', readonly=True)
    gtin14 = fields.Char('GTIN-14 code', readonly=True)
    units = fields.Float('Units')
    used_for = fields.Char('Used for')
    partner_ids = fields.Many2many(string='Assigned partners',
                                   comodel_name='res.partner',
                                   relation='product_gtin14_res_partner_rel',
                                   column1='gtin14_id',
                                   column2='partner_id')
    partners_count = fields.Integer(string='Partners',
                                    compute='_partners_count',
                                    readonly=True)

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = u'{} ({:f} uds) {}'.format(rec.gtin14, rec.units,
                                           rec.used_for if rec.used_for else '')
            res.append((rec.id, name))
        return res

    @api.one
    def _partners_count(self):
        self.partners_count = len(self.partner_ids)

    @api.multi
    def assign_partners(self):
        view = self.env.ref(
            'product_gtin_codes.product_gtin_codes_partners_form')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.gtin14',
            'res_id': self.id,
            'view_id': view.id,
            'target': 'new',
#            'flags': {'form': {'action_buttons': True}},
            'context': self.env.context,
        }

    @api.multi
    def action_get_gtin_barcode(self):
        self.ensure_one()
        return {
            'name': 'Get barcode',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/barcode/?type=Code128&humanreadable=1&value=' +
                   self.gtin14
        }

    @api.multi
    def action_print_gtin_barcode(self):
        self.ensure_one()
        gtin = self.env['product.gtin'].create({'gtin': self.gtin14})
        ctx = dict(self.env.context or {}, active_ids=[gtin.id],
                   active_model='product.gtin')
        size = self.env.context.get('barcode_size', 'normal')
        size = '_tiny' if size == 'tiny' else ''
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product_gtin_codes.gtin_barcode_report' + size,
            'context': ctx
        }

    @api.multi
    def action_print_tiny_gtin_barcode(self):
        return self.with_context(barcode_size='tiny').\
            action_print_gtin_barcode()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    gtin12 = fields.Char('GTIN-12', readonly=True)
    gtin13 = fields.Char('GTIN-13', related='ean13', readonly=True)
    gtin14_ids = fields.One2many(comodel_name='product.gtin14',
                                 inverse_name='product_id',
                                 string='GTIN-14 codes')
    gtin14_default = fields.Many2one(comodel_name='product.gtin14',
                                     string="Default GTIN14")
    gtin_asociado_01 = fields.Char(string='GTIN asociado 01')
    gtin_asociado_02 = fields.Char(string='GTIN asociado 02')

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res.compute_gtin_codes()
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        self.compute_gtin_codes()

        box_elements = vals.get('box_elements', False)
        if box_elements:
            for p in self:
                if p.gtin14_ids:
                    g = p.gtin14_ids.filtered(lambda r: r.log_var == 8)
                    g.units = box_elements
        return res

    @api.multi
    def compute_gtin_codes(self):
        def control_code(code):
            sum = 0
            for d in range(13):
                sum += int(code[d]) * (3 if d % 2 == 0 else 1)
            return (10 - sum % 10) % 10

        for p in self:
            if p.ean13 and len(p.ean13) == 13 and p.ean13.isnumeric():
                if p.ean13[:-1] != p.gtin12:
                    p.gtin12 = p.ean13[:-1]
                    l = []
                    if p.gtin14_ids:
                        for g in p.gtin14_ids:
                            code = str(g.log_var) + p.gtin12
                            code = code + str(control_code(code))
                            l.append((1, g.id, {
                                'gtin14': code
                            }))
                    else:
                        for i in range(1, 9):
                            code = str(i) + p.gtin12
                            code = code + str(control_code(code))
                            if i == 8:
                                l.append((0, 0, {
                                    'log_var': i,
                                    'gtin14': code,
                                    'units': p.box_elements,
                                    'used_for': _('Complete (Pharmadus)'),
                                }))
                            else:
                                l.append((0, 0, {
                                    'log_var': i,
                                    'gtin14': code,
                                }))
                    p.write({'gtin14_ids': l})

                    if not p.gtin14_default:
                        p.gtin14_default = \
                            p.gtin14_ids.filtered(lambda r: r.log_var == 8)
            elif p.gtin12:
                p.gtin12 = False
                p.gtin14_ids.unlink()
        return self

    @api.model
    def gtin14_partner_specific(self, partner_id):
        gtin14_id = self.gtin14_default
        if partner_id:
            if partner_id.type in ['delivery'] and partner_id.parent_id:
                partner_id = partner_id.parent_id
            for gtin_obj in self.gtin14_ids:
                for p in gtin_obj.partner_ids:
                    if p == partner_id:
                        gtin14_id = gtin_obj
        return gtin14_id

    @api.model
    def get_gtin_barcode(self, code):
        return {
            'name': 'Get barcode',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/barcode/?type=Code128&humanreadable=1&value=' + code
        }

    @api.model
    def print_gtin_barcode(self, code, size='normal'):
        gtin = self.env['product.gtin'].create({'gtin': code})
        ctx = dict(self.env.context or {}, active_ids=[gtin.id],
                   active_model='product.gtin')
        size = '_tiny' if size == 'tiny' else ''
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product_gtin_codes.gtin_barcode_report' + size,
            'context': ctx
        }

    @api.multi
    def action_get_gtin_barcode(self):
        self.ensure_one()
        bc_type = self.env.context.get('barcode_type')
        if bc_type == 'gtin12':
            return self.get_gtin_barcode(self.gtin12)
        if bc_type == 'gtin13':
            return self.get_gtin_barcode(self.gtin13)

    @api.multi
    def action_print_gtin_barcode(self):
        self.ensure_one()
        bc_type = self.env.context.get('barcode_type')
        size = self.env.context.get('barcode_size', 'normal')
        if bc_type == 'gtin12':
            return self.print_gtin_barcode(self.gtin12, size)
        if bc_type == 'gtin13':
            return self.print_gtin_barcode(self.gtin13, size)

    @api.multi
    def action_print_tiny_gtin_barcode(self):
        return self.with_context(barcode_size='tiny').\
            action_print_gtin_barcode()