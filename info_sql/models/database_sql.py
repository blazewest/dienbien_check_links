from odoo import models, fields


class DatabaseSQL(models.Model):
    _name = 'database.sql'
    _description = 'Database SQL'

    name = fields.Char("Tên database", required=True)
    table_ids = fields.One2many(
        'table.sql',
        'database_id',
        string="Tables"
    )


class TableSQL(models.Model):
    _name = 'table.sql'
    _description = 'Table Info'

    name_table = fields.Char("Tên bảng", required=True)
    record_date = fields.Date("Ngày ghi nhận", default=fields.Date.context_today)
    sum_record = fields.Integer("Tổng số dữ liệu")   # thay cho sum.record.sql
    database_id = fields.Many2one('database.sql', string="Database")

    column_ids = fields.One2many('table.column.sql', 'table_id', string="Columns")


class TableColumnSQL(models.Model):
    _name = 'table.column.sql'
    _description = 'Table Column Info'

    column_name = fields.Char("Tên cột", required=True)
    data_type = fields.Char("Kiểu dữ liệu")
    table_id = fields.Many2one('table.sql', string="Table")
