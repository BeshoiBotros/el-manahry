from odoo import models, fields, tools


class OfficeProfitReport(models.Model):
    _name = 'office.profit.report'
    _description = 'Office Profit Report'
    _auto = False

    year = fields.Char(string='Year', readonly=True)
    month = fields.Char(string='Month (YYYY-MM)', readonly=True)

    # Income side (from invoice transaction lines)
    total_invoices = fields.Float(string='Total Invoiced', readonly=True)
    total_office_profit = fields.Float(string='Office Gross Profit (ربح المكتب الإجمالي)', readonly=True)
    total_factory_share = fields.Float(string='Factory Share (حصة المصانع)', readonly=True)

    # Expense side (from office.expense)
    labor_expenses = fields.Float(string='Labor / عمالة', readonly=True)
    server_expenses = fields.Float(string='Server / سيرفر', readonly=True)
    porter_expenses = fields.Float(string='Porters / شيالين', readonly=True)
    transport_expenses = fields.Float(string='Transport / نقل', readonly=True)
    other_expenses = fields.Float(string='Other / أخرى', readonly=True)
    total_expenses = fields.Float(string='Total Expenses (إجمالي المصروفات)', readonly=True)

    # Net profit
    net_profit = fields.Float(string='Net Profit (صافي الربح)', readonly=True)

    factory_payments = fields.Float(string='Paid to Factory (المورد للمصانع)', readonly=True)
    net_factory_share = fields.Float(string='Net Factory Share (المتبقي للمصانع)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
            CREATE OR REPLACE VIEW {table} AS (
                SELECT
                    row_number() OVER () AS id,
                    COALESCE(inv.year, COALESCE(exp.year, fpay.year))    AS year,
                    COALESCE(inv.month, COALESCE(exp.month, fpay.month))  AS month,

                    COALESCE(inv.total_invoices, 0)       AS total_invoices,
                    COALESCE(inv.total_office_profit, 0)  AS total_office_profit,
                    COALESCE(inv.total_factory_share, 0)  AS total_factory_share,

                    COALESCE(exp.labor, 0)      AS labor_expenses,
                    COALESCE(exp.server, 0)     AS server_expenses,
                    COALESCE(exp.porter, 0)     AS porter_expenses,
                    COALESCE(exp.transport, 0)  AS transport_expenses,
                    COALESCE(exp.other, 0)      AS other_expenses,
                    COALESCE(exp.total, 0)      AS total_expenses,
                    
                    COALESCE(fpay.total_payments, 0) AS factory_payments,

                    COALESCE(inv.total_office_profit, 0) - COALESCE(exp.total, 0) AS net_profit,
                    COALESCE(inv.total_factory_share, 0) - COALESCE(fpay.total_payments, 0) AS net_factory_share

                FROM (
                    -- Aggregate invoice and return line profits per month
                    SELECT
                        to_char(t.date, 'YYYY')    AS year,
                        to_char(t.date, 'YYYY-MM') AS month,
                        SUM(CASE WHEN t.transaction_type = 'return' THEN -l.subtotal ELSE l.subtotal END) AS total_invoices,
                        SUM(CASE WHEN t.transaction_type = 'return' THEN -l.office_profit ELSE l.office_profit END) AS total_office_profit,
                        SUM(CASE WHEN t.transaction_type = 'return' THEN -l.factory_share ELSE l.factory_share END) AS total_factory_share
                    FROM office_client_transaction t
                    JOIN office_client_transaction_line l ON l.transaction_id = t.id
                    WHERE t.transaction_type IN ('invoice', 'return')
                    GROUP BY
                        to_char(t.date, 'YYYY'),
                        to_char(t.date, 'YYYY-MM')
                ) inv

                FULL OUTER JOIN (
                    -- Aggregate expenses per month, split by type
                    SELECT
                        to_char(date, 'YYYY')    AS year,
                        to_char(date, 'YYYY-MM') AS month,
                        SUM(CASE WHEN expense_type = 'labor'     THEN amount ELSE 0 END) AS labor,
                        SUM(CASE WHEN expense_type = 'server'    THEN amount ELSE 0 END) AS server,
                        SUM(CASE WHEN expense_type = 'porter'    THEN amount ELSE 0 END) AS porter,
                        SUM(CASE WHEN expense_type = 'transport' THEN amount ELSE 0 END) AS transport,
                        SUM(CASE WHEN expense_type = 'other'     THEN amount ELSE 0 END) AS other,
                        SUM(amount)                                                      AS total
                    FROM office_expense
                    GROUP BY
                        to_char(date, 'YYYY'),
                        to_char(date, 'YYYY-MM')
                ) exp ON exp.month = inv.month
                
                FULL OUTER JOIN (
                    -- Aggregate Factory Payments
                    SELECT
                        to_char(date, 'YYYY')    AS year,
                        to_char(date, 'YYYY-MM') AS month,
                        SUM(amount)              AS total_payments
                    FROM office_factory_payment
                    GROUP BY
                        to_char(date, 'YYYY'),
                        to_char(date, 'YYYY-MM')
                ) fpay ON fpay.month = COALESCE(inv.month, exp.month)
            )
        """.format(table=self._table)
        self.env.cr.execute(sql)
