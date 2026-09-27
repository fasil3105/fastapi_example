from sqlmodel import SQLModel


class DownloadResponse(SQLModel):

    download_url : str
    expires_in : int

