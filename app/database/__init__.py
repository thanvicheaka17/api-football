from app.database.repository import ApiResponseRepository
from app.database.utils import params_hash

Database = ApiResponseRepository


def get_database() -> ApiResponseRepository:
    return ApiResponseRepository()
