from odoo import models, fields

class LoginAttempt(models.Model):
    _name = 'login.attempt'
    _description = 'Thông Tin Đăng Nhập'
    _order = 'timestamp desc'

    login_date = fields.Datetime(string="Thời Gian Đăng Nhập")
    username = fields.Char(string="Tên Người Dùng")
    ip_address = fields.Char(string="Địa Chỉ IP")
    status = fields.Selection([
        ('success', 'Thành Công'),
        ('failure', 'Thất Bại')
    ], string="Trạng Thái Đăng Nhập")
    failure_reason = fields.Char(string="Lý Do Thất Bại", help="Lý do đăng nhập thất bại (nếu có)")
    telegraf_data_id = fields.Many2one('telegraf.data', string="Telegraf Data", ondelete='cascade')

    # Các trường bổ sung để lưu các thông tin chi tiết
    process_name = fields.Char(string="Tên Quá Trình")
    logon_type = fields.Char(string="Loại Đăng Nhập")
    event_id = fields.Char(string="ID Sự Kiện")
    logon_domain = fields.Char(string="Tên Miền Đăng Nhập")
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu
