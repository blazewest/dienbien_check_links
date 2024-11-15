from datetime import datetime
from odoo import http
from odoo.http import request
import json
import logging
from dateutil import parser

_logger = logging.getLogger(__name__)


class TelegrafDataController(http.Controller):

    @http.route('/telegraf/data', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_telegraf_data(self, **kw):
        data = request.httprequest.get_json()
        _logger.info("Received data from Telegraf: %s", json.dumps(data))

        metrics = data.get('metrics', [])
        host_name = self._get_host_name(metrics)

        if not host_name or host_name == 'Unknown':
            _logger.info("No host found in the data. Skipping record creation.")
            return {"status": "no host found"}

        existing_telegraf_data = request.env['telegraf.data'].sudo().search([('host', '=', host_name)], limit=1)

        if existing_telegraf_data:
            main_info = self._parse_main_info(metrics)
            existing_telegraf_data.sudo().write(main_info)
            telegraf_data = existing_telegraf_data
        else:
            main_info = self._parse_main_info(metrics)
            telegraf_data = request.env['telegraf.data'].sudo().create(main_info)

        # Update or create One2many related data
        self._store_disk_info(telegraf_data, metrics)
        self._store_port_response(telegraf_data, metrics)
        self._store_http_response(telegraf_data, metrics)
        self._store_login_attempts(telegraf_data, metrics)

        return {"status": "success"}

    def _get_host_name(self, metrics):
        for metric in metrics:
            if 'host' in metric.get('tags', {}):
                return metric['tags']['host']
        return 'Unknown'

    def _parse_main_info(self, metrics):
        main_info = {'host': self._get_host_name(metrics)}
        for metric in metrics:
            name = metric.get('name')
            fields = metric.get('fields', {})

            if name == 'mem':
                main_info.update({
                    'memory_total': fields.get('total', 0) / (1024 ** 3),
                    'memory_used': fields.get('used', 0) / (1024 ** 3),
                    'memory_available': fields.get('available', 0) / (1024 ** 3),
                    'memory_used_percent': fields.get('used_percent', 0),
                })
            elif name == 'netstat':
                main_info.update({
                    'tcp_established': fields.get('tcp_established', 0),
                    'tcp_listen': fields.get('tcp_listen', 0),
                    'tcp_time_wait': fields.get('tcp_time_wait', 0),
                    'udp_socket': fields.get('udp_socket', 0),
                })
        return main_info

    def _store_disk_info(self, telegraf_data, metrics):
        for metric in metrics:
            if metric.get('name') == 'disk':
                fields = metric.get('fields', {})
                request.env['telegraf.disk'].sudo().create({
                    'device': metric.get('tags', {}).get('device', 'Unknown'),
                    'total': fields.get('total', 0) / (1024 ** 3),
                    'used': fields.get('used', 0) / (1024 ** 3),
                    'free': fields.get('free', 0) / (1024 ** 3),
                    'used_percent': fields.get('used_percent', 0),
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })

    def _store_port_response(self, telegraf_data, metrics):
        for metric in metrics:
            if metric.get('name') == 'net_response':
                fields = metric.get('fields', {})
                request.env['telegraf.port_response'].sudo().create({
                    'port': metric.get('tags', {}).get('port', 'Unknown'),
                    'protocol': metric.get('tags', {}).get('protocol', 'Unknown'),
                    'response_time': fields.get('response_time', 0),
                    'result_type': fields.get('result_type', 'Unknown'),
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })

    def _store_http_response(self, telegraf_data, metrics):
        for metric in metrics:
            if metric.get('name') == 'http_response':
                fields = metric.get('fields', {})
                request.env['telegraf.http_response'].sudo().create({
                    'url': metric.get('tags', {}).get('server', 'Unknown'),
                    'response_time': fields.get('response_time', 0),
                    'http_response_code': fields.get('http_response_code', 0),
                    'content_length': fields.get('content_length', 0),
                    'result_type': fields.get('result_type', 'Unknown'),
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })

    def _store_login_attempts(self, telegraf_data, metrics):
        # Store login attempt information in one2many relation
        for metric in metrics:
            if metric.get("name") == "win_eventlog" and metric.get("tags", {}).get("EventID") in ["4625", "4624"]:
                login_status = 'success' if metric["tags"]["EventID"] == "4624" else 'failure'
                failure_reason = metric["fields"].get("Data_FailureReason", '') if login_status == 'failure' else ''

                # Chuyển đổi thời gian từ định dạng ISO 8601 và loại bỏ thông tin múi giờ
                time_created = metric["fields"].get("TimeCreated", datetime.now())
                if isinstance(time_created, str):  # Kiểm tra xem có phải là chuỗi hay không
                    time_created = parser.isoparse(time_created).replace(tzinfo=None)  # Chuyển đổi sang naive datetime

                request.env['login.attempt'].sudo().create({
                    'login_date': time_created,
                    'username': metric["fields"].get("Data_TargetUserName", "Unknown"),
                    'ip_address': metric["fields"].get("Data_IpAddress", "Unknown"),
                    'status': login_status,
                    'failure_reason': failure_reason,
                    'process_name': metric["fields"].get("ProcessName", ""),
                    'logon_type': metric["fields"].get("Data_LogonType", ""),
                    'event_id': metric["tags"].get("EventID", ""),
                    'logon_domain': metric["fields"].get("Data_SubjectDomainName", ""),
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })
