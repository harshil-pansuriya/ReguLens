from fastapi import FastAPI
from asyncpg import Pool, create_pool
from app.core.config import settings
from loguru import logger

async def get_db_pool() -> Pool:
    try:
        pool = await create_pool(
            user= settings.postgres_user,
            password= settings.postgres_password,
            database= settings.postgres_db,
            host= settings.postgres_host,
            port= settings.postgres_port,
            min_size= 1,
            max_size= 10    
        )
        async with pool.acquire() as conn:
            await conn.execute('SELECT 1')
        logger.info('Database Connection POOl created')
        
        return pool
    except Exception as e:
        logger.error(f'Failed to Connect Daabase: {e}')
        raise
    
    
async def init_db(app: FastAPI) -> None:
    app.state_db_pool= await get_db_pool()  #initialize db connection pool for FastAPI App
    
async def closed_db(app: FastAPI) -> None:
    if hasattr(app.state, 'db_pool') and app.state_db_pool:
        await app.state_db_pool.close()
        logger.info('Database connection pool closed.')
    