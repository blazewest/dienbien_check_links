from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.exceptions import UserError
class TelegrafData(models.Model):
    _name = 'telegraf.data'
    _description = 'Telegraf Data'
    _rec_name = 'host'  # Đặt host là tên đại diện
    _order = 'memory_used_percent desc'

    # Thông tin chính
    host = fields.Char(string='Host')
    memory_total = fields.Float(string='Tổng Ram (GB)')
    memory_used = fields.Float(string='Ram đã sử dụng (GB)')
    memory_available = fields.Float(string='Ram khả dụng (GB)')
    memory_used_percent = fields.Float(string='Ram đã sử dụng (%)')

    # Thông tin CPU
    cpu_load1 = fields.Float(string='CPU Load 1 Minute')
    cpu_load5 = fields.Float(string='CPU Load 5 Minutes')
    cpu_load15 = fields.Float(string='CPU Load 15 Minutes')
    n_cpus = fields.Integer(string='Số lượng CPU')

    disk_count = fields.Integer(string='Số lượng ổ đĩa', default=0)
    critical_disks = fields.Integer(string='Số ổ đĩa trên 80%', default=0)
    web_count = fields.Integer(string='Số lượng web', default=0)
    web_error_count = fields.Integer(string='Số lượng web hỏng', default=0)

    # Thời gian cập nhật cuối và cảnh báo
    last_update = fields.Datetime(string='Lần cập nhật cuối', default=lambda self: fields.Datetime.now())
    is_active = fields.Boolean(string='Đang hoạt động', default=True)

    # Kết nối mạng
    tcp_established = fields.Integer(string='TCP ESTABLISHED')
    tcp_listen = fields.Integer(string='TCP LISTEN')
    tcp_time_wait = fields.Integer(string='TCP TIME_WAIT')
    udp_socket = fields.Integer(string='socket UDP đang mở')

    # One2many fields for related information
    disk_info_ids = fields.One2many('telegraf.disk', 'telegraf_data_id', string='Thông tin đĩa')
    port_response_ids = fields.One2many('telegraf.port_response', 'telegraf_data_id', string='Phản hồi của cổng cụ thể')
    http_response_ids = fields.One2many('telegraf.http_response', 'telegraf_data_id', string='Phản hồi HTTP')
    login_attempt_ids = fields.One2many('login.attempt', 'telegraf_data_id', string="Thông Tin Đăng Nhập")

    # nhan thong bao tele
    notify_telegram = fields.Boolean(string='Thông báo telegram', required=False, default=True)
    telegram_main_id = fields.Many2one(comodel_name='telegram.bot', string='Cảnh báo chính', required=False, default=lambda self: self._get_default_telegram_bot())
    telegram_device_id = fields.Many2one(comodel_name='telegram.bot',string='Cảnh báo device', required=False, default=lambda self: self._get_default_telegram_bot())
    telegram_http_id = fields.Many2one(comodel_name='telegram.bot', string='Cảnh báo http', required=False, default=lambda self: self._get_default_telegram_bot())
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
    def _get_default_telegram_bot(self):
        # Lấy bản ghi đầu tiên trong telegram.bot hoặc None
        default_bot = self.env['telegram.bot'].search([], limit=1)
        return default_bot.id if default_bot else None

    @api.model
    def check_inactive_records(self):
        """Kiểm tra các bản ghi không nhận tín hiệu sau 10 phút và cập nhật trường 'is_active'."""
        threshold_time = datetime.now() - timedelta(minutes=10)
        inactive_records = self.search([('last_update', '<', threshold_time), ('is_active', '=', True)])

        # Đặt trạng thái is_active thành False cho các bản ghi không có cập nhật
        inactive_records.write({'is_active': False})

    @api.model
    def cron_send_telegram_alerts(self):
        # Lọc các bản ghi thỏa mãn điều kiện
        records = self.search([
            ('notify_telegram', '=', True),  # Chỉ các bản ghi có notify_telegram = True
            ('telegram_main_id', '!=', False),  # Có cấu hình Telegram Bot
            '|',  # Toán tử OR bắt đầu
            ('memory_used_percent', '>', 80),  # RAM sử dụng > 80%
            ('critical_disks', '>', 0)  # Có ổ đĩa trên 80%
        ])

        for record in records:
            # Tạo thông báo dựa trên điều kiện
            if record.memory_used_percent > 80 and record.critical_disks > 0:
                # Cả RAM > 80% và ổ đĩa > 80%
                message = (
                    f"<b>CẢNH BÁO HỆ THỐNG</b>\n"
                    f"Host: {record.host}\n"
                    f"RAM đã sử dụng: {record.memory_used_percent:.2f}%\n"
                    f"Số ổ đĩa trên 80%: {record.critical_disks}\n"
                )
            elif record.memory_used_percent > 80:
                # Chỉ RAM > 80%
                message = (
                    f"<b>CẢNH BÁO HỆ THỐNG</b>\n"
                    f"Host: {record.host}\n"
                    f"RAM đã sử dụng: {record.memory_used_percent:.2f}%\n"
                )
            elif record.critical_disks > 0:
                # Chỉ ổ đĩa > 80%
                message = (
                    f"<b>CẢNH BÁO HỆ THỐNG</b>\n"
                    f"Host: {record.host}\n"
                    f"Số ổ đĩa trên 80%: {record.critical_disks}\n"
                )
            else:
                # Không có cảnh báo (trường hợp này sẽ không xảy ra do bộ lọc)
                continue

            # Gửi thông báo qua Telegram
            try:
                record.telegram_main_id.send_message(message)
            except UserError as e:
                # Ghi log nếu không gửi được
                self.env['ir.logging'].create({
                    'name': 'Telegram Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send alert for host {record.host}: {str(e)}",
                    'path': 'telegraf.data',
                    'line': '0',
                    'func': 'cron_send_telegram_alerts',
                })

    @api.model
    def cron_check_server_signal(self):
        # Lấy thời gian hiện tại
        current_time = fields.Datetime.now()
        # Tính thời gian 10 phút trước
        ten_minutes_ago = current_time - timedelta(minutes=10)

        # Lọc các bản ghi thỏa mãn điều kiện
        records = self.search([
            ('notify_telegram', '=', True),  # Chỉ bản ghi có thông báo telegram
            ('telegram_main_id', '!=', False),  # Đã cấu hình Telegram Bot
            ('last_update', '<', ten_minutes_ago)  # Cập nhật cuối hơn 10 phút trước
        ])

        for record in records:
            # Tạo thông báo cảnh báo
            message = (
                f"<b>CẢNH BÁO HỆ THỐNG</b>\n"
                f"Host: {record.host}\n"
                f"Trạng thái: Không nhận được tín hiệu từ server.\n"
                f"Lần cập nhật cuối: {record.last_update}\n"
            )

            # Gửi thông báo qua Telegram
            try:
                record.telegram_main_id.send_message(message)
            except UserError as e:
                # Ghi log nếu gửi thông báo thất bại
                self.env['ir.logging'].create({
                    'name': 'Telegram Signal Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send alert for host {record.host}: {str(e)}",
                    'path': 'telegraf.data',
                    'line': '0',
                    'func': 'cron_check_server_signal',
                })
