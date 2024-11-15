from odoo import models, fields


class PortResponse(models.Model):
    _name = 'telegraf.port_response'
    _description = 'Port Response Information'

    port = fields.Char(string='Port')
    protocol = fields.Char(string='Protocol')
    response_time = fields.Float(string='Response Time (s)')
    result_type = fields.Char(string='Result Type')
    timestamp = fields.Datetime(string='Timestamp')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')
