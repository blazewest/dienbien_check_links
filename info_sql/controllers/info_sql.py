from odoo import http, fields
from odoo.http import request
import json


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

        today = fields.Date.context_today(request.env.user)

        results = []

        for payload in payloads:
            db_rec = self._get_or_create_database(
                db_name=payload.get('database_name'),
                sql_server=payload.get('sql_sever'),
                host=payload.get('host'),
            )
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

    def _get_or_create_database(self, db_name, sql_server, host):
        """Tìm hoặc tạo database.sql theo name + sql_seversql + telegraf_data_id.host"""
        Database = request.env['database.sql'].sudo()

        db_rec = Database.search([
            ('name', '=', db_name),
            ('sql_seversql', '=', sql_server),
            ('telegraf_data_id.host', '=', host),
        ], limit=1)

        if db_rec:
            # cập nhật nếu có thay đổi
            db_rec.write({
                'name': db_name,
                'sql_seversql': sql_server,
            })
        else:
            # tìm telegraf.data có host phù hợp
            telegraf_rec = request.env['telegraf.data'].sudo().search([('host', '=', host)], limit=1)

            db_rec = Database.create({
                'name': db_name,
                'sql_seversql': sql_server,
                'telegraf_data_id': telegraf_rec.id if telegraf_rec else False,
            })

        return db_rec

    def _process_schema_info(self, db_rec, schema_info, today):
        """Xử lý schema_info (tạo/cập nhật bảng theo ngày; columns lưu theo database)"""
        table_ids = []
        Table = request.env['table.sql'].sudo()
        Column = request.env['table.column.sql'].sudo()

        tables_cache = {}

        for s in schema_info:
            table_name = s.get('TableName')
            col_name = s.get('ColumnName')
            data_type = s.get('DataType')

            if not table_name:
                continue

            # --- xử lý bảng ---
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

            # --- xử lý column ---
            if col_name:
                col_rec = Column.search([
                    ('database_id', '=', db_rec.id),
                    ('column_name', '=', col_name),
                    ('name_table', '=', table_name),  # ✅ thêm điều kiện name_table
                ], limit=1)

                if col_rec:
                    col_rec.write({'data_type': data_type})
                else:
                    Column.create({
                        'column_name': col_name,
                        'data_type': data_type,
                        'database_id': db_rec.id,
                        'name_table': table_name,  # ✅ lưu luôn tên bảng
                    })

            table_ids.append(table_rec.id)

        return table_ids

    def _process_row_counts(self, db_rec, row_counts, today):
        """Cập nhật sum_record trực tiếp trong table.sql (theo db, host, name, table)"""
        updated = 0
        Table = request.env['table.sql'].sudo()
        table_cache = {}

        for r in row_counts:
            table_name = r.get('TableName')
            total_rows = r.get('TotalRows')

            if not table_name:
                continue

            # cache theo key (db_id + table_name + date)
            cache_key = (db_rec.id, table_name, today)

            table_rec = table_cache.get(cache_key)
            if not table_rec:
                table_rec = Table.search([
                    ('database_id', '=', db_rec.id),
                    ('name_table', '=', table_name),
                    ('record_date', '=', today),
                ], limit=1)

            if table_rec:
                table_rec.write({'sum_record': total_rows or 0})
                table_cache[cache_key] = table_rec
            else:
                new_rec = Table.create({
                    'name_table': table_name,
                    'sum_record': total_rows or 0,
                    'record_date': today,
                    'database_id': db_rec.id,
                })
                table_cache[cache_key] = new_rec
            updated += 1

        return updated


