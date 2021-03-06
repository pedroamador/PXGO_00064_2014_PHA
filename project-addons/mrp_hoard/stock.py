# -*- coding: utf-8 -*-
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
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from datetime import date


class StockMoveReturnOperations(models.Model):

    _name = 'stock.move.return.operations'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    qty = fields.Float('Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    move_id = fields.Many2one('stock.move', 'Move')
    production_id = fields.Many2one('mrp.production', 'Production')
    product_uom = fields.Many2one('product.uom', 'UoM')
    location_id = fields.Many2one('stock.location')
    """Informative fields"""
    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data",
                              digits=dp.get_precision(
                                   'Product Unit of Measure'))
    returned_qty = fields.Float('Returned qty', help="""Qty. of move that will
be returned on produce""", digits=dp.get_precision('Product Unit of Measure'))
    qty_used = fields.Float('Qty used',
                            digits=dp.get_precision('Product Unit of Measure'))
    qty_scrapped = fields.Float('Qty scrapped',
                                digits=dp.get_precision(
                                    'Product Unit of Measure'))
    initials = fields.Char('Initials')
    initials_return = fields.Char('Initials')
    initials_acond = fields.Char('Initials')
    used_lot = fields.Char('Use lot')

    """Fields of hoard used for return excess material"""
    hoard_served_qty = fields.Float('Served qty',
                                    help="Quality system field, no data",
                                    digits=dp.get_precision(
                                        'Product Unit of Measure'))
    hoard_returned_qty = fields.Float('Returned qty',
                                      help="""Qty. of move that will
be returned on produce""", digits=dp.get_precision('Product Unit of Measure'))
    hoard_initials = fields.Char('Initials')
    hoard_initials_return = fields.Char('Initials')
    acceptance_date = fields.Date('Acceptance date', readonly=True,
                                  related='lot_id.acceptance_date')

    @api.model
    def create(self, vals):
        """
            Se rellenan los campos que faltan con el lote
        """
        lot_id = int(vals.get('lot_id', False))
        lot = self.env['stock.production.lot'].browse(lot_id)
        if not vals.get('product_id', False):
            vals['product_id'] = lot.product_id.id
        if not vals.get('product_uom', False):
            vals['product_uom'] = lot.product_id.uom_id.id
        vals['lot_id'] = lot_id
        return super(StockMoveReturnOperations, self).create(vals)


class StockMove(models.Model):

    _inherit = 'stock.move'

    is_hoard_move = fields.Boolean('Is hoard move',
                                   compute='_get_is_hoard_move')
    original_move = fields.Many2one('stock.move', 'Original move')
    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'move_id', 'Return operations')
    return_production_move = fields.Boolean('return production move',
                                            copy=False)

    @api.one
    @api.depends('raw_material_production_id')
    def _get_is_hoard_move(self):
        self.is_hoard_move = self.move_dest_id and \
            self.move_dest_id.raw_material_production_id or False

    @api.multi
    def action_assign(self):
        """
            Se actualizan los registros de return operations unicamente si
            los movimientos corresponden a una produccion, o si es un acopio.
        """
        res = super(StockMove, self).action_assign()
        if self.env.context.get('no_return_operations', False):
            return res
        self.create_return_operations()
        return res

    def create_return_operations(self):
        q_lot_ids = []
        for move in self:
            if (move.move_dest_id and
                move.move_dest_id.raw_material_production_id):
                op_move = move
                if move.move_dest_id:
                    op_move = move.move_dest_id
                if op_move.return_operation_ids:
                    op_move.return_operation_ids.unlink()

                locations = move.reserved_quant_ids.mapped('location_id.id')
                for location in locations:
                    quants = self.env['stock.quant'].read_group(
                        [('reservation_id', '=', move.id), ('location_id', '=', location)], ['lot_id', 'qty',], ['lot_id'])
                    for quant in quants:
                        lot = quant['lot_id']
                        if lot:
                            q_lot_ids.append(lot[0])
                        operation = self.env['stock.move.return.operations'].search(
                            [('move_id', '=', op_move.id),
                             ('lot_id', '=', lot and lot[0] or False)])
                        operation_dict = {
                            'product_id': op_move.product_id.id,
                            'lot_id': lot and lot[0] or False,
                            'qty': quant['qty'],
                            'product_uom': move.product_uom.id,
                            'move_id': op_move.id,
                            'production_id': op_move.raw_material_production_id.id,
                            'location_id': location
                        }
                        self.env['stock.move.return.operations'].create(
                            operation_dict)


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    is_hoard = fields.Boolean('Is hoard', related='move_lines.is_hoard_move')
    accept_multiple_raw_material = fields.Boolean(
        related='move_lines.move_dest_id.raw_material_production_id.\
accept_multiple_raw_material')
    return_for_production = fields.Many2one('mrp.production')

    @api.multi
    def do_transfer(self):
        '''
            Se controla el uso de materias primas en acopios de producción.
        '''
        for picking in self:
            if picking.is_hoard and not picking.accept_multiple_raw_material:
#                if len(picking.mapped(
#                        'move_lines.product_id').filtered(lambda r: r.raw_material==True)) > 1:
#                    raise exceptions.Warning(
#                        _('Multiple raw material'),
#                        _('The route not accepts multiple raw material'))
                for move in picking.move_lines:
                    if move.product_id.raw_material:
                        if len(move.mapped('linked_move_operation_ids.operation_id.lot_id')) > 1:
                            raise exceptions.Warning(
                                _('Multiple lot'),
                                _('The production route only accepts one lot of raw material'))
        return super(StockPicking, self).do_transfer()

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for picking in self:
            if picking.is_hoard:
                lot_errors = []
                for lot in picking.mapped(
                        'move_lines.reserved_quant_ids.lot_id'):
                    if lot.alert_date and \
                            fields.Datetime.from_string(lot.alert_date).date() \
                            < date.today():
                        lot_errors.append(
                            'Fecha de alerta superada: %s  ->  %s' %
                            (lot.name, lot.product_id.name)
                        )
                    if lot.state == 'rejected':
                        lot_errors.append(
                            'Lote en estado rechazado: %s  ->  %s' %
                            (lot.name, lot.product_id.name)
                        )
                if lot_errors:
                    return self.env['custom.views.warning'].show_message(
                        'Mensajes de advertencia', '\n'.join(lot_errors)
                    )
        return res

    @api.model
    def _prepare_values_extra_move(self, op, product, remaining_qty):
        res = super(StockPicking, self)._prepare_values_extra_move(
            op=op, product=product, remaining_qty=remaining_qty)
        if op.picking_id.is_hoard:
            # en este momento solo debería de haber 1 movimiento
            # Pero puede haber varios links.
            move = op.mapped('linked_move_operation_ids.move_id')
            res['move_dest_id'] = move.move_dest_id.id
        return res

    @api.model
    def _create_extra_moves(self, picking):
        res = super(StockPicking, self)._create_extra_moves(picking)
        if res and picking.is_hoard:
            for move in self.env['stock.move'].browse(res):
                if move.move_dest_id:
                    move.move_dest_id.product_uom_qty += move.product_uom_qty
        return res


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.model
    def _quants_get_order(self, location, product, quantity, domain=[],
                          orderby='in_date'):
        '''
            Se controla la asignacion de materias primas para que no se asigne
            mas de un lote para materia prima en albaranes de acopio
            cuya ruta no tenga mezcladora.
            Si ya hay un lote en el domain, saltamos la comprobación.
        '''
        if 'lot_id' not in [x[0] for x in domain]:
            if product.raw_material:
                if self._context.get('active_model', False) == 'stock.picking':
                    picking = self.env['stock.picking'].browse(
                        self._context.get('active_id', False))
                    if picking.is_hoard and not \
                            picking.accept_multiple_raw_material:
                        custom_domain = domain
                        custom_domain += location and [
                            ('location_id', 'child_of', location.id)] or []
                        custom_domain += [('product_id', '=', product.id)]
                        if self._context.get('force_company'):
                            custom_domain += [
                                ('company_id', '=',
                                 self._context.get('force_company'))]
                        else:
                            custom_domain += [
                                ('company_id', '=',
                                 self.env.user.company_id.id)]
                        available_quants = self.env['stock.quant'].search(
                            custom_domain)
                        lots = {}
                        for quant in available_quants:
                            if quant.lot_id.id not in lots:
                                lots[quant.lot_id.id] = 0.0
                            lots[quant.lot_id.id] += quant.qty
                        available_lots = []
                        for lot in lots.keys():
                            if lots[lot] >= quantity:
                                available_lots.append(lot)
                        domain.append(['lot_id', 'in', available_lots])
        return super(StockQuant, self)._quants_get_order(location, product,
                                                         quantity, domain,
                                                         orderby)
