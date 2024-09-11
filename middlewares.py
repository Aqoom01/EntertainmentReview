from fastapi.middleware.cors import CORSMiddleware
import logging

def add_middlewares(app):
    # CORS 설정
    origins = ["http://localhost", "http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 로그 설정
    logging.basicConfig(level=logging.INFO)

    @app.middleware("http")
    async def log_requests(request, call_next):
        logging.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response
