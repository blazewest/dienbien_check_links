# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import requests
import json
from urllib.parse import urlencode
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class ZaloApplication(models.Model):
    _name = 'zalo.application'
    _description = 'zalo.application'

    name = fields.Char('Name Application')
    id_app = fields.Char('Zalo API', required=True)
    secret_key = fields.Char('Secret key', required=True)
    code = fields.Char('Code')
    access_token = fields.Char('Access token')
    refresh_token = fields.Char('Refresh token')
    model = fields.Many2many('ir.model')

    _sql_constraints = [('id_app', 'unique (id_app)', 'ID Application đã tồn tại!')]

    @api.constrains('id_app', 'model')
    def constrains_id_app_model(self):
        for record in self:
            if record.model:
                # Lấy tất cả các mô hình đã chọn trong trường model của bản ghi hiện tại
                selected_models = record.model.mapped('model')
                # Kiểm tra từng mô hình đã chọn
                for selected_model in selected_models:
                    # Kiểm tra xem mô hình đã tồn tại trong các bản ghi khác hay chưa
                    existing_records = self.search([
                        ('id', '!=', record.id),  # Loại trừ bản ghi hiện tại
                        ('model', '=', selected_model),  # Kiểm tra mô hình
                    ])
                    if existing_records:
                        raise ValidationError(f"Mô hình {selected_model} đã tồn tại trong một bản ghi khác.")

    def get_access_token_to_refresh_token(self):
        """
        Làm mới access_token bằng refresh_token cho một hoặc nhiều bản ghi.
        """
        # Kiểm tra từng bản ghi trong recordset
        for record in self:
            try:
                # Kiểm tra các trường bắt buộc
                required_fields = [
                    ('secret_key', 'Secret key'),
                    ('refresh_token', 'Refresh token'),
                    ('id_app', 'ID app'),
                ]
                missing_field = False
                for field, field_name in required_fields:
                    if not getattr(record, field):
                        _logger.warning(f"[Zalo] Thiếu {field_name} cho bản ghi {record.id} - {record.name}")
                        missing_field = True
                        break  # Dừng kiểm tra nếu thiếu trường

                if missing_field:
                    continue  # Bỏ qua bản ghi này, xử lý bản ghi tiếp theo

                # Chuẩn bị dữ liệu
                url = "https://oauth.zaloapp.com/v4/oa/access_token"  # ✅ Đã xóa khoảng trắng
                headers = {
                    "secret_key": record.secret_key,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Odoo Zalo Integration'
                }
                data = {
                    "refresh_token": record.refresh_token,
                    "app_id": record.id_app,
                    "grant_type": "refresh_token"
                }
                encoded_data = urlencode(data)

                # Gửi request
                response = requests.post(url, headers=headers, data=encoded_data, timeout=10)

                if response.status_code == 200:
                    response_data = response.json()
                    if 'access_token' in response_data:
                        record.write({
                            'access_token': response_data['access_token'],
                            'refresh_token': response_data.get('refresh_token', record.refresh_token),
                            # Cập nhật nếu có mới
                        })
                        _logger.info(f"[Zalo] Đã làm mới token cho {record.name}")
                    else:
                        error_desc = response_data.get('error_description', 'Unknown error')
                        _logger.error(f"[Zalo] Lỗi API khi làm mới token cho {record.name}: {error_desc}")
                else:
                    _logger.error(
                        f"[Zalo] Lỗi HTTP {response.status_code} khi làm mới token cho {record.name}: {response.text}")

            except Exception as e:
                _logger.exception(f"[Zalo] Lỗi khi làm mới token cho bản ghi {record.name}: {str(e)}")
                # Ghi vào ir.logging nếu cần
                self.env['ir.logging'].create({
                    'name': 'Zalo Token Refresh Failed',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Record {record.name}: {str(e)}",
                    'path': 'zalo.application',
                    'line': '0',
                    'func': 'get_access_token_to_refresh_token',
                })

    @api.model
    def _run_get_access_token(self):
        """
        Cron job: Làm mới access_token cho tất cả các bản ghi có refresh_token
        """
        zalo_apps = self.search([('refresh_token', '!=', False)])
        if not zalo_apps:
            _logger.info("[Zalo] Không tìm thấy bản ghi nào có refresh_token.")
            return

        zalo_apps.get_access_token_to_refresh_token()  # Gọi trên toàn bộ recordset

    @api.model
    def cron_notify_http_errors_zalo(self):
        # Các bản ghi lỗi cần gửi qua Zalo
        error_records = self.search([
            ('notify_zalo', '=', True),
            ('partner_id.id_zalo', '!=', False),
            ('zalo_oa_id.access_token', '!=', False),
            ('http_response_code', 'not in', [200, 302]),
        ])

        for record in error_records:
            try:
                self.env.cr.execute(
                    "SELECT id FROM telegraf_http_response_notification WHERE id = %s FOR UPDATE NOWAIT", (record.id,))

                message_text = (
                    f"{record.url}\n"
                    f"🛑 Mã phản hồi: {record.http_response_code}"
                )

                self._send_zalo_message(
                    access_token=record.zalo_oa_id.access_token,
                    user_id=record.partner_id.id_zalo,
                    message=message_text
                )

                record.write({
                    'is_notified': True,
                    'is_recovered': False,
                    'last_notification_time': fields.Datetime.now()
                })
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Zalo HTTP Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send Zalo HTTP alert for URL {record.url}: {str(e)}",
                    'path': 'telegraf.http_response_notification',
                    'line': '0',
                    'func': 'cron_notify_http_errors_zalo',
                })

        # Các bản ghi đã phục hồi cần gửi thông báo
        recovered_records = self.search([
            ('notify_zalo', '=', True),
            ('partner_id.id_zalo', '!=', False),
            ('zalo_oa_id.access_token', '!=', False),
            ('http_response_code', 'in', [200, 302]),
            ('is_recovered', '=', False),
            ('is_notified', '=', True),
        ])

        for record in recovered_records:
            try:
                self.env.cr.execute(
                    "SELECT id FROM telegraf_http_response_notification WHERE id = %s FOR UPDATE NOWAIT", (record.id,))

                message_text = (
                    f"{record.url}\n"
                    "🟢 Trạng thái: Đã hoạt động"
                )

                self._send_zalo_message(
                    access_token=record.zalo_oa_id.access_token,
                    user_id=record.partner_id.id_zalo,
                    message=message_text
                )

                record.write({
                    'is_recovered': True,
                    'last_notification_time': fields.Datetime.now()
                })
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Zalo HTTP Recovery Alert Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Failed to send Zalo recovery alert for URL {record.url}: {str(e)}",
                    'path': 'telegraf.http_response_notification',
                    'line': '0',
                    'func': 'cron_notify_http_errors_zalo',
                })

    def _send_zalo_message(self, access_token, user_id, message):
        """Hàm gửi tin nhắn Zalo CS"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'access_token': access_token,
            }
            payload = {
                "recipient": {
                    "user_id": user_id
                },
                "message": {
                    "text": message
                }
            }

            response = requests.post(
                "https://openapi.zalo.me/v3.0/oa/message/cs",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            # Optional: Ghi log nếu cần
            if response.json().get('error', 0) != 0:
                raise Exception(f"Zalo API error: {response.json()}")
        except Exception as e:
            raise Exception(f"Zalo send error: {str(e)}")