# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json

class HttpResponseNotificationAPI(http.Controller):

    @http.route('/api/http_response_notifications',
                type='http', auth='public', methods=['GET'],
                csrf=False, website=False)
    def get_http_response_notifications(self, **kwargs):
        try:
            # Lấy key từ tham số URL
            provided_key = kwargs.get('key')
            if not provided_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Missing key parameter'}, ensure_ascii=False),
                    content_type='application/json', status=400
                )

            # Lấy key hợp lệ từ ir.config_parameter
            valid_key = request.env['ir.config_parameter'].sudo().get_param('key_get_data')
            if not valid_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Server configuration error: key_get_data not set'}, ensure_ascii=False),
                    content_type='application/json', status=500
                )

            # Kiểm tra key
            if provided_key != valid_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Invalid key'}, ensure_ascii=False),
                    content_type='application/json', status=403
                )

            # Lấy dữ liệu
            records = request.env['telegraf.http_response_notification'].sudo().search([])
            data = [{
                'url': rec.url,
                'response_time': rec.response_time,
                'http_response_code': rec.http_response_code,
                'telegraf_data_name': rec.telegraf_data_id.name if rec.telegraf_data_id else None,
                'timestamp': rec.timestamp.strftime('%Y-%m-%d %H:%M:%S') if rec.timestamp else None,
            } for rec in records]

            return Response(
                json.dumps({'status': 'success', 'count': len(data), 'data': data}, ensure_ascii=False, indent=2),
                content_type='application/json', status=200
            )

        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False),
                content_type='application/json', status=500
            )
