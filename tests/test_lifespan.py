import pytest
from app.main import app

# app起動時のlifespanテスト
@pytest.mark.asyncio
async def test_lifespan():
    async with app.router.lifespan_context(app):
        # init_redisテスト
        assert app.state.redis is not None
    
    # close_redisテスト
    assert hasattr(app.state, "redis")