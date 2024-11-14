from odoo import models, fields, api

class TelegrafData(models.Model):
    _name = 'telegraf.data'
    _description = 'Telegraf Data'

    name = fields.Char(string='Data Name')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    cpu_usage = fields.Float(string='CPU Usage')
    memory_usage = fields.Float(string='Memory Usage')
    disk_usage = fields.Float(string='Disk Usage')
    network_in = fields.Float(string='Network In')
    network_out = fields.Float(string='Network Out')
    # Thêm các trường khác tùy theo dữ liệu bạn nhận được từ Telegraf
