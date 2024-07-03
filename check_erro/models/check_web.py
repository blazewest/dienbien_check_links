import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from odoo import models, fields, api
from odoo.exceptions import UserError


class WebsiteStatus(models.Model):
    _name = 'website.status'
    _description = 'Website Status Checker'

    name = fields.Char('Website URL', required=True)
    bool_limit = fields.Boolean('Giới hạn quét links',default=True)
    bot_send_tele = fields.Many2one('telegram.bot','Bot telegram')
    qty_requests = fields.Integer('Số lần quét lại', default=3)
    qty_requests_false = fields.Integer('Số lần đã quét lại', readonly=True, default=0)
    # bool_send_zalo = fields.Boolean('Đã gửi tin nhắn quét lỗi', readonly=False, default=False)
    limit_url = fields.Integer('Giới hạn số lượng quét links', default=30,)
    status_code = fields.Char('Mã trạng thái trang chủ', compute='_compute_links',store=True, readonly=True, compute_sudo=True, default='200')
    status_message = fields.Char('Tin nhắn trạng thái', compute='_compute_links',store=True, readonly=True, compute_sudo=True, default='')
    qty_links = fields.Integer('Số lượng links kiểm tra', compute='_compute_links',store=True, default=0, compute_sudo=True)
    qty_status_true = fields.Integer('Số lượng links web hoạt động bình thường', compute='_compute_links',store=True, default=0, compute_sudo=True)
    qty_status_false = fields.Integer('Số lượng links web hỏng', compute='_compute_links', store=True, default=0, compute_sudo=True)
    status_links = fields.Text('Chi tiết trạng thái Links web', compute='_compute_links', store=True, readonly=True, compute_sudo=True)
    # responsible_user_ids = fields.One2many('hr.employee','check_web_id', string='Người phụ trách')


    @api.depends('name')
    def _compute_links(self):
        for record in self:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                session = requests.Session()
                response = session.get(record.name, headers=headers)
                record.status_code = str(response.status_code)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.find_all("a")
                    status_links = []
                    links_url = set()
                    qty_links_ok = 1
                    qty_links_error = 0
                    if record.bool_limit == True:
                        for link in links:
                            href = link.get("href")
                            if href:
                                href = href.strip()
                                full_url = urljoin(record.name, href)
                                parsed_url = urlparse(full_url)
                                if parsed_url.scheme in ['http', 'https'] and (len(links_url) < (record.limit_url - 1)):
                                    links_url.add(full_url)
                                elif (len(links_url) >= (record.limit_url - 1)):
                                    break
                    else:
                        for link in links:
                            href = link.get("href")
                            if href:
                                href = href.strip()
                                full_url = urljoin(record.name, href)
                                parsed_url = urlparse(full_url)
                                if parsed_url.scheme in ['http', 'https']:
                                    links_url.add(full_url)


                    for full_url in links_url:
                        try:
                            link_response = session.get(full_url, headers=headers)
                            if link_response.status_code == 200:
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
                else:
                    record.status_message = response.reason
            except requests.exceptions.RequestException as e:
                record.status_code = 'Error'
                record.status_message = str(e)
                record.qty_links = 1
                record.qty_status_true = 0
                record.qty_status_false = 1
                record.status_links = ''
                record.qty_requests_false += 1
                # self.env['code.processing'].create()

    def compute_links_cron(self):
        websites = self.search([])
        for website in websites:
            website.check_website_status()
            if website.qty_requests_false >= website.qty_requests:
                message = "Website URL: " + website.name + "\n" + "Mã trạng thái trang chủ: " + website.status_code
                website.bot_send_tele.send_message(message)

    # def compute_update_send_zalo(self):
    #     websites = self.search(['bool_send_zalo', '=', 'true'])
    #     if websites:
    #         for website in websites:
    #             website.bool_send_zalo = False

    def send_error_email(self, website):
        if not website.responsible_user_id.work_email:
            raise UserError("The responsible user does not have a work email.")
        template = self.env.ref('check_erro.email_template_website_status_error')
        self.env['mail.template'].browse(template.id).send_mail(website.id, force_send=True)

    # def send_quick_email(self):
    #     for record in self:
    #         if record.status_code != '200' and record.responsible_user_id and record.responsible_user_id.work_email:
    #             self.send_error_email(record)

    def check_website_status(self):
        for record in self:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                session = requests.Session()
                response = session.get(record.name, headers=headers)
                record.status_code = str(response.status_code)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.find_all("a")
                    status_links = []
                    links_url = set()
                    qty_links_ok = 1
                    qty_links_error = 0

                    if record.bool_limit == True:
                        for link in links:
                            href = link.get("href")
                            if href:
                                href = href.strip()
                                full_url = urljoin(record.name, href)
                                parsed_url = urlparse(full_url)
                                if parsed_url.scheme in ['http', 'https'] and (len(links_url) < (record.limit_url - 1)):
                                    links_url.add(full_url)
                                elif (len(links_url) >= (record.limit_url - 1)):
                                    break
                    else:
                        for link in links:
                            href = link.get("href")
                            if href:
                                href = href.strip()
                                full_url = urljoin(record.name, href)
                                parsed_url = urlparse(full_url)
                                if parsed_url.scheme in ['http', 'https']:
                                    links_url.add(full_url)

                    for full_url in links_url:
                        try:
                            link_response = session.get(full_url, headers=headers)
                            if link_response.status_code == 200:
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
                else:
                    record.status_message = response.reason
            except requests.exceptions.RequestException as e:
                record.status_code = 'Error'
                record.status_message = str(e)
                record.qty_links = 1
                record.qty_status_true = 0
                record.qty_status_false = 1
                record.status_links = ''
                record.qty_requests_false += 1
                if record.qty_requests_false >= record.qty_requests:
                    message = "Website URL: " + record.name + "\n" + "Mã trạng thái trang chủ: " + record.status_code
                    record.bot_send_tele.send_message(message)
