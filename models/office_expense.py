from odoo import models, fields, api


class OfficeExpense(models.Model):
    _name = 'office.expense'
    _description = 'مصروف المكتب'
    _order = 'date desc, id desc'

    name = fields.Char(string='Description (وصف المصروف)', required=True)
    date = fields.Date(
        string='التاريخ',
        default=fields.Date.context_today,
        required=True
    )
    expense_type = fields.Selection([
        ('labor',     'العمالة'),
        ('server',    'Server Costs / مصروفات سيرفر'),
        ('porter',    'الشيالين'),
        ('transport', 'Transport / نقل منتجات'),
        ('other',     'أخرى'),
    ], string='نوع المصروف', required=True, default='other')

    amount = fields.Float(string='القيمة', required=True)
    notes = fields.Text(string='ملاحظات')

    # Convenience computed fields for grouping
    month = fields.Char(
        string='Month',
        compute='_compute_period',
        store=True
    )
    year = fields.Char(
        string='السنة',
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
