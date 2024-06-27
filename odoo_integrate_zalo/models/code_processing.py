# -*- coding: utf-8 -*-
import requests
import json
from odoo import models, fields, api


class CodeProcessing(models.TransientModel):
    _name = 'code.processing'
    _description = "Send Zalo"

    @api.model_create_multi
    def create(self, vals_list):
        # Lọc bỏ các trường không hợp lệ
        valid_fields = self.fields_get().keys()
        cleaned_vals_list = [
            {key: value for key, value in vals.items() if key in valid_fields}
            for vals in vals_list
        ]

        # Gọi phương thức create của lớp cha với danh sách các giá trị đã được làm sạch
        res = super(CodeProcessing, self).create(cleaned_vals_list)

        # Gửi tin nhắn Zalo
        model = self._context.get('active_model')
        information_record = self.env[model].browse(self._context.get('active_id'))
        if information_record.status_code != "200":
            res.send_mess_zalo(information_record)
            information_record.bool_send_zalo = True
        return res


    # https://developers.zalo.me/docs/zalo-notification-service/gui-tin-zns/gui-zns
    # https://account.zalo.cloud/PDUQYDP4VNRRM9WZA/spending/overview
    def send_mess_zalo(self, information_record):
        url = "https://business.openapi.zalo.me/message/template"
        headers = {
            "Content-Type": "application/json"
        }
        if self.get_access_token(information_record):
            headers["access_token"] = self.get_access_token(information_record)
        else:
            model = information_record._name
            vals_list = {'messenger': f"Chưa có Application Zalo cho {model}"}
            return self.env['zalo.log'].sudo().create(vals_list)

        phone_number_vn = self.process_phone_number(information_record)
        if not phone_number_vn:
            return False
        template_data, templates_id = self.process_template_data(information_record)
        for phone_number in phone_number_vn:
            data = {
                "phone": phone_number,
                "template_id": templates_id,
                "template_data": template_data,
                "tracking_id": "1791441201498752166"
            }

            response = requests.post(url, headers=headers, data=json.dumps(data))

            response_data = self.process_response_data(response, phone_number)
            self.create_zalo_log(response_data)

    def get_access_token(self, record):
        name_module = record._name  # Tên module
        # Tìm các bản ghi zalo.application có model nằm trong danh sách các mô hình đã chọn
        app_zalo = self.env['zalo.application'].search([('model.model', '=', name_module)], limit=1)
        if app_zalo:
            access_token = app_zalo.access_token
            return access_token
        else:
            return None

    def process_template_data(self, information_record):
        template_data = {}
        model_name = information_record._name
        templates = self.env['zalo.template'].search(
            [('model', '=', model_name), ('active', '=', 'true')])
        templates_id = templates.id_template
        template_records = templates.zalo_fields_ids
        if template_records:
            for template in template_records:
                model_field_selector = template.model_field_selector
                zalo_parameter = template.zalo_parameter
                field_parts = model_field_selector.split('.')
                len_field_parts = len(field_parts)
                res = information_record
                template_data[zalo_parameter] = self.recursively_process_data(field_parts, len_field_parts, res)
        return template_data, templates_id

    def recursively_process_data(self, list_template_records, len_field_parts, res):
        if len_field_parts == 0 or not list_template_records:
            return res
        data = list_template_records[0]
        type_fields = res._fields[data].type
        if len_field_parts == 1:
            if type_fields in ('many2one', 'many2many', 'one2many'):
                if type_fields == 'many2one':
                    return res[data]['name']
                else:
                    str_list = []
                    for line in res[data]:
                        str_list.append(line['name'])
                    return str_list

            if type_fields in ('date', 'datetime'):
                date = res[data].strftime('%d-%m-%Y %H:%M:%S') if type_fields == 'datetime' else res[data].strftime(
                    '%d-%m-%Y')
                return date
            return res[data]
        else:
            if type_fields in ('many2many', 'one2many'):
                lines = res[data]
                list_template_records = list_template_records[1:]
                len_field_parts -= 1
                result = []
                for line in lines:
                    result.append(
                        self.recursively_process_data(list_template_records, len_field_parts, line))
                return result
            else:
                res = res[data]
                list_template_records = list_template_records[1:]
                len_field_parts -= 1
                return self.recursively_process_data(list_template_records, len_field_parts, res)

    def process_phone_number(self, information_record):
        phone_number_vn_list = []
        list_phone = information_record.responsible_user_ids
        for phone in list_phone:
            phone_number = phone.mobile_phone
            if phone_number.startswith("0"):
                phone_number_vn = "84" + phone_number[1:]
                phone_number_vn_list.append(phone_number_vn)
            else:
                phone_number_vn = phone_number
                phone_number_vn_list.append(phone_number_vn)
        return phone_number_vn_list

    def process_response_data(self, response, phone_number):
        response_data = {}
        if response.status_code == 200:

            response_data["SĐT"] = phone_number
            response_data["LOG"] = response.json()
        else:
            response_data["SĐT"] = phone_number
            response_data["LOG"] = response.json()
        return response_data

    def create_zalo_log(self, response_data):
        vals_list = {'messenger': response_data}
        self.env['zalo.log'].sudo().create(vals_list)