# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json
from urllib.parse import urlencode
from odoo.exceptions import ValidationError

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

        url = "https://oauth.zaloapp.com/v4/oa/access_token"
        required_fields = [
            ('secret_key', 'Secret key'),
            ('refresh_token', 'Refresh token'),
            ('id_app', 'ID app'),
        ]
        for field, field_name in required_fields:
            if not getattr(self, field):
                raise models.ValidationError(f"Không có {field_name}")

        secret_key = self.secret_key
        headers = {
            "secret_key": secret_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        refresh_token = self.refresh_token
        app_id = self.id_app
        data = {
            "refresh_token": refresh_token,
            "app_id": app_id,
            "grant_type": "refresh_token"
        }
        encoded_data = urlencode(data)
        # Gửi yêu cầu POST
        # if
        response = requests.post(url, headers=headers, data=encoded_data)
        # Xử lý kết quả
        if response.status_code == 200:
            # print("Yêu cầu POST thành công")
            response_data = response.json()
            # print("Dữ liệu trả về từ Zalo API:", response_data)
            if 'access_token' in response_data:
                self.access_token = response_data['access_token']
                self.refresh_token = response_data['refresh_token']
            else:
                raise models.ValidationError(response_data['error_description'])
        else:
            print("Yêu cầu POST không thành công. Mã lỗi:", response.status_code)
            print("Nội dung lỗi:", response.text)


    def get_access_token(self, model):
        pass

    @api.model
    def _run_get_access_token(self):
        # Call your method here
        self.get_access_token_to_refresh_token()