from odoo import models, fields, api

class OfficeFactory(models.Model):
    _name = 'office.factory'
    _description = 'Factory Ledger'
    
    name = fields.Char(string='Factory Name', required=True)
    factory_type = fields.Selection([
        ('perfume', 'Perfume Factory (مصنع البرفان)'),
        ('eclador', 'Eclador Factory (مصنع الاكلادور)')
    ], string='Factory Type', required=True, unique=True)
    
    payment_ids = fields.One2many('office.factory.payment', 'factory_id', string='Payments (المسدد)')
    
    total_factory_debt = fields.Float(string='Remaining Debt (المتبقي)', compute='_compute_factory_debt', store=False)
    total_factory_invoices = fields.Float(string='Total Shares (اجمالي المستحقات)', compute='_compute_factory_debt', store=False)
    total_factory_returns = fields.Float(string='Total Returns (إجمالي المرتجعات)', compute='_compute_factory_debt', store=False)
    total_factory_payments = fields.Float(string='Total Paid (إجمالي المسدد)', compute='_compute_factory_debt', store=False)

    def _compute_factory_debt(self):
        for factory in self:
            # 1. Get all transactions impacting this factory
            transactions = self.env['office.client.transaction'].search([
                ('transaction_type', 'in', ('invoice', 'return'))
            ])
            
            # 2. Sum up shares based on factory type
            invoices = transactions.filtered(lambda t: t.transaction_type == 'invoice')
            returns = transactions.filtered(lambda t: t.transaction_type == 'return')
            
            invoices_total = 0.0
            returns_total = 0.0
            
            if factory.factory_type == 'perfume':
                invoices_total = sum(invoices.mapped('total_perfume_share'))
                returns_total = sum(returns.mapped('total_perfume_share'))
            elif factory.factory_type == 'eclador':
                invoices_total = sum(invoices.mapped('total_eclador_share'))
                returns_total = sum(returns.mapped('total_eclador_share'))
                
            payments_total = sum(factory.payment_ids.mapped('amount'))
            
            factory.total_factory_invoices = invoices_total
            factory.total_factory_returns = returns_total
            factory.total_factory_payments = payments_total
            
            factory.total_factory_debt = invoices_total - returns_total - payments_total

class OfficeFactoryPayment(models.Model):
    _name = 'office.factory.payment'
    _description = 'Factory Payment'
    _order = 'date desc, id desc'

    factory_id = fields.Many2one('office.factory', string='Factory', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)
