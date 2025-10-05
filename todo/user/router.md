# router.py 상세 설명

## 이 파일은 뭔가?
HTTP 요청을 받아서 응답을 반환하는 API 엔드포인트 정의 파일임. FastAPI 라우터라고 부름.

---

## 전체 코드

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep
from .service import TodoService
from .schemas import TodoCreate, TodoOut

router = APIRouter(prefix="/api", tags=["todo"])

def get_service(session: AsyncSession = Depends(db_dep)) -> TodoService:
    return TodoService(session)

@router.post("/todo", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
    item = await service.create(text=body.text)
    return item
```

---

## Router의 역할

### 계층 구조 복습
```
Router ← 여기 (HTTP 계층)
   ↓
Service (비즈니스 로직)
   ↓
Repository (데이터 접근)
   ↓
Database
```

### Router가 하는 일
1. **HTTP 요청 수신**: URL, Method, Body 받기
2. **데이터 검증**: Pydantic으로 자동 검증
3. **Service 호출**: 비즈니스 로직 실행
4. **HTTP 응답 반환**: JSON 변환 및 상태 코드

**Router는 HTTP와 비즈니스 로직 사이의 다리임.**

---

## Import 설명

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep
from .service import TodoService
from .schemas import TodoCreate, TodoOut
```

- `APIRouter`: 라우터 생성
- `Depends`: 의존성 주입
- `status`: HTTP 상태 코드 상수
- `AsyncSession`: 세션 타입 힌트
- `db_dep`: 데이터베이스 의존성 (deps.py에서)
- `TodoService`: 서비스 계층
- `TodoCreate, TodoOut`: 요청/응답 스키마

---

## Router 생성

```python
router = APIRouter(prefix="/api", tags=["todo"])
```

### 매개변수 설명

**prefix="/api":**
- 모든 엔드포인트에 `/api` 접두사 추가
- 예: `@router.post("/todo")` → 실제 URL은 `/api/todo`

**tags=["todo"]:**
- API 문서에서 그룹핑
- Swagger UI에서 "todo" 섹션으로 표시

### 사용 효과

```python
# router.py
@router.post("/todo")  # /api/todo
@router.get("/todo")   # /api/todo
@router.get("/todo/{id}")  # /api/todo/{id}
```

모두 `/api` 아래에 생김.

---

## get_service 함수

```python
def get_service(session: AsyncSession = Depends(db_dep)) -> TodoService:
    return TodoService(session)
```

### 역할
의존성 주입 헬퍼 함수. Service 객체를 생성해서 반환함.

### 동작 과정

#### 1단계: 세션 주입
```python
session: AsyncSession = Depends(db_dep)
```
- FastAPI가 `db_dep`를 호출
- `db_dep`는 `Depends(get_session)`
- 결국 `get_session()`이 실행되어 세션 생성

#### 2단계: Service 생성
```python
return TodoService(session)
```
- 받은 세션으로 TodoService 생성
- 반환된 Service는 엔드포인트에 주입됨

### 왜 이렇게?

#### 방법 1: get_service 없이 (번거로움)
```python
@router.post("/todo")
async def create_todo(
    body: TodoCreate, 
    session: AsyncSession = Depends(db_dep)
):
    service = TodoService(session)
    item = await service.create(text=body.text)
    return item
```

매번 `TodoService(session)` 작성해야 함.

#### 방법 2: get_service 사용 (현재 방식)
```python
@router.post("/todo")
async def create_todo(
    body: TodoCreate, 
    service: TodoService = Depends(get_service)
):
    item = await service.create(text=body.text)
    return item
```

`service`를 바로 받음. 깔끔함.

**이게 더 나음.**

---

## create_todo 엔드포인트

```python
@router.post("/todo", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
    item = await service.create(text=body.text)
    return item
```

### 데코레이터 분석

```python
@router.post("/todo", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
```

**@router.post:**
- HTTP POST 메서드
- 리소스 생성에 사용

**"/todo":**
- 경로 (prefix와 합쳐져 `/api/todo`)

**response_model=TodoOut:**
- 응답 데이터를 TodoOut 스키마로 변환
- 자동 검증 및 JSON 직렬화
- API 문서 자동 생성

**status_code=status.HTTP_201_CREATED:**
- 성공 시 201 상태 코드 반환
- 201 = Created (리소스 생성 성공)
- `status.HTTP_201_CREATED` = 201 (상수)

---

## 함수 시그니처

```python
async def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
```

### 매개변수

**body: TodoCreate:**
- 요청 body를 TodoCreate 스키마로 검증
- 자동으로 JSON → Python 객체 변환
- 검증 실패 시 422 에러 자동 반환

**service: TodoService = Depends(get_service):**
- `get_service()` 호출하여 Service 주입
- FastAPI가 자동으로 의존성 해결

---

## 함수 본문

```python
item = await service.create(text=body.text)
return item
```

### 단순함이 핵심
- Service 메서드 호출
- 결과 반환
- **다른 로직 없음**

**왜 단순한가?**
- 비즈니스 로직은 Service에
- 데이터 접근은 Repository에
- Router는 HTTP만 담당

**분리가 잘 되어있음.**

---

## 전체 요청/응답 흐름

### 1. 클라이언트 요청
```http
POST /api/todo HTTP/1.1
Content-Type: application/json

{
  "text": "장보기"
}
```

### 2. FastAPI 처리

#### 2-1. 라우터 찾기
- POST `/api/todo` → `create_todo` 함수

#### 2-2. 의존성 주입
```python
# db_dep 실행
session = await get_session()  # 세션 생성

# get_service 실행
service = TodoService(session)  # 서비스 생성
```

#### 2-3. Body 검증
```python
body = TodoCreate(text="장보기")
# - text가 문자열인지 체크
# - 1~255자인지 체크
# - 실패 시 422 에러 반환
```

#### 2-4. 함수 실행
```python
async def create_todo(body, service):
    item = await service.create(text=body.text)
    # service.create() 내부:
    #   - repo.add() → 객체 생성
    #   - commit() → DB 저장
    #   - refresh() → 최신 값
    return item
```

#### 2-5. 응답 변환
```python
response_model=TodoOut
# item (SQLAlchemy Todo) → TodoOut 스키마
# TodoOut → JSON
```

### 3. 서버 응답
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 1,
  "text": "장보기",
  "done": false,
  "createdAt": "2024-01-01T12:00:00"
}
```

---

## 추가 엔드포인트 예시

```python
from fastapi import HTTPException

router = APIRouter(prefix="/api", tags=["todo"])

def get_service(session: AsyncSession = Depends(db_dep)) -> TodoService:
    return TodoService(session)

# 생성 (기존)
@router.post("/todo", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
    item = await service.create(text=body.text)
    return item

# 전체 조회
@router.get("/todo", response_model=list[TodoOut])
async def get_todos(service: TodoService = Depends(get_service)):
    items = await service.get_all()
    return items

# 단건 조회
@router.get("/todo/{todo_id}", response_model=TodoOut)
async def get_todo(todo_id: int, service: TodoService = Depends(get_service)):
    item = await service.get_by_id(todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Todo not found")
    return item

# 상태 변경
@router.patch("/todo/{todo_id}", response_model=TodoOut)
async def update_todo_status(
    todo_id: int, 
    done: bool, 
    service: TodoService = Depends(get_service)
):
    item = await service.update_status(todo_id, done)
    if not item:
        raise HTTPException(status_code=404, detail="Todo not found")
    return item

# 삭제
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, service: TodoService = Depends(get_service)):
    success = await service.delete(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None  # 204는 body 없음
```

---

## response_model의 역할

### 1. 자동 변환
```python
@router.post("/todo", response_model=TodoOut)
async def create_todo(...):
    item = await service.create(...)  # Todo 모델
    return item  # TodoOut으로 자동 변환
```

### 2. 필드 필터링
```python
# Todo 모델에 password 필드가 있다면
class Todo(Base):
    id: Mapped[int]
    text: Mapped[str]
    password: Mapped[str]  # 민감 정보

# TodoOut에는 제외
class TodoOut(BaseModel):
    id: int
    text: str
    # password 없음

# 응답에 password 자동으로 제외됨
```

### 3. API 문서 생성
```python
response_model=TodoOut
# Swagger UI에 응답 예시 자동 생성
```

---

## status_code 설명

```python
from fastapi import status

# 성공
status.HTTP_200_OK  # 200 - 일반 성공
status.HTTP_201_CREATED  # 201 - 생성 성공
status.HTTP_204_NO_CONTENT  # 204 - 성공 (body 없음)

# 클라이언트 에러
status.HTTP_400_BAD_REQUEST  # 400 - 잘못된 요청
status.HTTP_404_NOT_FOUND  # 404 - 없음
status.HTTP_422_UNPROCESSABLE_ENTITY  # 422 - 검증 실패

# 서버 에러
status.HTTP_500_INTERNAL_SERVER_ERROR  # 500 - 서버 에러
```

**상수 사용 추천.** 숫자보다 의미가 명확함.

---

## 주의사항

### 1. Router는 단순하게
```python
# ❌ Router에 비즈니스 로직 (안 좋음)
@router.post("/todo")
async def create_todo(body: TodoCreate, db: AsyncSession):
    if len(body.text) < 3:
        raise HTTPException(400, "3글자 이상")
    
    item = Todo(text=body.text, done=False)
    db.add(item)
    await db.commit()
    # ...

# ✅ Router는 단순하게 (좋음)
@router.post("/todo")
async def create_todo(body: TodoCreate, service: TodoService):
    return await service.create(text=body.text)
```

### 2. response_model 필수
```python
# ❌ response_model 없으면 API 문서 불완전
@router.get("/todo")
async def get_todos(service: TodoService):
    return await service.get_all()

# ✅ response_model로 명시
@router.get("/todo", response_model=list[TodoOut])
async def get_todos(service: TodoService):
    return await service.get_all()
```

### 3. 예외 처리
```python
# ✅ 404 명시적 처리
@router.get("/todo/{todo_id}")
async def get_todo(todo_id: int, service: TodoService):
    item = await service.get_by_id(todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```

---

## main.py와 연결

```python
# main.py
from fastapi import FastAPI
from todo.user.router import router as todo_router

app = FastAPI()
app.include_router(todo_router)  # 라우터 등록
```

이렇게 하면 `/api/todo` 엔드포인트가 활성화됨.

---

## 핵심 정리

1. **Router = HTTP 계층**
   - 요청 받기
   - 응답 반환
   - 비즈니스 로직 없음

2. **의존성 주입 활용**
   - `Depends(db_dep)`: 세션
   - `Depends(get_service)`: 서비스
   - 자동으로 생성 및 정리

3. **response_model 필수**
   - 자동 변환
   - 필드 필터링
   - API 문서 생성

4. **상태 코드 명시**
   - 201: 생성
   - 200: 조회/수정
   - 204: 삭제
   - 404: 없음

5. **단순함이 핵심**
   - Service 호출만
   - 에러 처리 최소화
   - 가독성 최우선

Router는 프론트엔드와 백엔드의 접점임. 명확하고 단순하게 유지해야 함.

