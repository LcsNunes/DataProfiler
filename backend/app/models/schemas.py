from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FilePathRequest(BaseModel):
    path: str = Field(..., min_length=1)
    business_objective: str | None = Field(default=None, max_length=500)


class FilePathsRequest(BaseModel):
    paths: list[str] = Field(..., min_length=2)
    business_objective: str | None = Field(default=None, max_length=500)

    @field_validator("paths")
    @classmethod
    def validate_paths(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("Paths cannot be empty.")
        return cleaned


class ApiAuthConfig(BaseModel):
    type: Literal["none", "api_key", "bearer", "basic"] = "none"
    api_key_name: str | None = None
    api_key_value: str | None = None
    api_key_location: Literal["header", "query"] = "header"
    bearer_token: str | None = None
    basic_username: str | None = None
    basic_password: str | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "ApiAuthConfig":
        if self.type == "api_key" and (not self.api_key_name or not self.api_key_value):
            raise ValueError("API key auth requires api_key_name and api_key_value.")
        if self.type == "bearer" and not self.bearer_token:
            raise ValueError("Bearer auth requires bearer_token.")
        if self.type == "basic" and (not self.basic_username or not self.basic_password):
            raise ValueError("Basic auth requires username and password.")
        return self


class ApiPaginationConfig(BaseModel):
    type: Literal["none", "page_limit", "offset_limit", "next_url", "next_token"] = "none"
    page_param: str = "page"
    offset_param: str = "offset"
    limit_param: str = "limit"
    start_page: int = 1
    start_offset: int = 0
    limit: int = Field(default=100, ge=1, le=10000)
    max_pages: int = Field(default=3, ge=1, le=50)
    next_url_path: str | None = None
    next_token_path: str | None = None
    next_token_param: str = "next_token"


class ApiSourceRequest(BaseModel):
    url: str = Field(..., min_length=1)
    method: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    body: dict[str, Any] | list[Any] | None = None
    auth: ApiAuthConfig = Field(default_factory=ApiAuthConfig)
    timeout: float = Field(default=20.0, gt=0, le=180)
    retries: int = Field(default=1, ge=0, le=5)
    data_path: str | None = None
    pagination: ApiPaginationConfig = Field(default_factory=ApiPaginationConfig)
    business_objective: str | None = Field(default=None, max_length=500)

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.upper()

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://.")
        return value


class SqlSourceRequest(BaseModel):
    connection_string: str = Field(..., min_length=1)
    table: str | None = None
    query: str | None = None
    limit: int | None = Field(default=5000, ge=1, le=1_000_000)
    business_objective: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_table_or_query(self) -> "SqlSourceRequest":
        if not self.table and not self.query:
            raise ValueError("Provide either table or query.")
        if self.table and self.query:
            raise ValueError("Provide table or query, not both.")
        return self


class ReportSummary(BaseModel):
    id: str
    created_at: str
    source: dict[str, Any]
    summary: dict[str, Any]
    recommendation: dict[str, Any]
