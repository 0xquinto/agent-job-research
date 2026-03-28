from pydantic import BaseModel


class JobPosting(BaseModel):
    title: str
    company: str
    source: str
    job_url: str
    location: str | None = None
    is_remote: bool = True
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "USD"
    salary_interval: str = "yearly"
    date_posted: str | None = None
    job_type: str | None = None
    description: str | None = None

    @property
    def dedup_key(self) -> tuple[str, str]:
        return (self.title.strip().lower(), self.company.strip().lower())
