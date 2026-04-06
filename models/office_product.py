from odoo import models, fields, api

class OfficeProduct(models.Model):
    _name = 'office.product'
    _description = 'Office Product'
    
    name = fields.Char(string='اسم المنتج', required=True)
    list_price = fields.Float(string='Sales Price', default=0.0)
    
    profit_type = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount')
    ], string='Profit Type (Office)', required=True, default='percentage')
    
    profit_value = fields.Float(string='Profit Value', required=True, default=0.0)

    factory_type = fields.Selection([
        ('perfume', 'Perfume (برفان)'),
        ('eclador', 'Eclador (أكلادور)')
    ], string='المصنع', required=True, default='perfume')
