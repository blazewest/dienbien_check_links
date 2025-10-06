from odoo import models, fields, api

class CertificateInfo(models.Model):
    _name = 'certificate.info'
    _description = 'Thông tin Chứng Thư Số (CTS)'

    name = fields.Char("CN")  # CN
    loai_cts = fields.Char("Loại CTS")  # Loại CTS
    to_chuc = fields.Text("Tổ chức gốc")  # Chuỗi gốc
    to_chuc_phuong = fields.Char("Tổ chức Phường")  # Phần giữa
    to_chuc_truong = fields.Char("Tổ chức Trường")  # Phần cuối

    @api.model
    def create(self, vals):
        """Tự động tách chuỗi Tổ chức khi tạo mới"""
        if vals.get('to_chuc'):
            parts = [p.strip() for p in vals['to_chuc'].split(';') if p.strip()]
            if len(parts) >= 2:
                vals['to_chuc_phuong'] = parts[1]
            if len(parts) >= 3:
                vals['to_chuc_truong'] = parts[2]
            else:
                vals['to_chuc_truong'] = vals.get('to_chuc_phuong')
        return super(CertificateInfo, self).create(vals)

    def write(self, vals):
        """Tự động cập nhật khi sửa dữ liệu"""
        if vals.get('to_chuc'):
            parts = [p.strip() for p in vals['to_chuc'].split(';') if p.strip()]
            if len(parts) >= 2:
                vals['to_chuc_phuong'] = parts[1]
            if len(parts) >= 3:
                vals['to_chuc_truong'] = parts[2]
            else:
                vals['to_chuc_truong'] = vals.get('to_chuc_phuong')
        return super(CertificateInfo, self).write(vals)
