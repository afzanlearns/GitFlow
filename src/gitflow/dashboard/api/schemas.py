from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FilterParams(BaseModel):
    author: Optional[str] = Field(None, max_length=100)
    repo: Optional[str] = Field(None, max_length=100)
    days: int = Field(30, ge=1, le=365)  # Between 1-365
    language: Optional[str] = Field(None, max_length=20)
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=500)  # Max 500 per page
    
    @field_validator('days', mode='before')
    @classmethod
    def days_valid(cls, v):
        if v is not None:
            try:
                val = int(v)
                if not 1 <= val <= 365:
                    raise ValueError('days must be between 1 and 365')
                return val
            except ValueError:
                raise ValueError('days must be an integer between 1 and 365')
        return 30
    
    @field_validator('author', 'repo', 'language', mode='before')
    @classmethod
    def sanitize_strings(cls, v):
        if v is None:
            return v
        return str(v).strip()[:100]

class SearchParams(BaseModel):
    q: str = Field(..., min_length=1, max_length=200)
    category: str = Field('commits', pattern='^(commits|files|authors)$')
    limit: int = Field(20, ge=1, le=100)

class ExportParams(BaseModel):
    format: str = Field('csv', pattern='^(csv|json|markdown)$')
    days: int = Field(30, ge=1, le=365)
    output: Optional[str] = Field(None, max_length=255)

class ReportParams(BaseModel):
    days: int = Field(30, ge=1, le=365)
    include_authors: bool = Field(True)
    include_files: bool = Field(True)
