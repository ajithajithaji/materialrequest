# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _description = 'Material Request Line'

    product_id = fields.Many2one('product.product',
                                 string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    request_id = fields.Many2one('material.request',
                                 string='Material Request',
                                 readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Vendors')
    source_type = fields.Selection(
        [('purchase', 'Purchase Order'),
         ('internal', 'Internal Transfer')], string='Source Type',
        required=True)
    location_from_id = fields.Many2one('stock.location',
                                       string='From Location',
                                       domain="[('usage', '=', 'internal')]",
                                       default=1)
    location_to_id = fields.Many2one('stock.location',
                                     string='To Location',
                                     domain="[('usage', '=', 'internal')]",
                                     default=2)

    @api.onchange('source_type')
    def _onchange_source_type(self):
        """This Function Has working for source type is purchase the use cannot
        be chosen from and to locations"""
        if self.source_type == 'purchase':
            self.location_from_id = False
            self.location_to_id = False
