from pydantic import BaseModel

class AnalysisResult(BaseModel):
    analysis_id: str
    result_data: dict

class AnalysisRequest(BaseModel):
    file: str

class AnalysisResponse(BaseModel):
    analysis_id: str

class AnalysisStatus(BaseModel):
    analysis_id: str
    status: str

class AnalysisStatusResponse(BaseModel):
    status: str

class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str
