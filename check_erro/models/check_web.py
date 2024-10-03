import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import random


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36',
]


class WebsiteStatus(models.Model):
    _name = 'website.status'
    _description = 'Website Status Checker'


    name = fields.Char('Website URL', required=True)
    bool_limit = fields.Boolean('Giới hạn quét links',default=True)
    bot_send_tele = fields.Many2one('telegram.bot','Bot telegram')
    qty_requests = fields.Integer('Số lần quét lại', default=3)
    qty_requests_false = fields.Integer('Số lần đã quét lại', readonly=True, default=0)
    limit_url = fields.Integer('Giới hạn số lượng quét links', default=10)
    status_code = fields.Char('Mã trạng thái trang chủ',store=True, readonly=True, compute_sudo=True, default='200')
    status_message = fields.Char('Tin nhắn trạng thái', store=True, readonly=True, compute_sudo=True, default='')
    qty_links = fields.Integer('Số lượng links kiểm tra', store=True, default=0, compute_sudo=True)
    qty_status_true = fields.Integer('Số lượng links web hoạt động bình thường', store=True, default=0, compute_sudo=True)
    qty_status_false = fields.Integer('Số lượng links web hỏng',  store=True, default=0, compute_sudo=True)
    status_links = fields.Text('Chi tiết trạng thái Links web',  store=True, readonly=True, compute_sudo=True)
    bool_request = fields.Boolean('request chậm',default=True)
    status_code_last = fields.Selection([('activity', 'activity'), ('stopped', 'stopped')], default='activity')


    def compute_links_cron(self):
        websites = self.search([('bot_send_tele.name', '=', 'dienbiet_bot_icd')])
        for website in websites:
            website.check_fast()
            if website.qty_requests_false >= website.qty_requests:
                message = (f"Website URL: <a href='{website.name}'>{website.name}</a>\nMã : {website.status_code}"
                           f"\n🔴 Down")
                website.bot_send_tele.send_message(message, parse_mode='HTML')
                website.status_code_last = "stopped"
            elif website.status_code_last == "stopped" and website.status_code == "200":
                message = (
                    f"Website URL: <a href='{website.name}'>{website.name}</a>\nMã : {website.status_code}"
                    f"\n🔵 Up")
                website.bot_send_tele.send_message(message, parse_mode='HTML')
                website.status_code_last = "activity"

    def compute_links_cron_hscv(self):
        websites = self.search([('bot_send_tele.name', '=', 'HSCV')])
        for website in websites:
            website.check_fast()
            if website.qty_requests_false >= website.qty_requests:

                message = (f"Website URL: <a href='{website.name}'>{website.name}</a>\nMã : {website.status_code}"
                           f"\n🔴 Down")
                website.bot_send_tele.send_message(message, parse_mode='HTML')
                website.status_code_last = "stopped"
            elif website.status_code_last == "stopped" and website.status_code == "200":
                message = (
                    f"Website URL: <a href='{website.name}'>{website.name}</a>\nMã : {website.status_code}"
                    f"\n🔵 Up")
                website.bot_send_tele.send_message(message, parse_mode='HTML')
                website.status_code_last = "activity"

    def check_website_status(self):
        for record in self:
            # Khởi tạo giá trị mặc định cho các thuộc tính
            record.qty_links = 0
            record.qty_status_true = 0
            record.qty_status_false = 0
            record.status_links = ''
            record.qty_requests_false = getattr(record, 'qty_requests_false', 0)

            # Kiểm tra cả http và https
            for protocol in ['http', 'https']:
                try:
                    url = f"{protocol}://{record.name}"
                    session = requests.Session()
                    response = session.get(url, verify=False, timeout=5)
                    record.status_code = str(response.status_code)

                    if response.status_code == "200":
                        soup = BeautifulSoup(response.text, "html.parser")
                        links = soup.find_all("a")
                        status_links = []
                        links_url = set()
                        qty_links_ok = 1
                        qty_links_error = 0

                        # Kiểm tra giới hạn số lượng link nếu có
                        if record.bool_limit:
                            for link in links:
                                href = link.get("href")
                                if href:
                                    href = href.strip()
                                    full_url = urljoin(url, href)
                                    parsed_url = urlparse(full_url)
                                    if parsed_url.scheme in ['http', 'https'] and len(links_url) < (
                                            record.limit_url - 1):
                                        links_url.add(full_url)
                                    elif len(links_url) >= (record.limit_url - 1):
                                        break
                        else:
                            for link in links:
                                href = link.get("href")
                                if href:
                                    href = href.strip()
                                    full_url = urljoin(url, href)
                                    parsed_url = urlparse(full_url)
                                    if parsed_url.scheme in ['http', 'https']:
                                        links_url.add(full_url)

                        # Kiểm tra trạng thái của từng link được thu thập
                        for full_url in links_url:
                            try:
                                link_response = session.get(full_url, verify=False, timeout=5)
                                if link_response.status_code == "200":
                                    status_links.append(f"{full_url} - OK")
                                    qty_links_ok += 1
                                else:
                                    status_links.insert(0,
                                                        f"{full_url} - {link_response.status_code} {link_response.reason}")
                                    qty_links_error += 1
                            except requests.exceptions.RequestException as e:
                                status_links.insert(0, f"{full_url} - Error: {str(e)}")
                                qty_links_error += 1

                        qty_links = qty_links_ok + qty_links_error
                        record.qty_links = qty_links
                        record.qty_status_true = qty_links_ok
                        record.qty_status_false = qty_links_error
                        record.status_links = '\n'.join(status_links)
                        record.status_message = 'OK'
                        record.qty_requests_false = 0
                        break  # Thoát khỏi vòng lặp nếu tìm thấy kết nối thành công
                    else:
                        record.qty_links = 1
                        record.qty_status_true = 0
                        record.qty_status_false = 1
                        record.status_links = ''
                        record.qty_requests_false += 1
                        record.status_message = response.reason
                except requests.exceptions.RequestException as e:
                    record.status_code = 'Error'
                    record.status_message = str(e)
                    record.qty_links = 1
                    record.qty_status_true = 0
                    record.qty_status_false = 1
                    record.status_links = ''
                    record.qty_requests_false += 1

    def check_fast(self):
        def fetch_status(record):
            # Khởi tạo giá trị mặc định cho record
            record.qty_links = 1
            record.qty_status_true = 0
            record.qty_status_false = 0
            record.qty_requests_false = getattr(record, 'qty_requests_false', 0)
            record.status_code = ''
            record.status_message = ''

            headers = {
                'User-Agent': random.choice(user_agents)
            }

            # Hàm phụ để kiểm tra giao thức
            def check_protocol(protocol):
                url = f"{protocol}://{record.name}"
                try:
                    response = requests.get(url, headers=headers, verify=False)
                    return response.status_code, response.reason
                except requests.exceptions.RequestException as e:
                    return 'Error', str(e)

            # Kiểm tra cả http và https đồng thời
            with ThreadPoolExecutor(max_workers=2) as proto_executor:
                protocols = ['http', 'https']
                futures = {proto_executor.submit(check_protocol, proto): proto for proto in protocols}

                results = []
                for future in as_completed(futures):
                    status_code, reason = future.result()
                    results.append((status_code, reason))

            # Xử lý kết quả từ cả http và https
            for status_code, reason in results:
                if status_code == 200:
                    record.status_code = '200'
                    record.status_message = 'OK'
                    record.qty_status_true = 1
                    record.qty_status_false = 0
                    record.qty_requests_false = 0
                    break  # Nếu một giao thức thành công, dừng kiểm tra
                else:
                    record.status_code = str(status_code)
                    record.status_message = reason

            # Nếu cả hai giao thức đều thất bại, tăng số lần lỗi
            if record.qty_status_true == 0:
                record.qty_status_false = 1
                record.qty_requests_false += 1

        # Sử dụng ThreadPoolExecutor để kiểm tra song song nhiều record
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(fetch_status, record): record for record in self}
            for future in as_completed(futures):
                future_to_record = futures[future]
