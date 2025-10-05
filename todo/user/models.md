# models.py 상세 설명

## 이 파일은 뭔가?
데이터베이스 테이블을 Python 클래스로 정의하는 파일임. ORM 모델이라고 부름.

---

## 전체 코드

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, TIMESTAMP
from todo.core.database import Base
from datetime import datetime
from sqlalchemy.sql import text as sa_text 

class Todo(Base):
    __tablename__ = "todo"
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text:Mapped[str] = mapped_column("task", String(255), nullable=False)
    done:Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=sa_text("CURRENT_TIMESTAMP"),
        nullable=False
    )
```

---

## Import 설명

### SQLAlchemy ORM
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, TIMESTAMP
```
- `Mapped`: Python 타입 힌트용 (IDE가 타입 인식)
- `mapped_column`: 컬럼 정의하는 함수
- `Integer, String, Boolean, TIMESTAMP`: 데이터베이스 타입들

### Base 클래스
```python
from todo.core.database import Base
```
- database.py에서 만든 베이스 클래스
- 이걸 상속받아야 SQLAlchemy가 테이블로 인식함

### 기타
```python
from datetime import datetime
from sqlalchemy.sql import text as sa_text
```
- `datetime`: Python의 날짜/시간 타입
- `sa_text`: SQL 문자열을 SQLAlchemy가 이해하도록 변환

---

## Todo 모델 분석

### 클래스 선언
```python
class Todo(Base):
    __tablename__ = "todo"
```
- `Base` 상속: 이 클래스가 데이터베이스 테이블임을 선언
- `__tablename__ = "todo"`: 실제 DB 테이블 이름
- 클래스명은 `Todo`(대문자), 테이블명은 `todo`(소문자)

---

## 컬럼 상세 설명

### 1. id 컬럼
```python
id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
```

**분석:**
- `id: Mapped[int]`: Python에서는 int 타입
- `Integer`: DB에서는 Integer 타입
- `primary_key=True`: 기본키 (고유 식별자)
- `autoincrement=True`: 자동 증가 (1, 2, 3...)

**실제 DB:**
```sql
id INT PRIMARY KEY AUTO_INCREMENT
```

---

### 2. text 컬럼
```python
text:Mapped[str] = mapped_column("task", String(255), nullable=False)
```

**분석:**
- `text: Mapped[str]`: Python에서는 str 타입으로 `text` 속성 사용
- `"task"`: DB에서는 실제로 `task` 컬럼명 사용
- `String(255)`: 최대 255자 문자열
- `nullable=False`: NULL 불가 (필수 값)

**Python vs DB:**
- Python: `todo.text`
- DB: `task` 컬럼

**왜 다르게?**
- DB 설계가 먼저 되어있을 때 유용
- Python 코드는 읽기 좋게, DB는 기존 구조 유지

**실제 DB:**
```sql
task VARCHAR(255) NOT NULL
```

---

### 3. done 컬럼
```python
done:Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
```

**분석:**
- `done: Mapped[bool]`: Python에서는 True/False
- `Boolean`: DB에서는 Boolean (또는 TINYINT)
- `nullable=False`: NULL 불가
- `server_default="0"`: DB 레벨 기본값 (0 = False)

**server_default vs default:**
- `server_default`: DB 서버가 처리 (INSERT 시 자동)
- `default`: Python 코드가 처리 (명시 안 하면 적용)

**실제 DB:**
```sql
done BOOLEAN NOT NULL DEFAULT 0
```

---

### 4. createdAt 컬럼
```python
createdAt: Mapped[datetime] = mapped_column(
    TIMESTAMP,
    server_default=sa_text("CURRENT_TIMESTAMP"),
    nullable=False
)
```

**분석:**
- `createdAt: Mapped[datetime]`: Python datetime 객체
- `TIMESTAMP`: DB 타임스탬프 타입
- `server_default=sa_text("CURRENT_TIMESTAMP")`: 현재 시각 자동 입력
- `nullable=False`: NULL 불가

**sa_text를 쓰는 이유:**
- `"CURRENT_TIMESTAMP"`는 SQL 함수
- 문자열 그대로 전달하면 안 됨
- `sa_text()`로 감싸야 SQLAlchemy가 SQL로 인식

**실제 DB:**
```sql
createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```

---

## Mapped 타입의 장점

### Before (옛날 방식)
```python
class Todo(Base):
    __tablename__ = "todo"
    
    id = Column(Integer, primary_key=True)
    text = Column(String(255))
```
- 타입 힌트 없음
- IDE가 타입 모름
- 자동완성 안 됨

### After (현재 방식)
```python
class Todo(Base):
    __tablename__ = "todo"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(255))
```
- 타입 힌트 있음
- IDE가 타입 인식
- 자동완성 작동
- 타입 체크 가능

**이게 핵심임.** 코드 작성이 훨씬 편해짐.

---

## 실제 사용 예시

### 객체 생성
```python
# 새 Todo 생성
todo = Todo(text="장보기", done=False)
# id와 createdAt는 DB가 자동 생성

print(todo.text)  # "장보기"
print(todo.done)  # False
```

### 데이터베이스 저장
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def create_todo(session: AsyncSession):
    todo = Todo(text="운동하기", done=False)
    session.add(todo)
    await session.commit()
    await session.refresh(todo)  # DB가 생성한 id, createdAt 가져오기
    
    print(todo.id)  # 1 (자동 생성됨)
    print(todo.createdAt)  # 2024-01-01 12:00:00 (자동 생성됨)
```

### 데이터 수정
```python
async def update_todo(session: AsyncSession, todo_id: int):
    todo = await session.get(Todo, todo_id)
    todo.done = True  # 완료 처리
    await session.commit()
```

### 데이터 조회
```python
from sqlalchemy import select

async def get_all_todos(session: AsyncSession):
    result = await session.execute(select(Todo))
    todos = result.scalars().all()
    
    for todo in todos:
        print(f"{todo.id}: {todo.text} - {'완료' if todo.done else '미완료'}")
```

---

## 주의사항

### 1. 컬럼명 불일치 조심
```python
text:Mapped[str] = mapped_column("task", ...)
```
- Python: `todo.text`
- DB: `task` 컬럼
- 헷갈리지 않게 주의

### 2. nullable 설정
```python
# ❌ nullable 설정 안 하면 기본값은 True (NULL 허용)
text: Mapped[str] = mapped_column(String(255))

# ✅ 필수 값은 명시적으로 False
text: Mapped[str] = mapped_column(String(255), nullable=False)
```

### 3. 타입 일관성
```python
# ❌ Mapped 타입과 mapped_column 타입 불일치
text: Mapped[int] = mapped_column(String(255))  # 에러 발생 가능

# ✅ 타입 일치
text: Mapped[str] = mapped_column(String(255))
```

### 4. server_default vs default
```python
# server_default: DB가 처리 (추천)
done: Mapped[bool] = mapped_column(Boolean, server_default="0")

# default: Python이 처리 (마이그레이션 시 DB에 반영 안 됨)
done: Mapped[bool] = mapped_column(Boolean, default=False)
```

---

## 테이블 생성

### 자동 생성 (개발 환경)
```python
from todo.core.database import engine, Base
from todo.user.models import Todo

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### SQL로 생성 (프로덕션)
```sql
CREATE TABLE todo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task VARCHAR(255) NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0,
    createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 핵심 정리

1. **모델 = 데이터베이스 테이블**
   - Python 클래스로 테이블 정의
   - ORM이 자동으로 SQL 생성

2. **Mapped 타입 필수**
   - IDE 지원 받으려면 필수
   - 타입 안정성 확보

3. **컬럼 이름 주의**
   - Python 속성명 ≠ DB 컬럼명 가능
   - 첫 번째 인자로 DB 컬럼명 지정

4. **기본값 설정 위치**
   - `server_default`: DB 레벨 (추천)
   - `default`: Python 레벨

5. **자동 생성 컬럼**
   - `autoincrement`: id 자동 증가
   - `CURRENT_TIMESTAMP`: 현재 시각 자동 입력

모델은 데이터 구조의 청사진임. 잘 설계하면 나머지가 편해짐.

