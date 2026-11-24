import uvicorn

from infrastructure.config import settings


if __name__ == "__main__":
    uvicorn.run("api:app", host=settings.api_host, port=settings.api_port)
