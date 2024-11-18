from odoo import models, fields


class PortResponse(models.Model):
    _name = 'telegraf.port_response'
    _description = 'Port Response Information'

    port = fields.Char(string='Port')
    protocol = fields.Char(string='Giao thức')
    response_time = fields.Float(string='Thời gian phản hồi (s)')
    result_type = fields.Char(string='Loại kết quả')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')
