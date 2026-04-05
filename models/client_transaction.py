from odoo import models, fields, api
from odoo.exceptions import ValidationError

class OfficeClientTransaction(models.Model):
    _name = 'office.client.transaction'
    _description = 'Client Transaction'
    _order = 'date desc, id desc'

    client_id = fields.Many2one('office.client', string='Client', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    name = fields.Char(string='Description', required=True)
    transaction_type = fields.Selection([
        ('invoice', 'Invoice'),
        ('return', 'Return (إشعار مرتجع)'),
        ('payment', 'Payment'),
        ('adjustment', 'Adjustment/Gift (تسوية/عيدية)'),
        ('opening_balance', 'Opening Balance (رصيد أول المدة)')
    ], string='Type', required=True, default='invoice')

    amount = fields.Float(string='Amount', compute='_compute_amount', store=True, readonly=False)
    discount_percentage = fields.Float(string='Discount (%)', compute='_compute_discount_percentage', store=True, readonly=False)
    
    # Split Discount Amounts
    office_discount_amount = fields.Float(string='Office Discount', compute='_compute_discount_amounts', store=True)
    perfume_discount_amount = fields.Float(string='Perfume Discount', compute='_compute_discount_amounts', store=True)
    eclador_discount_amount = fields.Float(string='Eclador Discount', compute='_compute_discount_amounts', store=True)
    total_discount_amount = fields.Float(string='Total Discount', compute='_compute_discount_amounts', store=True)
    
    net_amount = fields.Float(string='Net Amount', compute='_compute_net_amount', store=True)

    line_ids = fields.One2many('office.client.transaction.line', 'transaction_id', string='Invoice Lines')
    total_office_profit = fields.Float(string='Total Office Profit', compute='_compute_totals', store=True)
    total_factory_share = fields.Float(string='Total Factory Share', compute='_compute_totals', store=True)

    @api.depends('line_ids.subtotal', 'transaction_type')
    def _compute_amount(self):
        for record in self:
            if record.transaction_type in ('invoice', 'return'):
                record.amount = abs(sum(record.line_ids.mapped('subtotal')))
            else:
                record.amount = record.amount or 0.0

    @api.depends('client_id.discount_type', 'client_id.yearly_discount_percentage', 'transaction_type')
    def _compute_discount_percentage(self):
        for record in self:
            if record.transaction_type in ('invoice', 'return') and record.client_id.discount_type == 'per_invoice':
                record.discount_percentage = record.client_id.yearly_discount_percentage
            else:
                record.discount_percentage = 0.0

    @api.depends(
        'transaction_type', 'amount', 'client_id.discount_type',
        'client_id.discount_office_percentage',
        'client_id.discount_perfume_percentage',
        'client_id.discount_eclador_percentage',
        'line_ids.subtotal', 'line_ids.factory_type'
    )
    def _compute_discount_amounts(self):
        for record in self:
            if record.transaction_type in ('invoice', 'return') and record.client_id.discount_type == 'per_invoice':
                # Office discount is applied on the total invoice amount
                record.office_discount_amount = record.amount * (record.client_id.discount_office_percentage / 100.0)
                
                # Factory discounts applied to their respective subtotals
                perfume_total = abs(sum(record.line_ids.filtered(lambda l: l.factory_type == 'perfume').mapped('subtotal')))
                eclador_total = abs(sum(record.line_ids.filtered(lambda l: l.factory_type == 'eclador').mapped('subtotal')))
                
                record.perfume_discount_amount = perfume_total * (record.client_id.discount_perfume_percentage / 100.0)
                record.eclador_discount_amount = eclador_total * (record.client_id.discount_eclador_percentage / 100.0)
                
                record.total_discount_amount = record.office_discount_amount + record.perfume_discount_amount + record.eclador_discount_amount
            elif record.transaction_type in ('invoice', 'return') and record.discount_percentage > 0:
                # Fallback for manual discount percentage entry
                record.total_discount_amount = record.amount * (record.discount_percentage / 100.0)
                record.office_discount_amount = record.total_discount_amount
                record.perfume_discount_amount = 0.0
                record.eclador_discount_amount = 0.0
            else:
                record.office_discount_amount = 0.0
                record.perfume_discount_amount = 0.0
                record.eclador_discount_amount = 0.0
                record.total_discount_amount = 0.0

    @api.depends('line_ids.office_profit', 'line_ids.factory_share', 'office_discount_amount', 'perfume_discount_amount', 'eclador_discount_amount', 'transaction_type')
    def _compute_totals(self):
        for record in self:
            if record.transaction_type in ('invoice', 'return'):
                base_office_profit = abs(sum(record.line_ids.mapped('office_profit')))
                base_factory_share = abs(sum(record.line_ids.mapped('factory_share')))
                
                # Office discount reduces office profit
                record.total_office_profit = base_office_profit - record.office_discount_amount
                # Factory discounts reduce factory share
                record.total_factory_share = base_factory_share - (record.perfume_discount_amount + record.eclador_discount_amount)
            else:
                record.total_office_profit = 0.0
                record.total_factory_share = 0.0

    @api.depends('amount', 'total_discount_amount', 'transaction_type')
    def _compute_net_amount(self):
        for record in self:
            if record.transaction_type in ('invoice', 'return'):
                record.net_amount = record.amount - record.total_discount_amount
            elif record.transaction_type in ('payment', 'adjustment', 'opening_balance'):
                record.net_amount = record.amount

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Amount must be strictly positive.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('transaction_type') in ('invoice', 'return', 'adjustment', 'opening_balance'):
                if not self.env.user.has_group('office_client_cards.group_office_client_manager'):
                    raise ValidationError("Only Managers are allowed to create Invoices, Returns, Adjustments, or Opening Balances.")
        return super(OfficeClientTransaction, self).create(vals_list)

    def write(self, vals):
        if 'transaction_type' in vals and vals['transaction_type'] in ('invoice', 'return', 'adjustment', 'opening_balance'):
            if not self.env.user.has_group('office_client_cards.group_office_client_manager'):
                raise ValidationError("Only Managers are allowed to change type to Invoice, Return, Adjustment, or Opening Balance.")
        return super(OfficeClientTransaction, self).write(vals)
