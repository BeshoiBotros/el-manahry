from odoo import models, fields, api

class OfficeClient(models.Model):
    _name = 'office.client'
    _description = 'Office Client'
    
    name = fields.Char(string='Client Name', required=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    
    discount_type = fields.Selection([
        ('none', 'No Discount'),
        ('yearly', 'Yearly Discount'),
        ('per_invoice', 'Per Invoice Discount')
    ], string='Discount Type', default='none', required=True)
    
    user_id = fields.Many2one('res.users', string='Salesperson (المندوب)', default=lambda self: self.env.user)

    # Total discount % agreed with the client (manually entered, e.g. 6%)
    yearly_discount_percentage = fields.Float(
        string='Total Discount (%)',
        help='The total discount percentage agreed with the client (e.g. 6%). Applies to both Yearly and Per Invoice.'
    )

    # --- Sub-percentages, each applied to a DIFFERENT base ---
    # Office portion
    discount_office_percentage = fields.Float(
        string='Office Discount (%)',
        help='The percentage borne by the Office (applied to total amount)'
    )
    # Perfume factory portion
    discount_perfume_percentage = fields.Float(
        string='Perfume Factory Discount (%)',
        help='The percentage borne by Perfume Factory (applied to perfume amount)'
    )
    # Eclador factory portion
    discount_eclador_percentage = fields.Float(
        string='Eclador Factory Discount (%)',
        help='The percentage borne by Eclador Factory (applied to eclador amount)'
    )

    transaction_ids = fields.One2many('office.client.transaction', 'client_id', string='Transactions')
    
    total_debt = fields.Float(string='Total Debt', compute='_compute_total_debt', store=True)
    
    # --- Yearly Stats (current year) ---
    current_year_collections_total = fields.Float(
        string='Current Year Collections',
        compute='_compute_yearly_stats', store=True
    )
    # Office pays this amount from their own share
    current_year_office_discount = fields.Float(
        string='Office Discount Amount (المكتب يدفع)',
        compute='_compute_yearly_stats', store=True
    )
    # Perfume factory owes this to the office
    yearly_perfume_invoices_total = fields.Float(
        string='Perfume Factory Annual Invoices',
        compute='_compute_yearly_stats', store=True
    )
    yearly_perfume_discount_owed = fields.Float(
        string='Perfume Discount Owed to Office (البرفان يدين المكتب)',
        compute='_compute_yearly_stats', store=True
    )
    # Eclador factory owes this to the office
    yearly_eclador_invoices_total = fields.Float(
        string='Eclador Factory Annual Invoices',
        compute='_compute_yearly_stats', store=True
    )
    yearly_eclador_discount_owed = fields.Float(
        string='Eclador Discount Owed to Office (الأكلادور يدين المكتب)',
        compute='_compute_yearly_stats', store=True
    )
    # Total discount earned by client = office_discount + perfume_discount + eclador_discount
    current_year_discount_earned = fields.Float(
        string='Total Earned Yearly Discount',
        compute='_compute_yearly_stats', store=True
    )

    # ---------------------------------------------------------------

    @api.depends('transaction_ids.net_amount', 'transaction_ids.transaction_type')
    def _compute_total_debt(self):
        for client in self:
            debt = 0.0
            for transaction in client.transaction_ids:
                if transaction.transaction_type in ('invoice', 'opening_balance'):
                    debt += transaction.net_amount
                elif transaction.transaction_type in ('payment', 'return', 'adjustment'):
                    debt -= transaction.net_amount
            client.total_debt = debt

    @api.depends(
        'transaction_ids.amount',
        'transaction_ids.transaction_type',
        'transaction_ids.date',
        'transaction_ids.line_ids.subtotal',
        'transaction_ids.line_ids.factory_type',
        'discount_type',
        'discount_office_percentage',
        'discount_perfume_percentage',
        'discount_eclador_percentage',
    )
    def _compute_yearly_stats(self):
        for client in self:
            current_year = fields.Date.today().year

            # --- Collections (payments) ---
            yearly_payments = client.transaction_ids.filtered(
                lambda t: t.transaction_type == 'payment'
                and t.date and t.date.year == current_year
            )
            total_collected = sum(yearly_payments.mapped('amount'))
            client.current_year_collections_total = total_collected

            if client.discount_type == 'yearly':
                # Office portion: applied to total collections
                office_discount = total_collected * (client.discount_office_percentage / 100.0)

                # Per-factory portions: applied to each factory's annual invoice subtotals MINUS returns
                yearly_transactions = client.transaction_ids.filtered(
                    lambda t: t.transaction_type in ('invoice', 'return')
                    and t.date and t.date.year == current_year
                )
                
                all_lines = yearly_transactions.mapped('line_ids')

                perfume_total = sum(all_lines.filtered(lambda l: l.factory_type == 'perfume').mapped('subtotal'))
                perfume_discount = perfume_total * (client.discount_perfume_percentage / 100.0)

                eclador_total = sum(all_lines.filtered(lambda l: l.factory_type == 'eclador').mapped('subtotal'))
                eclador_discount = eclador_total * (client.discount_eclador_percentage / 100.0)

                client.current_year_office_discount = office_discount
                client.yearly_perfume_invoices_total = perfume_total
                client.yearly_perfume_discount_owed = perfume_discount
                client.yearly_eclador_invoices_total = eclador_total
                client.yearly_eclador_discount_owed = eclador_discount
                client.current_year_discount_earned = (
                    office_discount + perfume_discount + eclador_discount
                )
            else:
                client.current_year_office_discount = 0.0
                client.yearly_perfume_invoices_total = 0.0
                client.yearly_perfume_discount_owed = 0.0
                client.yearly_eclador_invoices_total = 0.0
                client.yearly_eclador_discount_owed = 0.0
                client.current_year_discount_earned = 0.0
