from odoo import models, fields, tools


class OfficeYearlyDiscountReport(models.Model):
    _name = 'office.yearly.discount.report'
    _description = 'Yearly Discount Report (Split by Factory)'
    _auto = False

    client_id = fields.Many2one('office.client', string='العميل', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    year = fields.Char(string='السنة', readonly=True)

    # The overall agreed discount percentage (e.g., 6%)
    yearly_discount_percentage = fields.Float(string='إجمالي الخصم (%)', readonly=True)

    # Sub-percentages — stored on the client
    discount_office_percentage = fields.Float(string='Office %', readonly=True)
    discount_perfume_percentage = fields.Float(string='Perfume %', readonly=True)
    discount_eclador_percentage = fields.Float(string='Eclador %', readonly=True)

    # ---- Office portion ----
    # Applied to: annual payments (collections) × office %
    total_collections = fields.Float(string='إجمالي التحصيلات', readonly=True)
    office_discount_amount = fields.Float(string='Office Discount Amt', readonly=True)

    # ---- Perfume factory portion ----
    # Applied to: perfume invoice subtotals × perfume %
    perfume_invoices_total = fields.Float(string='Perfume Invoices Total', readonly=True)
    perfume_discount_owed = fields.Float(string='Perfume Owes Office', readonly=True)

    # ---- Eclador factory portion ----
    # Applied to: eclador invoice subtotals × eclador %
    eclador_invoices_total = fields.Float(string='Eclador Invoices Total', readonly=True)
    eclador_discount_owed = fields.Float(string='Eclador Owes Office', readonly=True)

    # Grand total = office + perfume + eclador discount amounts
    total_earned_discount = fields.Float(string='Total Discount Earned', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
            CREATE OR REPLACE VIEW {table} AS (
                SELECT
                    row_number() OVER () AS id,
                    c.id                                            AS client_id,
                    c.user_id                                       AS user_id,
                    agg.year                                        AS year,
                    c.yearly_discount_percentage,
                    c.discount_office_percentage,
                    c.discount_perfume_percentage,
                    c.discount_eclador_percentage,

                    COALESCE(agg.total_collections, 0)              AS total_collections,
                    COALESCE(agg.total_collections, 0)
                        * (COALESCE(c.discount_office_percentage, 0) / 100.0)    AS office_discount_amount,

                    COALESCE(agg.perfume_invoices_total, 0)         AS perfume_invoices_total,
                    COALESCE(agg.perfume_invoices_total, 0)
                        * (COALESCE(c.discount_perfume_percentage, 0) / 100.0)   AS perfume_discount_owed,

                    COALESCE(agg.eclador_invoices_total, 0)         AS eclador_invoices_total,
                    COALESCE(agg.eclador_invoices_total, 0)
                        * (COALESCE(c.discount_eclador_percentage, 0) / 100.0)   AS eclador_discount_owed,

                    (
                        COALESCE(agg.total_collections, 0)
                            * (COALESCE(c.discount_office_percentage, 0) / 100.0)
                      + COALESCE(agg.perfume_invoices_total, 0)
                            * (COALESCE(c.discount_perfume_percentage, 0) / 100.0)
                      + COALESCE(agg.eclador_invoices_total, 0)
                            * (COALESCE(c.discount_eclador_percentage, 0) / 100.0)
                    )                                               AS total_earned_discount

                FROM office_client c

                JOIN (
                    SELECT
                        t.client_id,
                        to_char(t.date, 'YYYY')                     AS year,

                        SUM(CASE WHEN t.transaction_type = 'payment'
                                 THEN t.amount ELSE 0 END)          AS total_collections,

                        SUM(CASE WHEN t.transaction_type = 'invoice'
                                      AND l.factory_type = 'perfume'
                                 THEN l.subtotal 
                                 WHEN t.transaction_type = 'return'
                                      AND l.factory_type = 'perfume'
                                 THEN l.subtotal
                                 ELSE 0 END)        AS perfume_invoices_total,

                        SUM(CASE WHEN t.transaction_type = 'invoice'
                                      AND l.factory_type = 'eclador'
                                 THEN l.subtotal 
                                 WHEN t.transaction_type = 'return'
                                      AND l.factory_type = 'eclador'
                                 THEN l.subtotal
                                 ELSE 0 END)        AS eclador_invoices_total

                    FROM office_client_transaction t
                    LEFT JOIN office_client_transaction_line l
                           ON l.transaction_id = t.id
                    GROUP BY
                        t.client_id,
                        to_char(t.date, 'YYYY')
                ) agg ON agg.client_id = c.id

                WHERE c.discount_type = 'yearly'
            )
        """.format(table=self._table)
        self.env.cr.execute(sql)
