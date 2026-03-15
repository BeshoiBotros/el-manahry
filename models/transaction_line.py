from odoo import models, fields, api

class OfficeClientTransactionLine(models.Model):
    _name = 'office.client.transaction.line'
    _description = 'Transaction Line'
    
    transaction_id = fields.Many2one('office.client.transaction', string='Transaction', required=True, ondelete='cascade')
    transaction_date = fields.Date(related='transaction_id.date', store=True, string='Transaction Date')
    transaction_type = fields.Selection(related='transaction_id.transaction_type', store=True, string='Transaction Type')
    
    product_id = fields.Many2one('office.product', string='Product', required=True)
    factory_type = fields.Selection(related='product_id.factory_type', store=True, string='Factory Type')
    
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts', store=True)
    office_profit = fields.Float(string='Office Profit', compute='_compute_amounts', store=True)
    factory_share = fields.Float(string='Factory Share', compute='_compute_amounts', store=True)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price
    
    @api.depends('quantity', 'price_unit', 'product_id.profit_type', 'product_id.profit_value', 'transaction_type')
    def _compute_amounts(self):
        for line in self:
            base_subtotal = line.quantity * line.price_unit
            
            profit = 0.0
            if line.product_id:
                if line.product_id.profit_type == 'percentage':
                    profit = base_subtotal * (line.product_id.profit_value / 100.0)
                elif line.product_id.profit_type == 'fixed':
                    profit = line.quantity * line.product_id.profit_value
                    
            base_factory_share = base_subtotal - profit
            
            # Apply sign based on transaction type
            multiplier = -1 if line.transaction_type == 'return' else 1
            
            line.subtotal = base_subtotal * multiplier
            line.office_profit = profit * multiplier
            line.factory_share = base_factory_share * multiplier
