# schemas.py 상세 설명

## 이 파일은 뭔가?
API 요청/응답 데이터의 형식을 정의하는 파일임. Pydantic 스키마라고 부름.

---

## 전체 코드

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TodoCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    
class TodoOut(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

## 스키마 vs 모델

### 모델 (models.py)
```python
class Todo(Base):  # SQLAlchemy
    __tablename__ = "todo"
    id: Mapped[int] = mapped_column(...)
```
- 데이터베이스 테이블 구조
- SQLAlchemy ORM
- DB와 직접 연결

### 스키마 (schemas.py)
```python
class TodoOut(BaseModel):  # Pydantic
    id: int
    text: str
```
- API 입출력 데이터 구조
- Pydantic
- 유효성 검증, JSON 변환

**역할이 다름.** 둘 다 필요함.

---

## Import 설명

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
```

- `datetime`: 날짜/시간 타입
- `BaseModel`: Pydantic 스키마의 기본 클래스
- `Field`: 필드에 제약사항 추가
- `ConfigDict`: 스키마 설정

---

## TodoCreate 스키마

```python
class TodoCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
```

### 용도
- Todo 생성 시 클라이언트가 보내는 데이터
- POST `/api/todo` 요청의 body

### 필드 분석
```python
text: str = Field(min_length=1, max_length=255)
```
- `text: str`: 문자열 타입
- `Field(...)`: 추가 제약사항
  - `min_length=1`: 최소 1글자 (빈 문자열 불가)
  - `max_length=255`: 최대 255자

### 실제 요청 예시
```json
{
  "text": "장보기"
}
```

### 검증 예시
```python
# ✅ 유효한 데이터
TodoCreate(text="운동하기")

# ❌ 빈 문자열 - 에러
TodoCreate(text="")  # min_length 위반

# ❌ 너무 긴 문자열 - 에러
TodoCreate(text="a" * 256)  # max_length 위반
```

### 왜 id, done, createdAt은 없나?
- `id`: DB가 자동 생성
- `done`: 기본값 False로 서버에서 처리
- `createdAt`: DB가 자동 생성

**클라이언트는 text만 보내면 됨.** 이게 핵심임.

---

## TodoOut 스키마

```python
class TodoOut(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)
```

### 용도
- Todo 조회 시 서버가 반환하는 데이터
- API 응답 body

### 필드 분석
```python
id: int
text: str
done: bool
createdAt: datetime
```
- 모든 필드 포함 (전체 정보 반환)
- 타입만 지정, 제약사항 없음
- 출력용이라 검증 필요 없음

### model_config 설명
```python
model_config = ConfigDict(from_attributes=True)
```

**from_attributes=True의 의미:**
- SQLAlchemy 모델 객체를 Pydantic 스키마로 자동 변환
- 속성(attribute)에서 값을 읽어옴

**예시:**
```python
# DB에서 조회한 Todo 모델
todo = await session.get(Todo, 1)
# todo.id = 1
# todo.text = "장보기"
# todo.done = False
# todo.createdAt = 2024-01-01 12:00:00

# TodoOut으로 자동 변환
todo_out = TodoOut.model_validate(todo)
# 또는 FastAPI가 자동으로 변환
```

**from_attributes=False면?**
```python
# ❌ 에러 발생
TodoOut.model_validate(todo)  # dict가 아니라서 에러

# dict로 변환해야 함
TodoOut.model_validate({
    "id": todo.id,
    "text": todo.text,
    "done": todo.done,
    "createdAt": todo.createdAt
})
```

**귀찮음.** `from_attributes=True`가 편함.

### 실제 응답 예시
```json
{
  "id": 1,
  "text": "장보기",
  "done": false,
  "createdAt": "2024-01-01T12:00:00"
}
```

---

## FastAPI에서 사용

### 라우터에서 사용
```python
from fastapi import APIRouter
from .schemas import TodoCreate, TodoOut

router = APIRouter()

@router.post("/todo", response_model=TodoOut)
async def create_todo(body: TodoCreate):
    # body.text 자동 검증됨
    # 반환값 자동으로 TodoOut 형식으로 변환
    pass
```

### 동작 과정

#### 1. 요청 수신
```json
POST /api/todo
{
  "text": "운동하기"
}
```

#### 2. Pydantic 검증
```python
body: TodoCreate
# - text가 문자열인지 체크
# - 1~255자인지 체크
# - 실패 시 422 에러 자동 반환
```

#### 3. 비즈니스 로직
```python
todo = await service.create(text=body.text)
# todo는 SQLAlchemy Todo 모델 객체
```

#### 4. 응답 변환
```python
response_model=TodoOut
# - Todo 모델을 TodoOut 스키마로 자동 변환
# - JSON으로 직렬화
```

#### 5. 응답 반환
```json
{
  "id": 1,
  "text": "운동하기",
  "done": false,
  "createdAt": "2024-01-01T12:00:00"
}
```

---

## 실전 패턴

### 1. 입력/출력 스키마 분리
```python
# 입력: 최소한의 정보
class TodoCreate(BaseModel):
    text: str

# 출력: 전체 정보
class TodoOut(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
```

**왜 분리?**
- 입력: 사용자가 제공
- 출력: 서버가 생성
- 역할이 다름

### 2. 수정용 스키마 (추가 예시)
```python
class TodoUpdate(BaseModel):
    text: str | None = None
    done: bool | None = None
```
- 모든 필드 선택적 (Optional)
- 원하는 필드만 수정 가능

### 3. 상세/간략 스키마
```python
# 간략 정보
class TodoSimple(BaseModel):
    id: int
    text: str

# 상세 정보
class TodoDetail(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
    updatedAt: datetime
```

---

## Field 추가 옵션

```python
from pydantic import Field

class TodoCreate(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=255,
        description="할 일 내용",
        examples=["장보기", "운동하기"]
    )
```

**옵션들:**
- `min_length`, `max_length`: 문자열 길이 제한
- `gt`, `lt`, `ge`, `le`: 숫자 범위 제한
- `description`: API 문서에 표시될 설명
- `examples`: API 문서에 표시될 예시
- `default`: 기본값

---

## 검증 예시

### 자동 검증 성공
```python
# ✅ 정상 데이터
data = {"text": "운동하기"}
todo = TodoCreate(**data)
print(todo.text)  # "운동하기"
```

### 자동 검증 실패
```python
# ❌ text 없음
data = {}
TodoCreate(**data)  # ValidationError

# ❌ 빈 문자열
data = {"text": ""}
TodoCreate(**data)  # ValidationError (min_length)

# ❌ 너무 김
data = {"text": "a" * 256}
TodoCreate(**data)  # ValidationError (max_length)

# ❌ 잘못된 타입
data = {"text": 123}
TodoCreate(**data)  # ValidationError (타입 불일치)
```

**FastAPI가 자동으로 422 에러 반환함.**

---

## 주의사항

### 1. from_attributes 꼭 설정
```python
# ❌ 설정 안 하면 ORM 객체 변환 안 됨
class TodoOut(BaseModel):
    id: int
    text: str

# ✅ 설정하면 자동 변환
class TodoOut(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)
```

### 2. 필드명 일치
```python
# models.py
class Todo(Base):
    text: Mapped[str] = mapped_column("task", ...)  # DB: task

# schemas.py
class TodoOut(BaseModel):
    text: str  # Python 속성명: text
    model_config = ConfigDict(from_attributes=True)
```
- Python 속성명(`text`)으로 매핑됨
- DB 컬럼명(`task`)이 아님
- 모델과 스키마의 필드명 맞춰야 함

### 3. 타입 일치
```python
# models.py
createdAt: Mapped[datetime] = ...

# schemas.py
createdAt: datetime  # 타입 동일하게
```

---

## 핵심 정리

1. **스키마 = API 데이터 형식**
   - 요청 검증
   - 응답 변환
   - 자동 문서화

2. **입력/출력 분리**
   - Create: 클라이언트 입력
   - Out: 서버 응답
   - 역할에 맞게 설계

3. **Field로 제약 추가**
   - 길이, 범위, 패턴 등
   - 자동 검증

4. **from_attributes 필수**
   - ORM 모델 자동 변환
   - 수동 매핑 불필요

5. **FastAPI 완벽 통합**
   - 자동 검증
   - 자동 문서화
   - 자동 에러 처리

스키마는 API의 계약서임. 명확하게 정의하면 버그가 줄어듦.

