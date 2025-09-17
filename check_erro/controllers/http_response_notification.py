# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HttpResponseNotificationAPI(http.Controller):

    @http.route('/api/http_response_notifications', type='http', auth='none', methods=['GET'], csrf=False)
    def get_http_response_notifications(self, **kwargs):
        """
        API endpoint to get all records of telegraf.http_response_notification
        Requires ?key=YOUR_SECRET_KEY matching ir.config_parameter 'key_get_data'
        Returns: url, response_time, http_response_code, telegraf_data_id.name, timestamp
        """
        try:
            # Lấy key từ tham số URL
            provided_key = kwargs.get('key')
            if not provided_key:
                return request.make_response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Missing key parameter'
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            # Lấy key hợp lệ từ ir.config_parameter
            valid_key = request.env['ir.config_parameter'].sudo().get_param('key_get_data')
            if not valid_key:
                return request.make_response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Server configuration error: key_get_data not set'
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=500
                )

            # Kiểm tra key
            if provided_key != valid_key:
                return request.make_response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Invalid key'
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )

            # Lấy tất cả bản ghi
            records = request.env['telegraf.http_response_notification'].sudo().search([])

            # Chuẩn bị dữ liệu trả về
            data = []
            for rec in records:
                data.append({
                    'url': rec.url,
                    'response_time': rec.response_time,
                    'http_response_code': rec.http_response_code,
                    'telegraf_data_name': rec.telegraf_data_id.name if rec.telegraf_data_id else None,
                    'timestamp': rec.timestamp.strftime('%Y-%m-%d %H:%M:%S') if rec.timestamp else None,
                })

            # Trả về JSON
            return request.make_response(
                json.dumps({
                    'status': 'success',
                    'count': len(data),
                    'data': data
                }, ensure_ascii=False, indent=2),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return request.make_response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }, ensure_ascii=False, indent=2),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
