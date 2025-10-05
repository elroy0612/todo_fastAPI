# main.py 상세 설명

## 이 파일은 뭔가?
FastAPI 애플리케이션의 진입점임. 앱을 생성하고 설정하는 파일임.

---

## 전체 코드

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from todo.user.router import router as todo_router 

app = FastAPI(title="Todo API", version="0.1.0")
app.include_router(todo_router) 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def test():
    return {"ok":True}
```

---

## Import 설명

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from todo.user.router import router as todo_router
```

- `FastAPI`: 앱 생성 클래스
- `CORSMiddleware`: CORS 설정 미들웨어
- `todo_router`: user 폴더의 라우터

---

## FastAPI 앱 생성

```python
app = FastAPI(title="Todo API", version="0.1.0")
```

### 매개변수

**title="Todo API":**
- API 문서(Swagger UI)에 표시될 제목
- `http://localhost:8000/docs` 상단에 표시됨

**version="0.1.0":**
- API 버전
- 문서에 표시됨
- 버전 관리에 사용

### 다른 옵션들 (사용 안 했지만 가능)
```python
app = FastAPI(
    title="Todo API",
    version="0.1.0",
    description="할 일 관리 API",
    docs_url="/docs",  # Swagger UI 경로 (기본값)
    redoc_url="/redoc",  # ReDoc 경로
    openapi_url="/openapi.json",  # OpenAPI 스키마
)
```

---

## 라우터 등록

```python
app.include_router(todo_router)
```

### 역할
- `todo_router`의 모든 엔드포인트를 앱에 등록
- `router.py`의 `@router.post`, `@router.get` 등이 활성화됨

### 동작 원리
```python
# router.py
router = APIRouter(prefix="/api", tags=["todo"])

@router.post("/todo")  # 실제 경로: /api/todo
async def create_todo(...):
    pass

# main.py
app.include_router(todo_router)
# 이제 POST /api/todo가 앱에 등록됨
```

### 여러 라우터 등록 가능
```python
from todo.user.router import router as user_router
from todo.admin.router import router as admin_router

app.include_router(user_router)
app.include_router(admin_router)
```

---

## CORS 미들웨어

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CORS란?
**Cross-Origin Resource Sharing** (교차 출처 리소스 공유)

- 브라우저 보안 정책
- 다른 도메인에서 API 호출 시 필요
- CORS 설정 없으면 브라우저가 요청 차단

**예시:**
```
프론트엔드: http://localhost:5173 (Vite)
백엔드: http://localhost:8000 (FastAPI)
→ 출처가 다름 → CORS 필요
```

---

## CORS 옵션 상세

### allow_origins
```python
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

**역할:** 허용할 출처(도메인) 목록

**설명:**
- 이 도메인들에서 오는 요청만 허용
- `http://localhost:5173`: Vite 개발 서버 (React, Vue 등)
- `http://localhost:3000`: CRA, Next.js 개발 서버

**주의:**
```python
# ❌ 프로덕션에서 절대 사용 금지
allow_origins=["*"]  # 모든 도메인 허용 (보안 위험)

# ✅ 명시적으로 지정
allow_origins=["https://yourdomain.com"]
```

---

### allow_credentials
```python
allow_credentials=True
```

**역할:** 쿠키, 인증 헤더 허용 여부

**True일 때:**
- 브라우저가 쿠키를 요청에 포함시킴
- Authorization 헤더 사용 가능

**사용 예시:**
```javascript
// 프론트엔드
fetch('http://localhost:8000/api/todo', {
  credentials: 'include',  // 쿠키 포함
  headers: {
    'Authorization': 'Bearer token123'  // 인증 헤더
  }
})
```

**주의:**
- `allow_credentials=True` + `allow_origins=["*"]` 조합 불가
- 보안상 명시적 출처 지정 필요

---

### allow_methods
```python
allow_methods=["*"]
```

**역할:** 허용할 HTTP 메서드

**"*"의 의미:**
- 모든 메서드 허용
- GET, POST, PUT, DELETE, PATCH, OPTIONS 등

**명시적 지정도 가능:**
```python
allow_methods=["GET", "POST", "PUT", "DELETE"]
```

---

### allow_headers
```python
allow_headers=["*"]
```

**역할:** 허용할 HTTP 헤더

**"*"의 의미:**
- 모든 헤더 허용
- Content-Type, Authorization, X-Custom-Header 등

**명시적 지정도 가능:**
```python
allow_headers=["Content-Type", "Authorization"]
```

---

## CORS 동작 원리

### 1. Preflight 요청 (OPTIONS)
```http
OPTIONS /api/todo HTTP/1.1
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type
```

브라우저가 실제 요청 전에 확인 요청 보냄.

### 2. 서버 응답
```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Credentials: true
```

CORS 미들웨어가 자동으로 응답함.

### 3. 실제 요청
```http
POST /api/todo HTTP/1.1
Origin: http://localhost:5173
Content-Type: application/json

{"text": "장보기"}
```

Preflight 통과하면 실제 요청 진행됨.

---

## 테스트 엔드포인트

```python
@app.get("/test")
async def test():
    return {"ok":True}
```

### 용도
- API 서버 동작 확인용
- 헬스 체크
- 개발/디버깅

### 사용법
```bash
curl http://localhost:8000/test
# {"ok": true}
```

### 프로덕션에서는?
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }
```

이런 식으로 더 자세한 정보 제공함.

---

## 앱 실행

### 개발 서버
```bash
uvicorn todo.main:app --reload
```

**옵션 설명:**
- `todo.main:app`: `todo/main.py`의 `app` 객체
- `--reload`: 코드 변경 시 자동 재시작
- 기본 포트: 8000

### 포트 변경
```bash
uvicorn todo.main:app --reload --port 5000
```

### 외부 접속 허용
```bash
uvicorn todo.main:app --reload --host 0.0.0.0
```

---

## 실전 확장

### 환경별 설정
```python
from fastapi import FastAPI
from todo.core.database import get_settings

settings = get_settings()

app = FastAPI(
    title="Todo API",
    version="0.1.0",
    debug=settings.DEBUG  # 환경 변수로 관리
)

# 프로덕션에서 CORS 제한
if settings.ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
else:
    # 개발 환경은 느슨하게
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### 여러 라우터 등록
```python
from todo.user.router import router as user_router
from todo.admin.router import router as admin_router

app.include_router(user_router)
app.include_router(admin_router)

# prefix 추가도 가능
app.include_router(admin_router, prefix="/admin")
```

### 전역 예외 처리
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"}
    )
```

### 미들웨어 추가
```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## API 문서 접근

### Swagger UI
```
http://localhost:8000/docs
```
- 대화형 API 문서
- 직접 테스트 가능

### ReDoc
```
http://localhost:8000/redoc
```
- 읽기 전용 문서
- 더 깔끔한 디자인

### OpenAPI JSON
```
http://localhost:8000/openapi.json
```
- API 스펙 JSON 형식
- 클라이언트 코드 생성에 사용

---

## 주의사항

### 1. CORS 프로덕션 설정
```python
# ❌ 프로덕션에서 절대 금지
allow_origins=["*"]

# ✅ 명시적으로 지정
allow_origins=["https://yourdomain.com"]
```

### 2. 라우터 순서
```python
# ❌ 순서 중요 (좁은 것 먼저)
app.include_router(catch_all_router)  # /{path}
app.include_router(specific_router)  # /api/todo (안 잡힘!)

# ✅ 구체적인 것 먼저
app.include_router(specific_router)  # /api/todo
app.include_router(catch_all_router)  # /{path}
```

### 3. 환경 변수 활용
```python
# .env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# main.py
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins)
```

---

## 핵심 정리

1. **main.py = 앱 진입점**
   - 앱 생성
   - 라우터 등록
   - 미들웨어 설정

2. **CORS 필수**
   - 프론트엔드 연동 위해 필요
   - 개발/프로덕션 설정 다르게

3. **라우터 분리**
   - 기능별로 router.py 분리
   - main.py에서 통합

4. **자동 문서화**
   - /docs: Swagger UI
   - /redoc: ReDoc
   - FastAPI가 자동 생성

5. **확장 가능**
   - 미들웨어 추가
   - 예외 처리
   - 환경별 설정

main.py는 모든 것의 시작점임. 간단하고 명확하게 유지하는 게 좋음.

