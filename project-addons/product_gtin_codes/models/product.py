# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class ProductGtin14(models.Model):
    _name = 'product.gtin14'
    _rec_name = 'gtin14'
    _order = 'log_var'

    product_id = fields.Many2one(comodel_name='product.product',
                                 ondelete='cascade')
    log_var = fields.Integer('Logistic variable')
    gtin14 = fields.Char('GTIN-14 code', readonly=True)
    units = fields.Integer('Units')
    used_for = fields.Char('Used for')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    gtin12 = fields.Char('GTIN-12', readonly=True)
    gtin13 = fields.Char('GTIN-13', related='ean13', readonly=True)
    gtin14_ids = fields.One2many(comodel_name='product.gtin14',
                                 inverse_name='product_id',
                                 string='GTIN-14 codes')

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
            elif p.gtin12:
                p.gtin12 = False
                p.gtin14_ids.unlink()

        return self