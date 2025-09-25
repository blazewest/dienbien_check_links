from odoo import http
from odoo.http import request
import json
from datetime import date


class InfoSQLController(http.Controller):

    @http.route('/info_sql', type='http', auth='public', methods=['POST'], csrf=False)
    def info_sql(self, **kwargs):
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

        today = date.today()
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

            # === Schema Info ===
            for s in schema_info:
                table_name = s.get('TableName')
                col_name = s.get('ColumnName')
                data_type = s.get('DataType')

                existing = request.env['table.sql'].sudo().search([
                    ('database_id', '=', db_rec.id),
                    ('name_table', '=', table_name),
                    ('column_name', '=', col_name),
                    ('record_date', '=', today),
                ], limit=1)

                if existing:
                    existing.write({
                        'data_type': data_type,
                    })
                    table_ids.append(existing.id)
                else:
                    table_rec = request.env['table.sql'].sudo().create({
                        'name_table': table_name,
                        'column_name': col_name,
                        'data_type': data_type,
                        'record_date': today,
                        'database_id': db_rec.id,
                    })
                    table_ids.append(table_rec.id)

            # === Row Counts ===
            for r in row_counts:
                table_name = r.get('TableName')
                total_rows = r.get('TotalRows')

                existing = request.env['sum.record.sql'].sudo().search([
                    ('database_id', '=', db_rec.id),
                    ('name_table', '=', table_name),
                    ('record_date', '=', today),
                ], limit=1)

                if existing:
                    existing.write({'sum_record': total_rows})
                    row_count_ids.append(existing.id)
                else:
                    row_rec = request.env['sum.record.sql'].sudo().create({
                        'name_table': table_name,
                        'sum_record': total_rows,
                        'record_date': today,
                        'database_id': db_rec.id,
                    })
                    row_count_ids.append(row_rec.id)

            # Gắn Many2many
            if table_ids:
                db_rec.write({'table_ids': [(4, tid) for tid in table_ids]})
            if row_count_ids:
                db_rec.write({'sum_record_ids': [(4, rid) for rid in row_count_ids]})

            results.append({
                "database": db_name,
                "updated_tables": len(table_ids),
                "updated_rows": len(row_count_ids),
            })

        return request.make_json_response({"status": "success", "details": results})
