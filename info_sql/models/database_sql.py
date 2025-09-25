from odoo import models, fields


class DatabaseSQL(models.Model):
    _name = 'database.sql'
    _description = 'Database SQL'

    name = fields.Char("Tên database", required=True)
    table_ids = fields.Many2many(
        'table.sql',
        'rel_database_table',
        'database_id',
        'table_id',
        string="Tables"
    )
    sum_record_ids = fields.Many2many(
        'sum.record.sql',
        'rel_database_sumrecord',
        'database_id',
        'sum_id',
        string="Row Counts"
    )


class TableSQL(models.Model):
    _name = 'table.sql'
    _description = 'Table Schema Info'

    name_table = fields.Char("Tên bảng", required=True)
    column_name = fields.Char("Tên cột")
    data_type = fields.Char("Kiểu dữ liệu")
    record_date = fields.Date("Ngày ghi nhận", default=fields.Date.context_today)
    database_id = fields.Many2one('database.sql', string="Database")


class SumRecordSQL(models.Model):
    _name = 'sum.record.sql'
    _description = 'Table Row Counts'

    name_table = fields.Char("Tên bảng", required=True)
    sum_record = fields.Integer("Tổng số dữ liệu")
    record_date = fields.Date("Ngày ghi nhận", default=fields.Date.context_today)
    database_id = fields.Many2one('database.sql', string="Database")
