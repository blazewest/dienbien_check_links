from odoo import models, fields

class HttpResponse(models.Model):
    _name = 'telegraf.http_response'
    _description = 'HTTP Response Information'
    _order = 'timestamp desc'

    url = fields.Char(string='URL')
    response_time = fields.Float(string='Thời gian phản hồi (s)')
    http_response_code = fields.Integer(string='Mã phản hồi HTTP')
    content_length = fields.Integer(string='Độ dài nội dung')
    result_type = fields.Char(string='Loại kết quả')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')

