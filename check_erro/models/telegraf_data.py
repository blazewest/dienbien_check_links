from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class TelegrafData(models.Model):
    _name = 'telegraf.data'
    _description = 'Telegraf Data'
    _rec_name = 'host'  # Đặt host là tên đại diện
    _order = 'memory_used_percent desc'

    # Thông tin chính
    host = fields.Char(string='Host')
    memory_total = fields.Float(string='Tổng bộ nhớ (GB)')
    memory_used = fields.Float(string='Bộ nhớ đã sử dụng (GB)')
    memory_available = fields.Float(string='Bộ nhớ khả dụng (GB)')
    memory_used_percent = fields.Float(string='Bộ nhớ đã sử dụng (%)')

    # Thông tin CPU
    cpu_load1 = fields.Float(string='CPU Load 1 Minute')
    cpu_load5 = fields.Float(string='CPU Load 5 Minutes')
    cpu_load15 = fields.Float(string='CPU Load 15 Minutes')
    n_cpus = fields.Integer(string='Số lượng CPU')

    # Thời gian cập nhật cuối và cảnh báo
    last_update = fields.Datetime(string='Lần cập nhật cuối', default=lambda self: fields.Datetime.now())
    is_active = fields.Boolean(string='Đang hoạt động', default=True)

    # Kết nối mạng
    tcp_established = fields.Integer(string='TCP ở trạng thái ESTABLISHED')
    tcp_listen = fields.Integer(string='TCP ở trạng thái LISTEN')
    tcp_time_wait = fields.Integer(string='TCP ở trạng thái TIME_WAIT')
    udp_socket = fields.Integer(string='socket UDP đang mở')

    # One2many fields for related information
    disk_info_ids = fields.One2many('telegraf.disk', 'telegraf_data_id', string='Thông tin đĩa')
    port_response_ids = fields.One2many('telegraf.port_response', 'telegraf_data_id', string='Phản hồi của cổng cụ thể')
    http_response_ids = fields.One2many('telegraf.http_response', 'telegraf_data_id', string='Phản hồi HTTP')
    login_attempt_ids = fields.One2many('login.attempt', 'telegraf_data_id', string="Thông Tin Đăng Nhập")

    @api.constrains('host')
    def _check_host_unique(self):
        for record in self:
            if self.search_count([('host', '=', record.host)]) > 1:
                raise ValidationError("Host phải là duy nhất!")

    def update_last_update_time(self):
        """Cập nhật thời gian cuối khi nhận dữ liệu mới"""
        self.write({
            'last_update': fields.Datetime.now(),
            'is_active': True  # Đặt lại thành hoạt động khi có cập nhật mới
        })

    @api.model
    def check_inactive_records(self):
        """Kiểm tra các bản ghi không nhận tín hiệu sau 10 phút và cập nhật trường 'is_active'."""
        threshold_time = datetime.now() - timedelta(minutes=10)
        inactive_records = self.search([('last_update', '<', threshold_time), ('is_active', '=', True)])

        # Đặt trạng thái is_active thành False cho các bản ghi không có cập nhật
        inactive_records.write({'is_active': False})

