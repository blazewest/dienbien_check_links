from odoo import models, fields

class HttpResponse(models.Model):
    _name = 'telegraf.http_response'
    _description = 'HTTP Response Information'

    url = fields.Char(string='URL')
    response_time = fields.Float(string='Response Time (s)')
    http_response_code = fields.Integer(string='HTTP Response Code')
    content_length = fields.Integer(string='Content Length')
    result_type = fields.Char(string='Result Type')
    timestamp = fields.Datetime(string='Timestamp')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')

