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
        # _logger.info("Received data from Telegraf: %s", json.dumps(data))

        metrics = data.get('metrics', [])
        host_name = self._get_host_name(metrics)
        # if host_name == 'WEBS-XAYDUNG':
        #     _logger.info("Received data from Telegraf: %s", json.dumps(data))

        if not host_name or host_name == 'Unknown':
            _logger.info("No host found in the data. Skipping record creation.")
            return {"status": "no host found"}

        existing_telegraf_data = request.env['telegraf.data'].sudo().search([('host', '=', host_name)], limit=1)

        if existing_telegraf_data:
            main_info = self._parse_main_info(metrics)
            existing_telegraf_data.sudo().write(main_info)
            existing_telegraf_data.update_last_update_time()  # Cập nhật thời gian cuối khi có dữ liệu mới
            telegraf_data = existing_telegraf_data
        else:
            main_info = self._parse_main_info(metrics)
            telegraf_data = request.env['telegraf.data'].sudo().create(main_info)
            telegraf_data.update_last_update_time()

        # Update or create One2many related data
        self._store_disk_info(telegraf_data, metrics)
        self._store_port_response(telegraf_data, metrics)
        self._store_http_response(telegraf_data, metrics)
        self._store_login_attempts(telegraf_data, metrics)
        _logger.info("Update data from Telegraf: %s", host_name)

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

            elif name == 'system' and 'load1' in fields and 'load5' in fields and 'load15' in fields:
                cpu_load1 = fields.get('load1', 0)
                cpu_load5 = fields.get('load5', 0)
                cpu_load15 = fields.get('load15', 0)
                n_cpus = fields.get('n_cpus', 0)

                main_info.update({
                    'cpu_load1': round(cpu_load1, 6),
                    'cpu_load5': round(cpu_load5, 6),
                    'cpu_load15': round(cpu_load15, 6),
                    'n_cpus': n_cpus,
                })

            # Cập nhật tỷ lệ sử dụng CPU
            elif name == 'cpu':
                usage_user = fields.get('usage_user', 0)
                usage_system = fields.get('usage_system', 0)
                usage_idle = fields.get('usage_idle', 0)

                # Tính toán tổng sử dụng CPU (user + system)
                cpu_used_percent = round(usage_user + usage_system, 2)

                main_info.update({
                    'cpu_used_percent': cpu_used_percent,
                })
            # 👇 IP WAN: lấy từ ifconfig.co hoặc ipinfo.io
            elif name == 'ip_wan':
                main_info.update({
                    'ip_wan': fields.get('ip', ''),  # JSON trả về có key "ip"
                })
            # 👇 IP LAN: lấy từ PowerShell
            elif name == 'ip_lan':
                lan_ips = fields.get('lan_ips', [])
                if isinstance(lan_ips, list):
                    main_info.update({'ip_lan': ', '.join(lan_ips)})
                else:
                    main_info.update({'ip_lan': str(lan_ips)})

        return main_info

    def _store_disk_info(self, telegraf_data, metrics):
        disk_count = 0
        critical_disks = 0

        for metric in metrics:
            if metric.get('name') == 'disk':
                fields = metric.get('fields', {})
                used_percent = fields.get('used_percent', 0)

                # Tạo bản ghi thông tin đĩa
                request.env['telegraf.disk'].sudo().create({
                    'device': metric.get('tags', {}).get('device', 'Unknown'),
                    'total': fields.get('total', 0) / (1024 ** 3),
                    'used': fields.get('used', 0) / (1024 ** 3),
                    'free': fields.get('free', 0) / (1024 ** 3),
                    'used_percent': used_percent,
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })

                # Cập nhật số lượng đĩa và đĩa "critical"
                disk_count += 1
                if used_percent > 90:
                    critical_disks += 1

        # Cập nhật các trường mới trong telegraf_data
        telegraf_data.sudo().write({
            'disk_count': disk_count,
            'critical_disks': critical_disks,
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
        unique_urls = set()  # Tập hợp lưu các URL duy nhất
        error_urls = set()  # Tập hợp lưu các URL hỏng

        for metric in metrics:
            if metric.get('name') == 'http_response':
                fields, tags, url, http_response_code = self._extract_http_response_data(metric)

                # Lưu thông tin vào mô hình 'telegraf.http_response'
                self._create_http_response(telegraf_data, fields, tags, url, http_response_code)

                # Cập nhật hoặc tạo mới thông tin vào mô hình 'telegraf.http_response_notification'
                self._update_or_create_notification(telegraf_data, fields, url, http_response_code)

                # Quản lý unique_urls và error_urls
                if url not in unique_urls:
                    unique_urls.add(url)
                    if http_response_code not in [200, 302]:
                        error_urls.add(url)

        # Cập nhật số lượng web và web lỗi
        self._update_telegraf_data(telegraf_data, unique_urls, error_urls)

    def _extract_http_response_data(self, metric):
        fields = metric.get('fields', {})
        tags = metric.get('tags', {})
        url = tags.get('server', 'Unknown')
        http_response_code = fields.get('http_response_code', 0)
        return fields, tags, url, http_response_code

    def _create_http_response(self, telegraf_data, fields, tags, url, http_response_code):
        request.env['telegraf.http_response'].sudo().create({
            'url': url,
            'response_time': fields.get('response_time', 0),
            'http_response_code': http_response_code,
            'content_length': fields.get('content_length', 0),
            'result_type': fields.get('result_type', 'Unknown'),
            'timestamp': datetime.now(),
            'telegraf_data_id': telegraf_data.id,
        })

    def _update_or_create_notification(self, telegraf_data, fields, url, http_response_code):
        notification_model = request.env['telegraf.http_response_notification'].sudo()
        existing_notification = notification_model.search([
            ('url', '=', url),
            ('telegraf_data_id', '=', telegraf_data.id)
        ], limit=1)

        if existing_notification:
            existing_notification.write({
                'response_time': fields.get('response_time', 0),
                'http_response_code': http_response_code,
                'content_length': fields.get('content_length', 0),
                'result_type': fields.get('result_type', 'Unknown'),
                'timestamp': datetime.now(),
            })
        else:
            notification_model.create({
                'url': url,
                'response_time': fields.get('response_time', 0),
                'http_response_code': http_response_code,
                'content_length': fields.get('content_length', 0),
                'result_type': fields.get('result_type', 'Unknown'),
                'timestamp': datetime.now(),
                'telegraf_data_id': telegraf_data.id,
            })

    def _update_telegraf_data(self, telegraf_data, unique_urls, error_urls):
        request.env['telegraf.data'].sudo().browse(telegraf_data.id).write({
            'web_count': len(unique_urls),  # Số lượng web là kích thước của tập hợp unique_urls
            'web_error_count': len(error_urls),  # Số lượng web hỏng là kích thước của tập hợp error_urls
        })

    def _store_login_attempts(self, telegraf_data, metrics):
        # Store login attempt information in one2many relation
        for metric in metrics:
            # Kiểm tra nguồn dữ liệu (Windows hoặc Ubuntu)
            if metric.get("name") == "win_eventlog" and metric.get("tags", {}).get("EventID") in ["4625", "4624"]:
                # Xử lý đăng nhập từ Windows Event Log
                login_status = 'success' if metric["tags"]["EventID"] == "4624" else 'failure'
                failure_reason = metric["fields"].get("Data_FailureReason", '') if login_status == 'failure' else ''

                # Chuyển đổi thời gian từ định dạng ISO 8601 và loại bỏ thông tin múi giờ
                time_created = metric["fields"].get("TimeCreated", datetime.now())
                if isinstance(time_created, str):  # Kiểm tra xem có phải là chuỗi hay không
                    time_created = parser.isoparse(time_created).replace(tzinfo=None)  # Chuyển đổi sang naive datetime

                # Tạo bản ghi trong hệ thống
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

            elif metric.get("name") == "tail":  # Xử lý log từ Ubuntu
                # Phân tích log đăng nhập từ Ubuntu
                login_status = metric["fields"].get("status", "unknown")
                time_created = metric["fields"].get("timestamp", datetime.now())
                if isinstance(time_created, str):  # Chuyển đổi chuỗi thời gian
                    time_created = parser.isoparse(time_created).replace(tzinfo=None)

                # Tạo bản ghi trong hệ thống
                request.env['login.attempt'].sudo().create({
                    'login_date': time_created,
                    'username': metric["fields"].get("user", "Unknown"),
                    'ip_address': metric["fields"].get("ip", "Unknown"),
                    'status': login_status,
                    'failure_reason': '',  # Không có thông tin lỗi từ Ubuntu log
                    'process_name': '',  # Không có thông tin process từ Ubuntu log
                    'logon_type': '',  # Không có loại đăng nhập từ Ubuntu log
                    'event_id': '',  # Không có EventID từ Ubuntu log
                    'logon_domain': '',  # Không có domain từ Ubuntu log
                    'timestamp': datetime.now(),
                    'telegraf_data_id': telegraf_data.id,
                })
