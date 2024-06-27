from odoo import models, fields, api

_LOG_API_ZALO = {
    "0": "Gửi thành công",
    "-100": "Xảy ra lỗi không xác định, vui lòng thử lại sau",
    "-101": "Ứng dụng không hợp lệ",
    "-102": "Ứng dụng không tồn tại",
    "-103": "Ứng dụng chưa được kích hoạt",
    "-104": "Secret key của ứng dụng không hợp lệ",
    "-105": "Ứng dụng gửi ZNS chưa đươc liên kết với OA nào",
    "-106": "Phương thức không được hỗ trợ",
    "-107": "ID thông báo không hợp lệ",
    "-108": "Số điện thoại không hợp lệ",
    "-109": "ID mẫu ZNS không hợp lệ",
    "-110": "Phiên bản Zalo app không được hỗ trợ. Người dùng cần cập nhật phiên bản mới nhất",
    "-111": "Mẫu ZNS không có dữ liệu",
    "-112": "Nội dung mẫu ZNS không hợp lệ",
    "-1123": "Không thể tạo QR code, vui lòng kiểm tra lại",
    "-113": "Button không hợp lệ",
    "-114": "Người dùng không nhận được ZNS vì các lý do: Trạng thái tài khoản, Tùy chọn nhận ZNS, Sử dụng Zalo phiên bản cũ, hoặc các lỗi nội bộ khác",
    "-115": "Tài khoản ZNS không đủ số dư",
    "-116": "Nội dung không hợp lệ",
    "-117": "OA hoặc ứng dụng gửi ZNS chưa được cấp quyền sử dụng mẫu ZNS này",
    "-118": "Tài khoản Zalo không tồn tại hoặc đã bị vô hiệu hoá",
    "-119": "Tài khoản không thể nhận ZNS",
    "-120": "OA chưa được cấp quyền sử dụng tính năng này",
    "-121": "Mẫu ZNS không có nội dung",
    "-122": "Body request không đúng định dạng JSON",
    "-123": "Giải mã nội dung thông báo RSA thất bại",
    "-124": "Mã truy cập không hợp lệ",
    "-125": "ID Official Account không hợp lệ",
    "-126": "Ví (development mode) không đủ số dư",
    "-127": "Template test chỉ có thể được gửi cho quản trị viên",
    "-128": "Mã encoding key không tồn tại",
    "-129": "Không thể tạo RSA key, vui lòng thử lại sau",
    "-130": "Nội dung mẫu ZNS vượt quá giới hạn kí tự",
    "-131": "Mẫu ZNS chưa được phê duyệt",
    "-132": "Tham số không hợp lệ",
    "-133": "Mẫu ZNS này không được phép gửi vào ban đêm (từ 22h-6h)",
    "-134": "Người dùng chưa phản hồi gợi ý nhận ZNS từ OA",
    "-135": "OA chưa có quyền gửi ZNS (chưa được xác thực, đang sử dụng gói miễn phí)",
    "-136": "Cần kết nối với ZCA để sử dụng tính năng này",
    "-137": "Thanh toán ZCA thất bại (ví không đủ số dư,…)",
    "-138": "Ứng dụng gửi ZNS chưa có quyền sử dụng tính năng này",
    "-139": "Người dùng từ chối nhận loại ZNS này",
    "-140": "OA chưa được cấp quyền gửi ZNS hậu mãi cho người dùng này",
    "-141": "Người dùng từ chối nhận ZNS từ Official Account",
    "-142": "RSA key không tồn tại, vui lòng gọi API tạo RSA key",
    "-143": "RSA key đã tồn tại, vui lòng gọi API lấy RSA key",
    "-144": "OA đã vượt giới hạn gửi ZNS trong ngày",
    "-145": "OA không được phép gửi loại nội dung ZNS này",
    "-146": "Mẫu ZNS này đã bị vô hiệu hóa do chất lượng gửi thấp",
    "-147": "Mẫu ZNS đã vượt giới hạn gửi trong ngày",
    "-148": "Không tìm thấy ZNS journey token",
    "-149": "ZNS journey token không hợp lệ",
    "-150": "ZNS journey token đã hết hạn",
    "-151": "Không phải mẫu ZNS E2EE",
    "-152": "Lấy E2EE key thất bại",
}


class ZaloLog(models.Model):
    _name = 'zalo.log'
    _description = 'zalo.log'

    messenger = fields.Char('Nội dung')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "messenger" in vals and "LOG" in vals["messenger"]:
                log = vals["messenger"]["LOG"]
                error = str(log.get('error'))
                if error in _LOG_API_ZALO:
                    vals["messenger"]["LOG"] = _LOG_API_ZALO[error]
                    # name = vals["messenger"]['Người Nhận']
                    phone = vals["messenger"]['SĐT']
                    # partner = self.env['res.partner'].search(
                    #     ['|', ('company_name', '=', name), ('name', '=', name), ('phone', '=', phone)], limit=1)
                    # if error in ('-114','-118','-119'):
                    #     partner.check_last_api_zalo = error
                    # elif error == '0' and (partner.check_last_api_zalo in ('-114','-118','-119')):
                    #     partner.check_last_api_zalo = error
        return super().create(vals_list)
