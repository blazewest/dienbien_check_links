from odoo import models, fields, api

class VirtualMachine(models.Model):
    _name = 'virtual.machine'
    _description = 'Virtual Machine'

    name = fields.Char(string='Name', required=True)
    state = fields.Selection([
        ('powered_on', 'Powered On'),
        ('powered_off', 'Powered Off'),
    ], string='State', required=True)
    status = fields.Char(string='Status')
    provisioned_space = fields.Float(string='Provisioned Space (GB)', compute="_compute_provisioned_space", store=True)
    used_space = fields.Float(string='Used Space (GB)', compute="_compute_used_space", store=True)

    raw_provisioned_space = fields.Char(string="Raw Provisioned Space")  # Lưu trữ giá trị gốc từ file
    raw_used_space = fields.Char(string="Raw Used Space")  # Lưu trữ giá trị gốc từ file

    @api.depends('raw_provisioned_space')
    def _compute_provisioned_space(self):
        for record in self:
            record.provisioned_space = self._convert_to_gb(record.raw_provisioned_space)

    @api.depends('raw_used_space')
    def _compute_used_space(self):
        for record in self:
            record.used_space = self._convert_to_gb(record.raw_used_space)

    def _convert_to_gb(self, value):
        # Hàm chuyển đổi giá trị sang GB
        if 'TB' in value:
            return float(value.replace('TB', '').strip()) * 1024  # 1 TB = 1024 GB
        elif 'GB' in value:
            return float(value.replace('GB', '').strip())
        elif 'MB' in value:
            return float(value.replace('MB', '').strip()) / 1024  # 1 GB = 1024 MB
        # Thêm điều kiện khác nếu có đơn vị khác
        return 0.0  # Giá trị mặc định nếu không xác định được đơn vị


