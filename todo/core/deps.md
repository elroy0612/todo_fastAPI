# deps.py 상세 설명

## 이 파일은 뭔가?
의존성 주입을 더 간편하게 만들어주는 헬퍼 파일임. 코드를 짧고 깔끔하게 만드는 게 목적임.

---

## 전체 코드

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from .database import get_session

def db_dep(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session
```

단 5줄짜리 파일이지만 역할은 명확함.

---

## 코드 분석

### Import 부분
```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from .database import get_session
```

**각 Import 설명:**
- `AsyncSession`: 비동기 데이터베이스 세션 타입
- `Depends`: FastAPI의 의존성 주입 함수
- `get_session`: database.py에서 만든 세션 제너레이터

### 함수 정의
```python
def db_dep(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session
```

**매개변수:**
- `session: AsyncSession`: 세션 객체의 타입 힌트
- `= Depends(get_session)`: FastAPI가 자동으로 get_session() 호출하여 세션 주입
- `-> AsyncSession`: 반환 타입

**동작:**
- 받은 세션을 그대로 반환함
- 별거 없어 보이지만 실용적임

---

## 왜 이렇게 만들었나?

### 1. 코드 길이 단축

#### Before - deps.py 없이
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.database import get_session

router = APIRouter()

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_session)):
    return await db.execute(select(User))

@router.post("/users")
async def create_user(db: AsyncSession = Depends(get_session)):
    return await db.execute(insert(User))

@router.delete("/users/{id}")
async def delete_user(id: int, db: AsyncSession = Depends(get_session)):
    return await db.execute(delete(User).where(User.id == id))
```

매번 `db: AsyncSession = Depends(get_session)` 타이핑하는 게 귀찮음.

#### After - deps.py 사용
```python
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep

router = APIRouter()

@router.get("/users")
async def get_users(db: AsyncSession = db_dep):
    return await db.execute(select(User))

@router.post("/users")
async def create_user(db: AsyncSession = db_dep):
    return await db.execute(insert(User))

@router.delete("/users/{id}")
async def delete_user(id: int, db: AsyncSession = db_dep):
    return await db.execute(delete(User).where(User.id == id))
```

`= db_dep`만 쓰면 됨. 훨씬 짧음.

### 2. 일관성 유지

모든 라우터에서 동일한 패턴 사용:
```python
db: AsyncSession = db_dep
```

누가 봐도 "아, 데이터베이스 의존성이구나" 바로 알 수 있음.

### 3. 변경 용이성

나중에 세션 로직 변경할 때 deps.py만 수정하면 됨:
```python
# 예: 트랜잭션 자동 시작하도록 변경
def db_dep(session: AsyncSession = Depends(get_transaction)) -> AsyncSession:
    return session
```

모든 라우터 코드는 수정 안 해도 됨.

---

## 사용 예시

### 기본 사용
```python
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep
from todo.user.models import User

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = db_dep):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 여러 의존성과 함께 사용
```python
from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep

router = APIRouter()

@router.get("/users")
async def get_users(
    db: AsyncSession = db_dep,
    skip: int = Query(0),
    limit: int = Query(10)
):
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

---

## 대안과 비교

### 방법 1: deps.py 없이 매번 작성
```python
db: AsyncSession = Depends(get_session)
```
- 장점: 직관적, 추가 파일 불필요
- 단점: 타이핑 많음, 오타 가능성

### 방법 2: deps.py 사용 (현재 방식)
```python
db: AsyncSession = db_dep
```
- 장점: 짧고 간결, 일관성
- 단점: 한 단계 추상화 추가

### 방법 3: 타입 어노테이션만 사용 (Python 3.9+)
```python
from typing import Annotated

DbDep = Annotated[AsyncSession, Depends(get_session)]

@router.get("/users")
async def get_users(db: DbDep):
    ...
```
- 장점: 가장 깔끔, 타입 힌트 레벨에서 해결
- 단점: Python 버전 제약

---

## 실전 팁

### 1. 다른 의존성도 추가 가능
```python
# deps.py
from fastapi import Depends, Header, HTTPException

def auth_dep(token: str = Header(...)) -> str:
    if not verify_token(token):
        raise HTTPException(status_code=401)
    return token

def admin_dep(token: str = auth_dep) -> str:
    if not is_admin(token):
        raise HTTPException(status_code=403)
    return token
```

### 2. 여러 버전의 db_dep 만들기
```python
# deps.py
def db_dep(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session

def db_transaction_dep(session: AsyncSession = Depends(get_transaction)) -> AsyncSession:
    return session

def db_readonly_dep(session: AsyncSession = Depends(get_readonly_session)) -> AsyncSession:
    return session
```

### 3. 네이밍 컨벤션
- `_dep` 접미사: 의존성임을 명확히 표시
- 짧고 기억하기 쉬운 이름 사용
- 일관된 패턴 유지

---

## 주의사항

### 1. 타입 힌트는 필수
```python
# ❌ 타입 없으면 IDE 자동완성 안 됨
async def get_users(db = db_dep):
    ...

# ✅ 타입 힌트로 IDE 지원 받기
async def get_users(db: AsyncSession = db_dep):
    ...
```

### 2. db_dep는 함수가 아닌 "이미 주입된" 형태
```python
# ❌ 틀림
async def get_users(db: AsyncSession = db_dep()):
    ...

# ✅ 맞음
async def get_users(db: AsyncSession = db_dep):
    ...
```

`db_dep` 자체가 이미 `Depends(get_session)`을 기본값으로 가진 매개변수임.

### 3. 순환 import 주의
```python
# ❌ 순환 참조 발생 가능
# deps.py에서 router import
# router.py에서 deps import

# ✅ deps는 최소한의 import만
# core 레벨에서만 import
```

---

## 핵심 정리

1. **deps.py = 의존성 주입 단축키**
   - `Depends(get_session)` → `db_dep`로 단축
   - 코드가 짧고 읽기 편함

2. **일관성과 유지보수성**
   - 모든 곳에서 동일한 패턴
   - 한 곳만 수정하면 전체 적용

3. **선택사항임**
   - 없어도 작동함
   - 편의를 위한 헬퍼 함수
   - 프로젝트 크기에 따라 선택

4. **확장 가능**
   - 인증, 권한 등 다른 의존성도 추가 가능
   - 프로젝트 전체 의존성 관리 포인트

작은 파일이지만 반복 작업을 줄여주는 실용적인 친구임.

