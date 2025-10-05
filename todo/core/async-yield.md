# async-yield 패턴 상세 설명

## 이게 뭔가?
async-yield 패턴은 비동기 제너레이터를 만드는 방법임. FastAPI의 의존성 주입에서 자원을 자동으로 관리하는 핵심 패턴임.

---

## 기본 개념

### 1. 일반 함수 vs 제너레이터
```python
# 일반 함수 - return 사용
def normal_function():
    return "값"

# 제너레이터 - yield 사용
def generator_function():
    yield "값"
```

**차이점:**
- `return`: 값을 반환하고 함수 종료
- `yield`: 값을 반환하지만 함수는 일시 중지 상태로 유지됨

### 2. 동기 vs 비동기
```python
# 동기 제너레이터
def sync_gen():
    yield "값"

# 비동기 제너레이터
async def async_gen():
    yield "값"
```

**차이점:**
- 동기: 일반적인 함수처럼 순차적으로 실행
- 비동기: `async`/`await` 사용, I/O 작업 시 다른 작업도 처리 가능

---

## database.py의 async-yield 패턴

```python
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
```

### 동작 흐름 분석

#### 1단계: 세션 생성
```python
async with AsyncSessionLocal() as session:
```
- `AsyncSessionLocal()`로 새 데이터베이스 세션 생성
- `async with`는 비동기 컨텍스트 관리자
- 자동으로 세션 생명주기 관리

#### 2단계: 세션 제공
```python
    yield session
```
- 생성한 세션을 호출자에게 전달
- 여기서 함수는 일시 중지됨
- 호출자가 세션을 사용하는 동안 대기

#### 3단계: 세션 정리
```python
# yield 이후 (암묵적)
```
- 호출자가 세션 사용 완료하면 함수 재개
- `async with` 블록이 자동으로 세션 닫음
- 예외 발생해도 안전하게 정리됨

---

## 왜 이 패턴을 쓰는가?

### 1. 자동 리소스 관리
```python
# ❌ 수동 관리 - 실수하기 쉬움
async def bad_example():
    session = AsyncSessionLocal()
    try:
        # 작업 수행
        result = await session.execute(query)
        return result
    finally:
        await session.close()  # 깜빡하면 메모리 누수

# ✅ async-yield - 자동 관리
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session  # 자동으로 정리됨
```

### 2. 코드 재사용성
```python
# 모든 라우터에서 동일한 패턴 사용
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_session)):
    # 세션 생성/종료 신경 안 써도 됨
    return await db.execute(select(User))

@router.post("/users")
async def create_user(db: AsyncSession = Depends(get_session)):
    # 동일한 패턴
    return await db.execute(insert(User))
```

### 3. 예외 안전성
```python
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
        # 예외 발생해도 여기까지 도달
        # async with가 자동으로 정리
```

---

## FastAPI에서 사용하는 방법

### 기본 사용
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.database import get_session

router = APIRouter()

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_session)):
    # 1. FastAPI가 get_session() 호출
    # 2. yield까지 실행하여 session 받음
    # 3. 이 함수에 session 주입
    # 4. 이 함수 완료 후 get_session() 나머지 실행
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### 실행 순서
1. 요청 받음
2. FastAPI가 `get_session()` 호출
3. `async with AsyncSessionLocal() as session:` 실행
4. `yield session` 도달 → 세션 반환
5. `get_items()` 함수 실행 (세션 사용)
6. `get_items()` 완료
7. `get_session()`의 `async with` 블록 종료
8. 세션 자동 종료
9. 응답 반환

---

## 다른 용도 예시

### 1. 트랜잭션 관리
```python
async def get_transaction():
    async with AsyncSessionLocal() as session:
        async with session.begin():  # 트랜잭션 시작
            yield session
            # 자동 커밋 또는 롤백
```

### 2. 파일 관리
```python
async def get_file():
    file = await open_file("data.txt")
    try:
        yield file
    finally:
        await file.close()
```

### 3. 연결 풀 관리
```python
async def get_redis_connection():
    conn = await redis_pool.acquire()
    try:
        yield conn
    finally:
        await redis_pool.release(conn)
```

---

## 일반적인 실수

### 1. yield 없이 return 사용
```python
# ❌ 틀림
async def wrong_get_session():
    async with AsyncSessionLocal() as session:
        return session  # 여기서 종료되어 세션이 바로 닫힘

# ✅ 맞음
async def correct_get_session():
    async with AsyncSessionLocal() as session:
        yield session  # 일시 중지, 사용 후 자동 정리
```

### 2. async 없이 yield만 사용
```python
# ❌ 틀림 - 비동기 세션인데 동기 함수
def wrong_get_session():
    async with AsyncSessionLocal() as session:  # 에러!
        yield session

# ✅ 맞음
async def correct_get_session():
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. 수동으로 세션 닫기
```python
# ❌ 불필요함
async def unnecessary():
    async with AsyncSessionLocal() as session:
        yield session
        await session.close()  # async with가 이미 처리함

# ✅ 간결함
async def clean():
    async with AsyncSessionLocal() as session:
        yield session  # 이것만으로 충분
```

---

## 핵심 정리

1. **async-yield = 비동기 제너레이터**
   - 값을 반환하지만 함수는 계속 살아있음
   - 호출자가 끝나면 정리 코드 자동 실행

2. **컨텍스트 관리자와 궁합이 좋음**
   - `async with` + `yield` = 완벽한 자원 관리
   - 예외 상황에도 안전

3. **FastAPI 의존성 주입의 핵심**
   - `Depends()`와 함께 사용
   - 자동으로 생명주기 관리
   - 코드가 깔끔해짐

4. **메모리 누수 방지**
   - 수동 관리보다 훨씬 안전
   - 까먹고 안 닫는 실수 방지

이게 async-yield 패턴의 전부임. 처음엔 복잡해 보이지만 익숙해지면 엄청 편함.

