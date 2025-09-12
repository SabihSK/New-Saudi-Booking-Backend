from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from collections.abc import AsyncGenerator
from app.core.config import settings
from app.features.users.models import User, UserRole
from app.core.security.auth import get_password_hash


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency for FastAPI routes
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# Initialize DB (create tables)
async def init_db():
    async with engine.begin() as conn:
        # ⚠️ drops everything and recreates (dev only!)
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    # ✅ Seed admin user if not exists
    async with async_session_maker() as session:
        stmt = select(User).where(User.role == UserRole.admin)
        result = await session.exec(stmt)
        admin = result.first()

        if not admin:
            admin = User(
                email="admin@admin.com",
                full_name="Default Admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.admin,
            )
            session.add(admin)
            await session.commit()
            print("✅ Default admin created: admin@admin.com / admin123")
        else:
            print("ℹ️ Admin already exists, skipping seeding.")
