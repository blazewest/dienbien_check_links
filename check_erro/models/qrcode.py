from odoo import models, fields, api
import qrcode
import base64
from io import BytesIO

class QRCodeGenerator(models.Model):
    _name = 'qr.code.generator'
    _description = 'QR Code Generator'

    name = fields.Char(string="Đường Link", required=True)  # Đầu vào là đường link
    qr_code = fields.Binary(string="Mã QR", readonly=True)  # Ảnh QR được lưu dưới dạng Binary
    qr_code_name = fields.Char(string="Tên file QR", readonly=True)  # Tên của file QR

    @api.model
    def create(self, vals):
        record = super(QRCodeGenerator, self).create(vals)
        # Gọi hàm tạo mã QR sau khi tạo bản ghi mới
        record.generate_qr_code()
        return record

    def generate_qr_code(self):
        for record in self:
            if record.name:
                # Tạo mã QR từ đường link
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.name)
                qr.make(fit=True)

                # Tạo hình ảnh QR
                img = qr.make_image(fill='black', back_color='white')

                # Lưu ảnh QR vào bộ nhớ dưới dạng base64
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_image = base64.b64encode(buffer.getvalue())

                # Cập nhật bản ghi với ảnh QR và tên file
                record.write({
                    'qr_code': qr_image,
                    'qr_code_name': record.name.replace(' ', '_') + '_qrcode.png'
                })

    def download_qr(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=qr.code.generator&id=%s&field=qr_code&download=true&filename=%s' % (
            self.id, self.qr_code_name),
            'target': 'self',
        }
