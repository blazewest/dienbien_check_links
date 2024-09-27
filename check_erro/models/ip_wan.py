from odoo import models, fields, api
from odoo.exceptions import ValidationError

class IpWan(models.Model):
    _name = 'ip.wan'
    _description = 'IP Wan'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Đã kế thừa sẵn tracking

    name = fields.Char("domain", tracking=True)  # Theo dõi thay đổi của trường 'name'
    info_ip = fields.Char(string='IP WAN', required=False, tracking=True)  # Theo dõi thay đổi trường 'info_ip'
    Ngay = fields.Date(string='Ngày Khởi tạo', required=False, tracking=True)  # Theo dõi thay đổi trường 'Ngay'

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            # Kiểm tra xem đã có bản ghi nào với cùng giá trị 'name' chưa
            existing_domain = self.search([('name', '=', record.name), ('id', '!=', record.id)])
            if existing_domain:
                raise ValidationError("Tên domain '{}' đã tồn tại. Vui lòng chọn tên khác.".format(record.name))
