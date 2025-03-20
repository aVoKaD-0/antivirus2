import asyncio
from app.services.analysis_service import AnalysisService
from app.utils.file_operations import FileOperations
# import asyncio

async def test_analysis_service():
    analysis_service = AnalysisService()
    await analysis_service.get_db()
    await analysis_service.analyze("61454e7c-b20b-4b8d-9f56-cd48a7e4ca06", "4ukey_11739454314679240201.exe", "61454e7c-b20b-4b8d-9f56-cd48a7e4ca06")

if __name__ == "__main__":
    asyncio.run(test_analysis_service())