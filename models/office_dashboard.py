from odoo import models, fields, api
from datetime import date

class OfficeDashboard(models.TransientModel):
    _name = 'office.dashboard'
    _description = 'Manager Dashboard'

    name = fields.Char(default='Manager Dashboard (الرئيسية)')
    
    total_market_debt = fields.Float(string='Total Market Debt (إجمالي الديون بالسوق)', compute='_compute_stats')
    total_monthly_profit = fields.Float(string='Monthly Profit (ربح الشهر)', compute='_compute_stats')
    total_monthly_collections = fields.Float(string='Monthly Collections (تحصيلات الشهر)', compute='_compute_stats')
    
    total_factory_debt = fields.Float(string='Owed to Factories (مستحقات المصانع)', compute='_compute_stats')

    def _compute_stats(self):
        for record in self:
            # 1. Total Debt in Market
            clients = self.env['office.client'].search([])
            record.total_market_debt = sum(clients.mapped('total_debt'))

            # 2. Monthly Profit & Collections
            today = date.today()
            first_day_of_month = today.replace(day=1)
            transactions = self.env['office.client.transaction'].search([
                ('date', '>=', first_day_of_month)
            ])
            # Only count actual invoices and returns for profit
            record.total_monthly_profit = sum(transactions.mapped('total_office_profit'))
            
            payments = transactions.filtered(lambda t: t.transaction_type == 'payment')
            record.total_monthly_collections = sum(payments.mapped('net_amount'))
            
            # 3. Factory Debt
            factories = self.env['office.factory'].search([])
            # To compute fields not stored, we read the computed field
            record.total_factory_debt = sum(f.total_factory_debt for f in factories)
