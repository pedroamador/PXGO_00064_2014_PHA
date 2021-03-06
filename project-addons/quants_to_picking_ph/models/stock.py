# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    def action_quants_to_picking(self):
        company_id = self.env.user.company_id
        company_picking_type = {
            1: self.env.ref('stock.picking_type_internal'),       # Pharmadus
            6: self.env.ref('__export__.stock_picking_type_11'),  # Maricielo
            5: self.env.ref('__export__.stock_picking_type_16'),  # Seal
            7: self.env.ref('__export__.stock_picking_type_21')   # Marbemsa
        }
        picking_type =  company_picking_type.get(company_id.id, False)

        location_dest_id = company_id.internal_transit_location_id
        picking = self.env['stock.picking'].create({
            'invoice_state': 'none',
            'move_type': 'direct',
            'picking_type_id': picking_type.id,
            'state': 'draft'
        })

        # Create moves from selected quants
        moves = self.env['stock.move']
        for quant in self:
            moves.create({
                'invoice_state': 'none',
                'location_dest_id': location_dest_id.id,
                'location_id': quant.location_id.id,
                'name': quant.product_id.name,
                'picking_id': picking.id,
                'picking_type_id': picking_type.id,
                'procure_method': 'make_to_stock',
                'product_id': quant.product_id.id,
                'product_uom': quant.product_id.uom_id.id,
                'product_uom_qty': quant.qty,
                'state': 'draft',
                'restrict_lot_id': quant.lot_id.id,
            })

        # Returns the new created picking
        return {
            'picking_id': picking.id,
            'location_dest_id': location_dest_id.id
        }

    @api.multi
    def action_group_in_the_same_picking(self):
        picking_id = self.mapped('reservation_picking_id')
        if len(picking_id) != 1:
            raise exceptions.Warning(_('Operación no permitida'),
                                     _('Debe escoger un grupo de quants en los '
                                       'que las reservas sean todas de un mismo'
                                       ' albarán.'))
        # Create movements
        sample_move_id = self.mapped('reservation_id')[0]
        for quant_id in self:
            if not quant_id.reservation_picking_id:
                move_id = sample_move_id.copy()
                move_id.write({
                    'name': quant_id.product_id.name,
                    'product_id': quant_id.product_id.id,
                    'product_uom': quant_id.product_id.uom_id.id,
                    'product_uom_qty': quant_id.qty,
                    'state': 'draft',
                    'restrict_lot_id': quant_id.lot_id.id,
                })
        # Returns the new created picking
        return {'picking_id': picking_id.id}
