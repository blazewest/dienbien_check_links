from odoo import models, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class CleanupCron(models.TransientModel):
    _name = "cleanup.cron"
    _description = "Cron job cleanup old records"

    @api.model
    def cleanup_old_records(self, batch_size=1000):
        """Gọi các hàm xóa dữ liệu cũ theo từng model"""
        self._cleanup_http_response(batch_size)
        self._cleanup_disk(batch_size)
        self._cleanup_login_attempt(batch_size)
        self._cleanup_port_response(batch_size)

    def _cleanup_http_response(self, batch_size):
        """Xóa bản ghi cũ trong telegraf.http_response, giữ lại 1 bản ghi mới nhất mỗi ngày cho mỗi URL"""
        model_name = "telegraf.http_response"
        limit_date = datetime.today() - timedelta(days=30)

        try:
            # Lấy tất cả URL có bản ghi cũ
            urls = self.env[model_name].search([
                ("create_date", "<", limit_date)
            ]).mapped("url")

            for url in set(urls):  # Duyệt từng URL duy nhất
                # Lấy danh sách ngày có dữ liệu cũ cho URL này
                records = self.env[model_name].search([
                    ("url", "=", url),
                    ("create_date", "<", limit_date)
                ], order="create_date asc")

                # Nhóm theo ngày (giữ lại 1 bản ghi mới nhất mỗi ngày)
                daily_groups = {}
                for rec in records:
                    day = rec.create_date.date()  # Nhóm theo ngày
                    if day not in daily_groups:
                        daily_groups[day] = []
                    daily_groups[day].append(rec.id)

                # Với mỗi ngày, giữ lại bản ghi mới nhất (id lớn nhất), xóa các bản ghi còn lại
                ids_to_delete = []
                for day, ids in daily_groups.items():
                    if len(ids) > 1:
                        # Giữ lại id lớn nhất (mới nhất), xóa các id còn lại
                        ids_to_delete.extend(sorted(ids)[:-1])  # Loại bỏ id lớn nhất
                    # Nếu chỉ có 1 bản ghi trong ngày → vẫn xóa (vì quá hạn và không cần giữ nếu không có yêu cầu đặc biệt)
                    else:
                        ids_to_delete.extend(ids)

                # Giới hạn batch_size
                ids_to_delete = ids_to_delete[:batch_size]
                if ids_to_delete:
                    records_to_delete = self.env[model_name].browse(ids_to_delete)
                    count = len(records_to_delete)
                    records_to_delete.unlink()
                    _logger.info("Đã xóa %s bản ghi cũ của URL '%s' trong %s", count, url, model_name)
                else:
                    _logger.info("Không có bản ghi cũ cần xóa cho URL '%s' trong %s", url, model_name)

        except Exception as e:
            _logger.error("Lỗi khi xử lý dọn dẹp %s: %s", model_name, str(e))

    def _cleanup_disk(self, batch_size):
        """Xóa bản ghi cũ trong telegraf.disk, giữ lại 1 bản ghi mới nhất mỗi ngày cho mỗi device"""
        model_name = "telegraf.disk"
        limit_date = datetime.today() - timedelta(days=30)

        try:
            # Lấy tất cả device có bản ghi cũ
            devices = self.env[model_name].search([
                ("create_date", "<", limit_date)
            ]).mapped("device")

            for device in set(devices):
                records = self.env[model_name].search([
                    ("device", "=", device),
                    ("create_date", "<", limit_date)
                ], order="create_date asc")

                # Nhóm theo ngày
                daily_groups = {}
                for rec in records:
                    day = rec.create_date.date()
                    if day not in daily_groups:
                        daily_groups[day] = []
                    daily_groups[day].append(rec.id)

                # Giữ lại bản ghi mới nhất (id lớn nhất) mỗi ngày, xóa các bản ghi còn lại
                ids_to_delete = []
                for day, ids in daily_groups.items():
                    if len(ids) > 1:
                        ids_to_delete.extend(sorted(ids)[:-1])
                    else:
                        ids_to_delete.extend(ids)

                # Giới hạn batch_size
                ids_to_delete = ids_to_delete[:batch_size]
                if ids_to_delete:
                    records_to_delete = self.env[model_name].browse(ids_to_delete)
                    count = len(records_to_delete)
                    records_to_delete.unlink()
                    _logger.info("Đã xóa %s bản ghi cũ của device '%s' trong %s", count, device, model_name)
                else:
                    _logger.info("Không có bản ghi cũ cần xóa cho device '%s' trong %s", device, model_name)

        except Exception as e:
            _logger.error("Lỗi khi xử lý dọn dẹp %s: %s", model_name, str(e))

    def _cleanup_login_attempt(self, batch_size):
        """Xóa toàn bộ bản ghi cũ trong login.attempt (> 1 tháng)"""
        self._cleanup_simple_model("login.attempt", batch_size)

    def _cleanup_port_response(self, batch_size):
        """Xóa toàn bộ bản ghi cũ trong telegraf.port_response (> 1 tháng)"""
        self._cleanup_simple_model("telegraf.port_response", batch_size)

    def _cleanup_simple_model(self, model_name, batch_size):
        """Hàm hỗ trợ: xóa batch_size bản ghi cũ nhất trong model bất kỳ"""
        limit_date = datetime.today() - timedelta(days=30)
        try:
            records = self.env[model_name].search(
                [("create_date", "<", limit_date)],
                order="create_date asc",
                limit=batch_size
            )
            count = len(records)
            if count:
                records.unlink()
                _logger.info("Đã xóa %s bản ghi trong %s", count, model_name)
            else:
                _logger.info("Không còn dữ liệu cũ trong %s", model_name)
        except Exception as e:
            _logger.error("Lỗi khi xóa %s: %s", model_name, str(e))