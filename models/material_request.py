# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import AccessError


class MaterialRequest(models.Model):
    """Create a model for material request"""
    _name = 'material.request'
    _description = 'Material Request'

    name = fields.Char(string='Request Name', required=True,
                       default=lambda self: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True,
                                  default=lambda self:
                                  self.env.user.employee_id.id)
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager_approved', 'Manager Approved'),
        ('head_approved', 'Head Approved'),
        ('confirm', 'Confirm'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', required=True)
    product_lines_ids = fields.One2many('material.request.line',
                                        'request_id',
                                        string='Products')
    purchase_count = fields.Integer(string='Purchase Count',
                                    compute='get_purchase_count')
    transfer_count = fields.Integer(string='Transfer Count',
                                    compute='get_transfer_count')

    def create_purchase_orders_for_product_vendors(self):
        """Create a function for create rfq in the product vendors"""
        vendor_lines = defaultdict(lambda: defaultdict(int))

        for line in self.product_lines_ids.filtered(
                lambda line: line.source_type == 'purchase'):
            product = line.product_id
            vendor_info = product.seller_ids

            for vendor in vendor_info:
                vendor_name = vendor.partner_id.name
                vendor_lines[vendor_name][product.id] += line.quantity

        for vendor_name, products in vendor_lines.items():
            vendor = self.env['res.partner'].search(
                [('name', '=', vendor_name)], limit=1)
            if vendor:
                purchase_order = self.env['purchase.order'].create({
                    'partner_id': vendor.id,
                    'origin': self.name,
                })

                order_lines = []
                for product_id, quantity in products.items():
                    order_lines.append(fields.Command.create({
                        'product_id': product_id,
                        'name': self.env['product.product'].browse(
                            product_id).name,
                        'product_qty': quantity,
                    }))

                purchase_order.order_line = order_lines
                purchase_order.button_confirm()

    def create_internal_transfers(self):
        """create an internal transfer for different locations"""
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        for record in self:
            internal_lines = record.product_lines_ids.filtered(
                lambda line: line.source_type == 'internal')
            if internal_lines:
                picking_vals = {
                    'picking_type_id': self.env.ref(
                        'stock.picking_type_internal').id,
                    'origin': self.name,
                    'location_id': internal_lines[0].location_from_id.id,
                    'location_dest_id': internal_lines[0].location_to_id.id,
                }
                picking = StockPicking.create(picking_vals)

                for lines in internal_lines:
                    product_id = lines.product_id.id
                    quantity = lines.quantity
                    move_vals = {
                        'picking_id': picking.id,
                        'product_id': product_id,
                        'product_uom_qty': quantity,
                        'name': lines.product_id.name,
                        'location_id': lines.location_from_id.id,
                        'location_dest_id': lines.location_to_id.id,
                    }
                    StockMove.create(move_vals)

                picking.action_confirm()

    @api.model
    def create(self, vals):
        """create a sequence for material request"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'material.request') or _('New')
        res = super(MaterialRequest, self).create(vals)
        return res

    def get_purchase_orders(self):
        """this function has working in purchases smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchased',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('origin', '=', self.name)],
            'context': "{'create': False}"
        }

    def get_internal_transfer(self):
        """this function has working in transfers smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
            'context': "{'create': False}"
        }

    def action_submit(self):
        """This function has working in submit button click only users can
        submit the request"""
        self.ensure_one()
        if self.env.user.has_group('material_request.material_user_access'):
            self.state = 'submitted'
        else:
            raise AccessError(
                'You are not authorized to Submit this material request.')


    def action_manager_approve(self):
        """This function has working in Manager Approval button click
        only Managers group can Approve"""
        self.ensure_one()
        if self.env.user.has_group('material_request.material_manager_access'):
            self.state = 'manager_approved'
        else:
            raise AccessError(
                'You are not authorized to Approve this material request.')

    def action_head_approve(self):
        """This function has working in Head Approval button click
        only Managers group can Approve"""
        self.ensure_one()
        if self.env.user.has_group('material_request.material_head_access'):
            self.state = 'head_approved'
        else:
            raise AccessError(
                'You are not authorized to Approve this material request.')

    def action_reject(self):
        """This function has working in Head Reject button click only
        Managers group can Approve"""
        self.ensure_one()
        if self.env.user.has_group('material_request.material_head_access'):
            self.state = 'rejected'
        else:
            raise AccessError(
                'You are not authorized to reject this material request.')

    def action_confirm(self):
        """this function has working in cancel button click"""
        self.ensure_one()
        if self.env.user.has_group('material_request.material_user_access'):
            self.state = 'confirm'
            self.create_purchase_orders_for_product_vendors()
            self.create_internal_transfers()
        else:
            raise AccessError(
                'You are not authorized to confirm this material request.')

    def action_draft(self):
        """this function has working in draft button click"""
        for record in self:
            record.state = 'draft'

    def get_purchase_count(self):
        """In this function has working calculating count of
        purchases based on source document"""
        for record in self:
            record.purchase_count = self.env['purchase.order'].search_count(
                [('origin', '=', self.name)])
            return record.purchase_count

    def get_transfer_count(self):
        """In this function has working calculating count of
        transfers based on source document"""
        for record in self:
            record.transfer_count = self.env['stock.picking'].search_count(
                [('origin', '=', self.name)])
            return record.transfer_count
