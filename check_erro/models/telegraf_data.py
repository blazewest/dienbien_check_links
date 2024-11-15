from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TelegrafData(models.Model):
    _name = 'telegraf.data'
    _description = 'Telegraf Data'

    # Thông tin chính
    host = fields.Char(string='Host')
    memory_total = fields.Float(string='Tổng bộ nhớ (GB)')
    memory_used = fields.Float(string='Bộ nhớ đã sử dụng (GB)')
    memory_available = fields.Float(string='Bộ nhớ khả dụng (GB)')
    memory_used_percent = fields.Float(string='Bộ nhớ đã sử dụng (%)')

    # Kết nối mạng
    tcp_established = fields.Integer(string='SL TCP ở trạng thái ESTABLISHED')
    tcp_listen = fields.Integer(string='SL TCP ở trạng thái LISTEN')
    tcp_time_wait = fields.Integer(string='SL TCP ở trạng thái TIME_WAIT')
    udp_socket = fields.Integer(string='SL socket UDP đang mở')

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

