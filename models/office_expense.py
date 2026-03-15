from odoo import models, fields, api


class OfficeExpense(models.Model):
    _name = 'office.expense'
    _description = 'Office Expense'
    _order = 'date desc, id desc'

    name = fields.Char(string='Description (وصف المصروف)', required=True)
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True
    )
    expense_type = fields.Selection([
        ('labor',     'Labor / عمالة'),
        ('server',    'Server Costs / مصروفات سيرفر'),
        ('porter',    'Porters / شيالين'),
        ('transport', 'Transport / نقل منتجات'),
        ('other',     'Other / أخرى'),
    ], string='Expense Type', required=True, default='other')

    amount = fields.Float(string='Amount', required=True)
    notes = fields.Text(string='Notes')

    # Convenience computed fields for grouping
    month = fields.Char(
        string='Month',
        compute='_compute_period',
        store=True
    )
    year = fields.Char(
        string='Year',
        compute='_compute_period',
        store=True
    )

    @api.depends('date')
    def _compute_period(self):
        for rec in self:
            if rec.date:
                rec.year = str(rec.date.year)
                rec.month = rec.date.strftime('%Y-%m')
            else:
                rec.year = False
                rec.month = False
