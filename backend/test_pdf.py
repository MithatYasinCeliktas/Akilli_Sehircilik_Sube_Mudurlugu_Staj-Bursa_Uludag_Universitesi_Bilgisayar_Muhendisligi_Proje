import pytest
from app.core.database import async_session
from app.services.report_service import ReportService
from app.services.export_service import ExportService

@pytest.mark.asyncio

async def test_export():
    async with async_session() as db:
        service = ReportService(db)
        try:
            # Rapor 1'i çek
            report = await service.get_report_by_id(1)
            pdf = await ExportService.export_report_to_pdf(report, db)
            print("PDF OK, size:", len(pdf.getvalue()))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("ERROR", e)

        try:
            reports, total = await service.report_repo.get_filtered_reports(filters=type("Filter", (), {"year": None, "month": None, "status": None, "user_ids": None, "unit_id": None, "category": None, "search_text": None, "start_date": None, "end_date": None, "report_ids": None})())
            from app.schemas.report import ActivityReportResponse
            items = [ActivityReportResponse.model_validate(r) for r in reports]
            excel = await ExportService.export_reports_to_excel(items, db)
            print("EXCEL OK, size:", len(excel.getvalue()))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("EXCEL ERROR", e)


