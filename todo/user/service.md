# service.py 상세 설명

## 이 파일은 뭔가?
비즈니스 로직과 트랜잭션을 관리하는 계층임. Service 패턴이라고 부름.

---

## 전체 코드

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .repository import TodoRepository
from .models import Todo

class TodoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TodoRepository(session)

    async def create(self, text: str) -> Todo:
        try:
            item = await self.repo.add(text)
            await self.session.commit()
            await self.session.refresh(item)
            return item
        except IntegrityError:
            await self.session.rollback()
            raise
```

---

## Service의 역할

### 계층 구조 복습
```
Router
   ↓
Service ← 여기
   ↓
Repository
   ↓
Database
```

### Service가 하는 일
1. **비즈니스 로직**: 규칙, 검증, 계산
2. **트랜잭션 관리**: commit, rollback
3. **예외 처리**: 에러 잡고 복구
4. **Repository 조합**: 여러 Repository 사용

### Repository와 차이
```
Repository: "DB에서 가져와", "DB에 저장해"
Service: "유효한지 확인하고, 저장하고, 에러나면 취소해"
```

**Service가 더 높은 레벨임.**

---

## Import 설명

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .repository import TodoRepository
from .models import Todo
```

- `AsyncSession`: 비동기 세션
- `IntegrityError`: DB 무결성 에러 (중복, 외래키 위반 등)
- `TodoRepository`: 데이터 접근 계층
- `Todo`: Todo 모델

---

## TodoService 클래스

### 생성자
```python
def __init__(self, session: AsyncSession):
    self.session = session
    self.repo = TodoRepository(session)
```

**동작:**
1. 세션 저장
2. 같은 세션으로 Repository 생성

**중요 포인트:**
- Service와 Repository가 같은 세션 공유
- 같은 트랜잭션 안에서 작업
- 세션은 Router에서 의존성 주입으로 받음

**사용 예시:**
```python
# router.py
def get_service(session: AsyncSession = Depends(db_dep)) -> TodoService:
    return TodoService(session)

@router.post("/todo")
async def create_todo(service: TodoService = Depends(get_service)):
    # service 사용
    pass
```

---

## create 메서드 상세 분석

```python
async def create(self, text: str) -> Todo:
    try:
        item = await self.repo.add(text)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    except IntegrityError:
        await self.session.rollback()
        raise
```

### 전체 흐름

```
1. Repository에 추가 요청
   ↓
2. commit (DB에 실제 저장)
   ↓
3. refresh (DB 생성 값 가져오기)
   ↓
4. 성공 → 객체 반환
   에러 → rollback 후 예외 던짐
```

---

## 단계별 상세 설명

### 1단계: Repository 호출
```python
item = await self.repo.add(text)
```

**동작:**
- Repository의 `add()` 메서드 호출
- Todo 객체 생성하고 세션에 추가
- **아직 DB에 저장 안 됨** (pending 상태)

**item 상태:**
```python
item.id  # None (아직 DB가 생성 안 함)
item.text  # "장보기"
item.done  # False
item.createdAt  # None (아직 DB가 생성 안 함)
```

---

### 2단계: Commit
```python
await self.session.commit()
```

**동작:**
- 세션에 쌓인 모든 변경사항을 DB에 반영
- 실제 SQL 실행됨

**실제 SQL:**
```sql
BEGIN;
INSERT INTO todo (task, done) VALUES ('장보기', 0);
COMMIT;
```

**commit 후 item 상태:**
```python
# commit 후에도 item은 "만료(expired)" 상태
# 속성 접근하면 자동으로 다시 조회함
item.id  # DB 접근 → 1 (새로 조회)
```

**만료(expired)란?**
- commit 후 객체의 값이 DB와 다를 수 있음
- 접근 시 자동으로 다시 조회 (새 쿼리 발생)
- 성능 이슈 가능

---

### 3단계: Refresh
```python
await self.session.refresh(item)
```

**동작:**
- DB에서 최신 데이터를 명시적으로 가져옴
- `id`, `createdAt` 같은 DB 생성 값을 업데이트

**실제 SQL:**
```sql
SELECT * FROM todo WHERE id = 1;
```

**refresh 후 item 상태:**
```python
item.id  # 1 (DB에서 가져옴)
item.text  # "장보기"
item.done  # False
item.createdAt  # 2024-01-01 12:00:00 (DB에서 가져옴)
```

**왜 refresh?**
- DB가 자동 생성하는 값 확인 필요
- `id` (autoincrement)
- `createdAt` (CURRENT_TIMESTAMP)
- API 응답에 포함해야 함

**refresh 안 하면?**
```python
# commit 후
print(item.id)  # DB 조회 발생 (자동)
print(item.text)  # DB 조회 발생 (자동)
print(item.createdAt)  # DB 조회 발생 (자동)
# 여러 번 조회 → 비효율적
```

**refresh 하면:**
```python
# refresh로 한 번에 조회
print(item.id)  # 메모리 값 사용
print(item.text)  # 메모리 값 사용
print(item.createdAt)  # 메모리 값 사용
# 한 번만 조회 → 효율적
```

---

### 4단계: 예외 처리
```python
except IntegrityError:
    await self.session.rollback()
    raise
```

**IntegrityError란?**
- DB 무결성 제약 위반 에러
- 예: UNIQUE 중복, NOT NULL 위반, 외래키 위반

**rollback() 역할:**
- 트랜잭션 취소
- DB를 변경 이전 상태로 되돌림

**raise 역할:**
- 에러를 상위(Router)로 전달
- FastAPI가 500 에러 반환

**동작 예시:**
```python
try:
    item = await self.repo.add(text)
    await self.session.commit()  # 여기서 에러 발생!
except IntegrityError:
    await self.session.rollback()  # 취소
    raise  # 에러 전달
```

**실제 SQL:**
```sql
BEGIN;
INSERT INTO todo (task, done) VALUES ('장보기', 0);
-- 에러 발생 (예: 중복)
ROLLBACK;  -- 취소
```

---

## 트랜잭션 흐름 예시

### 성공 케이스
```python
# 1. 시작
service = TodoService(session)

# 2. create 호출
todo = await service.create("장보기")

# 3. 내부 동작
# - repo.add() → 세션에 추가
# - commit() → DB에 저장
# - refresh() → 최신 값 가져오기
# - return todo

# 4. 결과
print(todo.id)  # 1
print(todo.text)  # "장보기"
```

### 실패 케이스
```python
# 1. 시작
service = TodoService(session)

# 2. create 호출
try:
    todo = await service.create("중복값")
except IntegrityError:
    print("에러 발생")

# 3. 내부 동작
# - repo.add() → 세션에 추가
# - commit() → 에러 발생!
# - rollback() → 취소
# - raise → 에러 전달
```

---

## 실전 확장

### 추가 메서드 예시

```python
class TodoService:
    # 기존 코드...
    
    async def get_all(self) -> list[Todo]:
        """전체 목록 조회"""
        return await self.repo.list_desc()
    
    async def get_by_id(self, todo_id: int) -> Todo | None:
        """ID로 조회"""
        return await self.repo.get_by_id(todo_id)
    
    async def update_status(self, todo_id: int, done: bool) -> Todo | None:
        """완료 상태 변경"""
        try:
            item = await self.repo.get_by_id(todo_id)
            if not item:
                return None
            
            item.done = done
            await self.session.commit()
            await self.session.refresh(item)
            return item
        except IntegrityError:
            await self.session.rollback()
            raise
    
    async def delete(self, todo_id: int) -> bool:
        """삭제"""
        try:
            item = await self.repo.get_by_id(todo_id)
            if not item:
                return False
            
            await self.session.delete(item)
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            raise
```

### 비즈니스 로직 추가

```python
async def create(self, text: str) -> Todo:
    # 비즈니스 규칙 검증
    if len(text.strip()) < 3:
        raise ValueError("할 일은 3글자 이상이어야 합니다")
    
    if "욕설" in text:
        raise ValueError("부적절한 내용이 포함되어 있습니다")
    
    try:
        # 정제
        text = text.strip()
        
        item = await self.repo.add(text)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    except IntegrityError:
        await self.session.rollback()
        raise
```

### 여러 Repository 조합

```python
class TodoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.todo_repo = TodoRepository(session)
        self.user_repo = UserRepository(session)
    
    async def create_with_user(self, text: str, user_id: int) -> Todo:
        """사용자 확인 후 Todo 생성"""
        try:
            # 사용자 존재 확인
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("사용자를 찾을 수 없습니다")
            
            # Todo 생성
            item = await self.todo_repo.add(text)
            item.user_id = user_id
            
            # 한 번에 commit
            await self.session.commit()
            await self.session.refresh(item)
            return item
        except IntegrityError:
            await self.session.rollback()
            raise
```

---

## 주의사항

### 1. commit은 Service에서만
```python
# ✅ Service가 commit
async def create(self, text: str):
    item = await self.repo.add(text)
    await self.session.commit()  # 여기서

# ❌ Repository에서 commit (안 됨)
async def add(self, text: str):
    item = Todo(text=text)
    self.session.add(item)
    await self.session.commit()  # 이러면 안 됨
```

### 2. refresh 잊지 말기
```python
# ❌ refresh 안 하면 DB 생성 값 없음
async def create(self, text: str):
    item = await self.repo.add(text)
    await self.session.commit()
    return item  # id, createdAt이 None일 수 있음

# ✅ refresh로 최신 값 가져오기
async def create(self, text: str):
    item = await self.repo.add(text)
    await self.session.commit()
    await self.session.refresh(item)  # 필수
    return item
```

### 3. 예외 처리 패턴
```python
# ✅ rollback 후 raise
try:
    await self.session.commit()
except IntegrityError:
    await self.session.rollback()  # 먼저 rollback
    raise  # 그 다음 raise

# ❌ rollback만 하고 raise 안 함
try:
    await self.session.commit()
except IntegrityError:
    await self.session.rollback()
    # 에러 숨김 → 나중에 버그 발생
```

---

## 핵심 정리

1. **Service = 비즈니스 로직 + 트랜잭션**
   - 규칙 검증
   - commit/rollback 관리
   - 예외 처리

2. **트랜잭션 3단계**
   - Repository 호출
   - commit (저장)
   - refresh (최신화)

3. **예외 처리 필수**
   - IntegrityError 잡기
   - rollback으로 취소
   - raise로 전달

4. **Repository 조합**
   - 여러 Repository 사용 가능
   - 같은 세션 = 같은 트랜잭션

5. **책임 분리**
   - Repository: 데이터만
   - Service: 로직 + 트랜잭션
   - Router: HTTP만

Service는 오케스트라 지휘자임. Repository들을 조합해서 비즈니스 로직을 완성함.

