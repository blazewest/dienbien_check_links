from odoo import http
from odoo.http import request
import json
import logging
from odoo.http import Response


_logger = logging.getLogger(__name__)


class TelegrafDataController(http.Controller):

    @http.route('/telegraf/data', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_telegraf_data(self):
        data = request.jsonrequest  # Thay vì **data
        _logger.info("Received data from Telegraf: %s", json.dumps(data))
        print("Data received:", data)  # Kiểm tra dữ liệu nhận được

        # Lấy các thông tin từ dữ liệu gửi lên
        name = data.get('name', 'Unknown')
        cpu_usage = data.get('cpu_usage', 0.0)
        memory_usage = data.get('memory_usage', 0.0)
        disk_usage = data.get('disk_usage', 0.0)
        network_in = data.get('network_in', 0.0)
        network_out = data.get('network_out', 0.0)

        # Kiểm tra xem bản ghi với tên này đã tồn tại chưa
        existing_record = request.env['telegraf.data'].sudo().search([('name', '=', name)], limit=1)

        if existing_record:
            # Nếu đã tồn tại, cập nhật bản ghi
            existing_record.sudo().write({
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_in': network_in,
                'network_out': network_out,
            })
            message = f"Record {name} updated successfully"
        else:
            # Nếu chưa tồn tại, tạo bản ghi mới
            request.env['telegraf.data'].sudo().create({
                'name': name,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_in': network_in,
                'network_out': network_out,
            })
            message = f"Record {name} created successfully"

        # Trả về JSON response hợp lệ
        return Response(json.dumps({'status': 'success', 'message': message}), content_type='application/json')
