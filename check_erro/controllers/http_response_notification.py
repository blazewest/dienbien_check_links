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
                'telegraf_data_name': rec.telegraf_data_id.host if rec.telegraf_data_id else None,
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

    @http.route('/api/disk_info',
                type='http', auth='public', methods=['GET'],
                csrf=False, website=False)
    def get_disk_info(self, **kwargs):
        try:
            # Lấy key từ tham số URL
            provided_key = kwargs.get('key')
            if not provided_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Missing key parameter'}, ensure_ascii=False),
                    content_type='application/json', status=400
                )

            # Lấy key hợp lệ từ cấu hình
            valid_key = request.env['ir.config_parameter'].sudo().get_param('key_get_data')
            if not valid_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Server configuration error: key_get_data not set'},
                               ensure_ascii=False),
                    content_type='application/json', status=500
                )

            # Kiểm tra key
            if provided_key != valid_key:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Invalid key'}, ensure_ascii=False),
                    content_type='application/json', status=403
                )

            Disk = request.env['telegraf.disk'].sudo()

            # nhóm theo device + telegraf_data_id
            groups = Disk.read_group(
                [],  # bỏ filter để không loại bản ghi
                fields=['device', 'telegraf_data_id'],
                groupby=['device', 'telegraf_data_id'],
                lazy=False
            )

            records = []
            for g in groups:
                device = g.get('device')
                telegraf_data = g.get('telegraf_data_id')
                telegraf_data_id = telegraf_data[0] if telegraf_data else False

                if not device or not telegraf_data_id:
                    continue

                # Lấy bản ghi mới nhất cho từng cặp
                rec = Disk.search([
                    ('device', '=', device),
                    ('telegraf_data_id', '=', telegraf_data_id)
                ], order='timestamp desc', limit=1)

                if rec:
                    records.append({
                        'telegraf_data_host': rec.telegraf_data_id.host if rec.telegraf_data_id else None,
                        'device': rec.device,
                        'total': rec.total,
                        'used': rec.used,
                        'free': rec.free,
                        'used_percent': rec.used_percent,
                        'timestamp': rec.timestamp.strftime('%Y-%m-%d %H:%M:%S') if rec.timestamp else None,
                    })

            return Response(
                json.dumps({'status': 'success', 'count': len(records), 'data': records}, ensure_ascii=False, indent=2),
                content_type='application/json', status=200
            )

        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False),
                content_type='application/json', status=500
            )
