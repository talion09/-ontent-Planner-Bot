from fastapi import APIRouter

from api_service.admin_statistics.dao import AdminStatisticsDao
from api_service.admin_statistics.schemas import StatiscticSchema
from api_service.utils.schemas import Response

router_admin_statistics = APIRouter(
    prefix="/admin_statistics",
    tags=["AdminStatistics"],
)


@router_admin_statistics.get("/",response_model=Response[StatiscticSchema])
async def get_statistics():
    try:
        result = await AdminStatisticsDao.statistics()
        data = StatiscticSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response