from odoo import http
from odoo.http import request
import json
from datetime import date


class InfoSQLController(http.Controller):

    @http.route('/info_sql', type='http', auth='public', methods=['POST'], csrf=False)
    def info_sql(self, **kwargs):
        """API nhận dữ liệu database, schema, row count"""
        payloads = self._get_payloads()
        if not payloads:
            return request.make_json_response(
                {"status": "error", "message": "Invalid JSON"},
                status=400
            )

        today = date.today()
        results = []

        for payload in payloads:
            db_rec = self._get_or_create_database(payload.get('database_name'))
            schema_info = payload.get('schema_info', [])
            row_counts = payload.get('table_row_counts', [])

            table_ids = self._process_schema_info(db_rec, schema_info, today)
            row_count_ids = self._process_row_counts(db_rec, row_counts, today)

            # Gắn Many2many
            if table_ids:
                db_rec.write({'table_ids': [(4, tid) for tid in set(table_ids)]})
            if row_count_ids:
                db_rec.write({'sum_record_ids': [(4, rid) for rid in set(row_count_ids)]})

            results.append({
                "database": db_rec.name,
                "tables_processed": len(set(table_ids)),
                "rows_processed": len(set(row_count_ids)),
            })

        return request.make_json_response({"status": "success", "details": results})

    # ==========================
    # Helpers
    # ==========================

    def _get_payloads(self):
        """Đọc JSON từ request"""
        try:
            data = request.httprequest.get_data().decode('utf-8')
            payloads = json.loads(data)
            if not isinstance(payloads, list):
                payloads = [payloads]
            return payloads
        except Exception:
            return None

    def _get_or_create_database(self, db_name):
        """Tìm hoặc tạo database"""
        db_rec = request.env['database.sql'].sudo().search([('name', '=', db_name)], limit=1)
        if not db_rec:
            db_rec = request.env['database.sql'].sudo().create({'name': db_name})
        return db_rec

    def _process_schema_info(self, db_rec, schema_info, today):
        """Xử lý schema_info (bảng + cột)"""
        table_ids = []
        Table = request.env['table.sql'].sudo()
        Column = request.env['table.column.sql'].sudo()

        for s in schema_info:
            table_name = s.get('TableName')
            col_name = s.get('ColumnName')
            data_type = s.get('DataType')

            # Tìm hoặc tạo table (theo ngày)
            table_rec = Table.search([
                ('database_id', '=', db_rec.id),
                ('name_table', '=', table_name),
                ('record_date', '=', today),
            ], limit=1)

            if not table_rec:
                table_rec = Table.create({
                    'name_table': table_name,
                    'record_date': today,
                    'database_id': db_rec.id,
                })

            # Tìm hoặc tạo column
            col_rec = Column.search([
                ('table_id', '=', table_rec.id),
                ('column_name', '=', col_name),
            ], limit=1)

            if col_rec:
                col_rec.write({'data_type': data_type})
            else:
                Column.create({
                    'column_name': col_name,
                    'data_type': data_type,
                    'table_id': table_rec.id,
                })

            table_ids.append(table_rec.id)

        return table_ids

    def _process_row_counts(self, db_rec, row_counts, today):
        """Xử lý row_counts (tổng số dòng mỗi bảng)"""
        row_count_ids = []
        RowCount = request.env['sum.record.sql'].sudo()

        for r in row_counts:
            table_name = r.get('TableName')
            total_rows = r.get('TotalRows')

            row_rec = RowCount.search([
                ('database_id', '=', db_rec.id),
                ('name_table', '=', table_name),
                ('record_date', '=', today),
            ], limit=1)

            if row_rec:
                row_rec.write({'sum_record': total_rows})
            else:
                row_rec = RowCount.create({
                    'name_table': table_name,
                    'sum_record': total_rows,
                    'record_date': today,
                    'database_id': db_rec.id,
                })

            row_count_ids.append(row_rec.id)

        return row_count_ids
