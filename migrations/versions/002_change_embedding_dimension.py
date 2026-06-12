"""change embedding dimension from 1536 to 512

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

切换为本地 BGE-small-zh-v1.5 嵌入模型（512维）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 清空旧的无用 chunk 数据（之前因 API 404 存入的都是零向量）
    op.execute('DELETE FROM chunks')

    # 2. 删除旧的 IVFFlat 索引
    op.execute('DROP INDEX IF EXISTS chunks_embedding_idx')

    # 3. 修改 embedding 列维度：1536 → 512
    op.execute('ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(512)')

    # 4. 重建 IVFFlat 索引
    op.execute('CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    op.execute('DELETE FROM chunks')
    op.execute('DROP INDEX IF EXISTS chunks_embedding_idx')
    op.execute('ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536)')
    op.execute('CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')
