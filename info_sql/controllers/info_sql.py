from odoo import http, fields
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

        # DÙNG fields.Date.context_today để đảm bảo định dạng giống Odoo và tôn trọng timezone/context
        today = fields.Date.context_today(request.env.user)  # -> 'YYYY-MM-DD' string

        results = []

        for payload in payloads:
            db_rec = self._get_or_create_database(payload.get('database_name'))
            schema_info = payload.get('schema_info', [])
            row_counts = payload.get('table_row_counts', [])

            table_ids = self._process_schema_info(db_rec, schema_info, today)
            updated_tables = self._process_row_counts(db_rec, row_counts, today)

            results.append({
                "database": db_rec.name,
                "tables_processed": len(set(table_ids)),
                "rows_updated": updated_tables,
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
        """Xử lý schema_info (tạo/cập nhật bảng theo ngày; columns lưu theo database)"""
        table_ids = []
        Table = request.env['table.sql'].sudo()
        Column = request.env['table.column.sql'].sudo()

        # cache local: tránh search/create nhiều lần cho cùng 1 table trong 1 request
        tables_cache = {}

        for s in schema_info:
            table_name = s.get('TableName')
            col_name = s.get('ColumnName')
            data_type = s.get('DataType')

            if not table_name:
                continue

            # lấy từ cache trước
            table_rec = tables_cache.get(table_name)
            if not table_rec:
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
                tables_cache[table_name] = table_rec

            # Columns: lưu/cập nhật theo database (không theo ngày)
            if col_name:
                col_rec = Column.search([
                    ('database_id', '=', db_rec.id),
                    ('column_name', '=', col_name),
                ], limit=1)

                if col_rec:
                    col_rec.write({'data_type': data_type})
                else:
                    Column.create({
                        'column_name': col_name,
                        'data_type': data_type,
                        'database_id': db_rec.id,
                    })

            table_ids.append(table_rec.id)

        return table_ids

    def _process_row_counts(self, db_rec, row_counts, today):
        """Cập nhật sum_record trực tiếp trong table.sql"""
        updated = 0
        Table = request.env['table.sql'].sudo()

        # cache table records by name to giảm search
        table_cache = {}

        for r in row_counts:
            table_name = r.get('TableName')
            total_rows = r.get('TotalRows')

            if not table_name:
                continue

            table_rec = table_cache.get(table_name)
            if not table_rec:
                table_rec = Table.search([
                    ('database_id', '=', db_rec.id),
                    ('name_table', '=', table_name),
                    ('record_date', '=', today),
                ], limit=1)

            if table_rec:
                table_rec.write({'sum_record': total_rows or 0})
                updated += 1
                table_cache[table_name] = table_rec
            else:
                # tạo mới nếu chưa có
                new_rec = Table.create({
                    'name_table': table_name,
                    'sum_record': total_rows or 0,
                    'record_date': today,
                    'database_id': db_rec.id,
                })
                table_cache[table_name] = new_rec
                updated += 1

        return updated