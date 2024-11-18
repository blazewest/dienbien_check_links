from odoo import models, fields

class DiskInfo(models.Model):
    _name = 'telegraf.disk'
    _description = 'Disk Information'

    device = fields.Char(string='Device')
    total = fields.Float(string='Tổng dung lượng (GB)')
    used = fields.Float(string='Dung lượng đã sử dụng (GB)')
    free = fields.Float(string='Không gian trống (GB)')
    used_percent = fields.Float(string='Phần trăm đã sử dụng (%)')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')
