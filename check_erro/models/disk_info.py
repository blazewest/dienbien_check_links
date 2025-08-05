from odoo import models, fields, api
from datetime import datetime, timedelta

class DiskInfo(models.Model):
    _name = 'telegraf.disk'
    _description = 'Disk Information'
    _order = 'timestamp desc'

    device = fields.Char(string='Device')
    total = fields.Float(string='Tổng dung lượng (GB)')
    used = fields.Float(string='Dung lượng đã sử dụng (GB)')
    free = fields.Float(string='Không gian trống (GB)')
    used_percent = fields.Float(string='Phần trăm đã sử dụng (%)')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu
    days = fields.Integer(string='Số ngày hiển thị', default=1)
    disk_chart = fields.Text(string='Biểu đồ', compute='_compute_disk_chart')

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')

    @api.depends('device', 'days')
    def _compute_disk_chart(self):
        for record in self:
            record.disk_chart = False
            if record.device:
                chart_data = self.get_disk_usage_data(record.device, record.days)
                record.disk_chart = chart_data

    @api.model
    def get_disk_usage_data(self, device=None, days=1):
        """
        Lấy dữ liệu sử dụng ổ đĩa theo thời gian cho biểu đồ
        :param device: Tên thiết bị ổ đĩa cần theo dõi
        :param days: Số ngày cần lấy dữ liệu (mặc định 1 ngày)
        :return: dict chứa dữ liệu cho biểu đồ
        """
        domain = [
            ('timestamp', '>=', fields.Datetime.now() - timedelta(days=days))
        ]
        if device:
            domain.append(('device', '=', device))

        disk_records = self.search(domain, order='timestamp asc')

        data = {
            'labels': [],  # Trục x - thời gian
            'datasets': [{
                'label': 'Dung lượng đã sử dụng (GB)',
                'data': [],  # Trục y - dung lượng sử dụng
                'borderColor': '#2196F3',
                'fill': False,
                'tension': 0.1
            }]
        }

        for record in disk_records:
            data['labels'].append(record.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            data['datasets'][0]['data'].append(round(record.used, 2))

        return data
