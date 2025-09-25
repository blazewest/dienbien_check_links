from odoo import http
from odoo.http import request
import json


class InfoSQLController(http.Controller):

    @http.route('/info_sql', type='http', auth='public', methods=['POST'], csrf=False)
    def info_sql(self, **kwargs):
        # Lấy raw body
        try:
            data = request.httprequest.get_data().decode('utf-8')
            payloads = json.loads(data)
        except Exception:
            return request.make_json_response(
                {"status": "error", "message": "Invalid JSON"},
                status=400
            )

        if not isinstance(payloads, list):
            payloads = [payloads]

        results = []
        for payload in payloads:
            db_name = payload.get('database_name')
            schema_info = payload.get('schema_info', [])
            row_counts = payload.get('table_row_counts', [])

            # Tìm hoặc tạo database
            db_rec = request.env['database.sql'].sudo().search([('name', '=', db_name)], limit=1)
            if not db_rec:
                db_rec = request.env['database.sql'].sudo().create({'name': db_name})

            table_ids = []
            row_count_ids = []

            # Tạo schema info
            for s in schema_info:
                table_rec = request.env['table.sql'].sudo().create({
                    'name_table': s.get('TableName'),
                    'column_name': s.get('ColumnName'),
                    'data_type': s.get('DataType'),
                })
                table_ids.append(table_rec.id)

            # Tạo row counts
            for r in row_counts:
                row_rec = request.env['sum.record.sql'].sudo().create({
                    'name_table': r.get('TableName'),
                    'sum_record': r.get('TotalRows'),
                })
                row_count_ids.append(row_rec.id)

            # Gắn Many2many (append, không xóa cũ)
            if table_ids:
                db_rec.write({'table_ids': [(4, tid) for tid in table_ids]})
            if row_count_ids:
                db_rec.write({'sum_record_ids': [(4, rid) for rid in row_count_ids]})

            results.append({
                "database": db_name,
                "added_tables": len(table_ids),
                "added_rows": len(row_count_ids),
            })

        return request.make_json_response({"status": "success", "details": results})
