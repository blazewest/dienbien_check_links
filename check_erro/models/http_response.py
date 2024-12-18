from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class HttpResponse(models.Model):
    _name = 'telegraf.http_response'
    _description = 'HTTP Response Information'
    _order = 'timestamp desc'

    url = fields.Char(string='URL')
    response_time = fields.Float(string='Thời gian phản hồi (s)')
    http_response_code = fields.Integer(string='Mã phản hồi HTTP')
    content_length = fields.Integer(string='Độ dài nội dung')
    result_type = fields.Char(string='Loại kết quả')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data')


class HttpResponseNotification(models.Model):
    _name = 'telegraf.http_response_notification'
    _description = 'HTTP Response Notification'

    url = fields.Char(string='URL', required=True)
    response_time = fields.Float(string='Thời gian phản hồi (s)')
    http_response_code = fields.Integer(string='Mã phản hồi HTTP')
    content_length = fields.Integer(string='Độ dài nội dung')
    result_type = fields.Char(string='Loại kết quả')
    timestamp = fields.Datetime(string='Mốc thời gian')  # Thời gian thu thập dữ liệu

    # Reference to the main model
    telegraf_data_id = fields.Many2one('telegraf.data', string='Telegraf Data',
        required=True, ondelete='cascade')

    # Notification fields
    notify_telegram = fields.Boolean(string='Thông báo telegram', required=False, default=True)
    telegram_http_id = fields.Many2one(
        comodel_name='telegram.bot',
        string='Cảnh báo http',
        required=False,
        default=lambda self: self._get_default_telegram_bot()
    )
    # Trạng thái thông báo
    is_notified = fields.Boolean(string='Đã thông báo lỗi', default=False)
    is_recovered = fields.Boolean(string='Đã thông báo phục hồi', default=False)
    last_notification_time = fields.Datetime(string='Thời gian thông báo gần nhất')

    # Unique constraint on 'url' and 'telegraf_data_id'
    @api.constrains('url', 'telegraf_data_id')
    def _check_unique_url_telegraf_data(self):
        for record in self:
            duplicate = self.search([
                ('url', '=', record.url),
                ('telegraf_data_id', '=', record.telegraf_data_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    "The combination of URL and Telegraf Data must be unique. "
                    f"Duplicate found for URL: {record.url} and Telegraf Data ID: {record.telegraf_data_id.id}"
                )

    @api.model
    def _get_default_telegram_bot(self):
        """Return the default telegram bot."""
        default_bot = self.env['telegram.bot'].search([], limit=1)
        return default_bot.id if default_bot else None

    @api.model
    def cron_notify_http_errors(self):
        # Lấy tất cả các bản ghi có lỗi HTTP
        error_records = self.search([
            ('notify_telegram', '=', True),
            ('telegram_http_id', '!=', False),
            ('http_response_code', 'not in', [200, 302]),
        ])

        for record in error_records:
            try:
                # Đặt khóa FOR UPDATE
                self.env.cr.execute(
                    "SELECT id FROM telegraf_http_response_notification WHERE id = %s FOR UPDATE NOWAIT", (record.id,))
                # Gửi thông báo lỗi
                message = (
                    f"<a href='{record.url}'>{record.url}</a>\n"
                    f" 🛑Mã phản hồi: {record.http_response_code}\n"
                )
                record.telegram_http_id.send_message(message)
                # Cập nhật thời gian thông báo lỗi lần cuối
                record.write(
                    {'is_notified': True, 'is_recovered': False, 'last_notification_time': fields.Datetime.now()})
            except Exception as e:
                # Ghi log lỗi
                self.env['ir.logging'].create({
                    'name': 'Telegram HTTP Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send HTTP alert for URL {record.url}: {str(e)}",
                    'path': 'telegraf.http_response_notification',
                    'line': '0',
                    'func': 'cron_notify_http_errors',
                })

        # Lấy tất cả các bản ghi đã phục hồi và chưa thông báo phục hồi
        recovered_records = self.search([
            ('notify_telegram', '=', True),
            ('telegram_http_id', '!=', False),
            ('http_response_code', 'in', [200, 302]),
            ('is_recovered', '=', False),
            ('is_notified', '=', True)  # Chỉ gửi thông báo nếu trước đó đã có thông báo lỗi
        ])

        for record in recovered_records:
            try:
                # Đặt khóa FOR UPDATE
                self.env.cr.execute(
                    "SELECT id FROM telegraf_http_response_notification WHERE id = %s FOR UPDATE NOWAIT", (record.id,))
                # Gửi thông báo phục hồi
                message = (
                    f"<a href='{record.url}'>{record.url}</a>\n"
                    "🟢 Trạng thái: Đã hoạt động\n"
                )
                record.telegram_http_id.send_message(message)
                # Đánh dấu đã phục hồi
                record.write({'is_recovered': True, 'last_notification_time': fields.Datetime.now()})
            except Exception as e:
                # Ghi log lỗi
                self.env['ir.logging'].create({
                    'name': 'Telegram HTTP Recovery Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send HTTP recovery alert for URL {record.url}: {str(e)}",
                    'path': 'telegraf.http_response_notification',
                    'line': '0',
                    'func': 'cron_notify_http_errors',
                })




