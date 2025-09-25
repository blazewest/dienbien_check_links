from odoo import http
from odoo.http import request

class InfoSQLController(http.Controller):

    @http.route('/info_sql', type='json', auth='public', methods=['POST'], csrf=False)
    def info_sql(self, **kwargs):
        # Lấy dữ liệu JSON gửi đến
        data = request.jsonrequest
        print(data)
        return {
            "status": "success",
            "received": data
        }
