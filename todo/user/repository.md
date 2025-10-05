# repository.py 상세 설명

## 이 파일은 뭔가?
데이터베이스에 직접 접근하는 계층임. Repository 패턴이라고 부름.

---

## 전체 코드

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Todo

class TodoRepository:
    def __init__(self, session:AsyncSession):
        self.session = session
        
    async def add(self, text: str) -> Todo:
        item = Todo(text=text, done=False)
        self.session.add(item)
        return item

    async def get_by_id(self, todo_id: int) -> Todo | None:
        return await self.session.get(Todo, todo_id)

    async def list_desc(self) -> list[Todo]:
        result = await self.session.execute(select(Todo).order_by(Todo.id.desc()))
        return result.scalars().all()
```

---

## Repository 패턴이란?

### 계층 구조
```
Router (라우터)
   ↓
Service (비즈니스 로직)
   ↓
Repository (데이터 접근)
   ↓
Database (데이터베이스)
```

### 각 계층의 역할
- **Router**: HTTP 요청/응답 처리
- **Service**: 비즈니스 로직, 트랜잭션 관리
- **Repository**: 데이터베이스 쿼리만 담당
- **Database**: 실제 데이터 저장소

### 왜 분리하나?
```python
# ❌ 분리 안 하면
@router.post("/todo")
async def create_todo(body: TodoCreate, db: AsyncSession):
    # 라우터에 모든 로직이 섞임
    item = Todo(text=body.text, done=False)
    db.add(item)
    await db.commit()
    # ... 검증, 예외 처리 등

# ✅ 분리하면
@router.post("/todo")
async def create_todo(body: TodoCreate, service: TodoService):
    # 라우터는 단순해짐
    return await service.create(text=body.text)
```

**장점:**
- 코드 재사용 가능
- 테스트 쉬움
- 유지보수 편함
- 책임이 명확함

---

## Import 설명

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Todo
```

- `AsyncSession`: 비동기 데이터베이스 세션
- `select`: SQL SELECT 쿼리 생성
- `Todo`: Todo 모델

---

## TodoRepository 클래스

### 생성자
```python
def __init__(self, session:AsyncSession):
    self.session = session
```

**역할:**
- 세션을 받아서 인스턴스 변수에 저장
- 모든 메서드에서 이 세션 사용

**사용 예시:**
```python
# Service에서 Repository 생성
class TodoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TodoRepository(session)  # 세션 전달
```

**왜 이렇게?**
- 세션은 요청마다 새로 생성됨
- Repository도 요청마다 새로 생성됨
- 같은 세션 공유 = 같은 트랜잭션 사용

---

## 메서드 상세 분석

### 1. add 메서드

```python
async def add(self, text: str) -> Todo:
    item = Todo(text=text, done=False)
    self.session.add(item)
    return item
```

**역할:** 새 Todo 객체 생성하고 세션에 추가

**동작 단계:**
1. `Todo(text=text, done=False)`: 새 객체 생성
2. `self.session.add(item)`: 세션에 추가 (아직 DB에 저장 안 됨)
3. `return item`: 객체 반환

**중요 포인트:**
- `commit()` 안 함 → Service가 담당
- `refresh()` 안 함 → Service가 담당
- 객체 생성과 추가만 담당

**왜 commit 안 하나?**
```python
# 만약 여러 작업을 한 트랜잭션으로 묶고 싶다면?
async def create_user_with_todos(service: TodoService):
    user = await user_service.create(name="철수")
    todo1 = await todo_service.create(text="할일1")  # commit 안 함
    todo2 = await todo_service.create(text="할일2")  # commit 안 함
    # 여기서 한 번에 commit
```

**Repository는 commit 안 함.** Service가 관리함.

**실제 SQL (commit 후):**
```sql
INSERT INTO todo (task, done) VALUES ('장보기', 0);
```

---

### 2. get_by_id 메서드

```python
async def get_by_id(self, todo_id: int) -> Todo | None:
    return await self.session.get(Todo, todo_id)
```

**역할:** ID로 Todo 조회

**매개변수:**
- `todo_id: int`: 찾을 Todo의 ID

**반환값:**
- `Todo`: 찾으면 Todo 객체
- `None`: 없으면 None

**session.get() 설명:**
- SQLAlchemy의 편의 메서드
- 기본키로 조회할 때 사용
- 간단하고 빠름

**동작:**
```python
todo = await repo.get_by_id(1)
if todo:
    print(todo.text)
else:
    print("없음")
```

**실제 SQL:**
```sql
SELECT * FROM todo WHERE id = 1;
```

**대안 (select 사용):**
```python
async def get_by_id(self, todo_id: int) -> Todo | None:
    result = await self.session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    return result.scalar_one_or_none()
```

**session.get()이 더 간단함.**

---

### 3. list_desc 메서드

```python
async def list_desc(self) -> list[Todo]:
    result = await self.session.execute(select(Todo).order_by(Todo.id.desc()))
    return result.scalars().all()
```

**역할:** 모든 Todo를 ID 역순(최신순)으로 조회

**동작 분석:**

#### 1단계: 쿼리 작성
```python
select(Todo).order_by(Todo.id.desc())
```
- `select(Todo)`: Todo 테이블 전체 조회
- `.order_by(Todo.id.desc())`: ID 내림차순 정렬
- `desc()`: descending (큰 숫자부터)

#### 2단계: 쿼리 실행
```python
result = await self.session.execute(...)
```
- 쿼리를 DB에 전송하고 결과 받음
- `result`는 Result 객체 (여러 행 포함)

#### 3단계: 결과 추출
```python
return result.scalars().all()
```
- `.scalars()`: 각 행에서 첫 번째 컬럼(Todo 객체)만 추출
- `.all()`: 모든 행을 리스트로 반환

**반환값:**
```python
[Todo(id=3, ...), Todo(id=2, ...), Todo(id=1, ...)]
```

**실제 SQL:**
```sql
SELECT * FROM todo ORDER BY id DESC;
```

---

## scalars()가 뭔가?

### result 구조
```python
result = await session.execute(select(Todo))
# result = Result([
#   (Todo(id=1, ...), ),  # Row 1
#   (Todo(id=2, ...), ),  # Row 2
#   (Todo(id=3, ...), ),  # Row 3
# ])
```

각 행은 튜플 형태임.

### scalars() 사용
```python
result.scalars().all()
# [Todo(id=1, ...), Todo(id=2, ...), Todo(id=3, ...)]
```

튜플을 벗기고 첫 번째 값만 추출함.

### scalars() 안 쓰면?
```python
result.all()
# [(Todo(id=1, ...),), (Todo(id=2, ...),), (Todo(id=3, ...),)]
```

튜플이 껴있어서 불편함.

**scalars() 필수임.**

---

## 실전 활용

### 추가 메서드 예시

```python
class TodoRepository:
    # 기존 코드...
    
    async def update_done(self, todo_id: int, done: bool) -> Todo | None:
        """완료 상태 변경"""
        todo = await self.get_by_id(todo_id)
        if todo:
            todo.done = done
        return todo
    
    async def delete(self, todo_id: int) -> bool:
        """삭제"""
        todo = await self.get_by_id(todo_id)
        if todo:
            await self.session.delete(todo)
            return True
        return False
    
    async def list_by_status(self, done: bool) -> list[Todo]:
        """상태별 조회"""
        result = await self.session.execute(
            select(Todo).where(Todo.done == done).order_by(Todo.id.desc())
        )
        return result.scalars().all()
    
    async def count(self) -> int:
        """전체 개수"""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(Todo)
        )
        return result.scalar_one()
```

---

## 주의사항

### 1. commit은 Service에서
```python
# ❌ Repository에서 commit (안 함)
async def add(self, text: str):
    item = Todo(text=text, done=False)
    self.session.add(item)
    await self.session.commit()  # 이러면 안 됨

# ✅ Repository는 객체만 다룸
async def add(self, text: str) -> Todo:
    item = Todo(text=text, done=False)
    self.session.add(item)
    return item  # Service가 commit
```

### 2. 예외 처리는 Service에서
```python
# ❌ Repository에서 예외 처리 (안 함)
async def add(self, text: str):
    try:
        item = Todo(text=text, done=False)
        self.session.add(item)
    except Exception:
        # Repository는 예외 처리 안 함
        pass

# ✅ Service가 예외 처리
# Repository는 그냥 에러 던짐
```

### 3. 비즈니스 로직은 Service에서
```python
# ❌ Repository에 비즈니스 로직 (안 함)
async def add(self, text: str):
    if len(text) < 3:  # 비즈니스 규칙
        raise ValueError("3글자 이상")
    # ...

# ✅ Repository는 순수 데이터 접근만
async def add(self, text: str) -> Todo:
    item = Todo(text=text, done=False)
    self.session.add(item)
    return item
```

---

## 핵심 정리

1. **Repository = 데이터 접근 계층**
   - SQL 쿼리만 담당
   - commit, 예외처리, 비즈니스 로직 없음

2. **세션 주입**
   - 생성자로 받음
   - Service와 같은 세션 공유

3. **CRUD 메서드**
   - add: 생성
   - get_by_id: 조회
   - list_desc: 목록
   - (update, delete 추가 가능)

4. **scalars() 필수**
   - Result에서 객체 추출
   - 튜플 제거

5. **책임 분리**
   - Repository: 데이터만
   - Service: 비즈니스 로직
   - Router: HTTP 처리

Repository는 DB와 대화하는 전용 통역사임. 단순하고 명확하게 유지해야 함.

