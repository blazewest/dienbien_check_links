from odoo import models, fields

class DiskInfo(models.Model):
    _name = 'telegraf.disk'
    _description = 'Disk Information'

    device = fields.Char(string='Device')
    total = fields.Float(string='Total Space (GB)')
    used = fields.Float(string='Used Space (GB)')
    free = fields.Float(string='Free Space (GB)')
    used_percent = fields.Float(string='Used Percentage (%)')
    timestamp = fields.Datetime(string='Timestamp')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')
