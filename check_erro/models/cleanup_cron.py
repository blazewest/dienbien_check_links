from odoo import models, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CleanupCron(models.TransientModel):
    _name = "cleanup.cron"
    _description = "Cron job cleanup old records"

    @api.model
    def cleanup_old_records(self, batch_size=1000):
        """Xóa dữ liệu cũ hơn 1 tháng, mỗi lần xóa batch_size bản ghi"""
        limit_date = datetime.today() - timedelta(days=30)
        models_to_clean = [
            "telegraf.http_response",
            "login.attempt",
            "telegraf.port_response",
            "telegraf.disk",
        ]

        for model in models_to_clean:
            try:
                # lấy 1000 bản ghi cũ nhất
                records = self.env[model].search(
                    [("create_date", "<", limit_date)],
                    order="create_date asc",
                    limit=batch_size
                )
                count = len(records)
                if count:
                    records.unlink()
                    _logger.info("Đã xóa %s bản ghi trong %s", count, model)
                else:
                    _logger.info("Không còn dữ liệu cũ trong %s", model)
            except Exception as e:
                _logger.error("Lỗi khi xóa %s: %s", model, str(e))
