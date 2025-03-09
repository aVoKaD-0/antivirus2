from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    id: str
    analysis_id: str
    token: str
    file: str

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    file_activity: list
    docker_output: str


