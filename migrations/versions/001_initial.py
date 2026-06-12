"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    # 创建pgvector扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 创建collections表
    op.create_table(
        'collections',
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(length=50), nullable=True),
        sa.Column('chunk_size', sa.Integer(), nullable=True),
        sa.Column('chunk_overlap', sa.Integer(), nullable=True),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('collection_id')
    )
    op.create_index(op.f('ix_collections_collection_id'), 'collections', ['collection_id'], unique=False)

    # 创建documents表
    op.create_table(
        'documents',
        sa.Column('doc_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('doc_type', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=True),
        sa.Column('severity', sa.String(length=10), nullable=True),
        sa.Column('affected_systems', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('collection_id', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.Column('utime', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.collection_id'], ),
        sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_index(op.f('ix_documents_author_id'), 'documents', ['author_id'], unique=False)
    op.create_index(op.f('ix_documents_collection_id'), 'documents', ['collection_id'], unique=False)
    op.create_index(op.f('ix_documents_doc_id'), 'documents', ['doc_id'], unique=False)
    op.create_index(op.f('ix_documents_doc_type'), 'documents', ['doc_type'], unique=False)
    op.create_index(op.f('ix_documents_org_id'), 'documents', ['org_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)

    # 创建chunks表
    op.create_table(
        'chunks',
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=True),
        sa.Column('collection_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('chunk_metadata', sa.JSON(), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.doc_id'], ),
        sa.PrimaryKeyConstraint('chunk_id')
    )
    op.create_index(op.f('ix_chunks_chunk_id'), 'chunks', ['chunk_id'], unique=False)
    op.create_index(op.f('ix_chunks_collection_id'), 'chunks', ['collection_id'], unique=False)
    op.create_index(op.f('ix_chunks_doc_id'), 'chunks', ['doc_id'], unique=False)

    # 创建IVFFlat索引加速向量检索
    op.execute('CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')

    # 创建incident_templates表
    op.create_table(
        'incident_templates',
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('symptom_template', sa.Text(), nullable=True),
        sa.Column('root_cause_template', sa.Text(), nullable=True),
        sa.Column('resolution_template', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('subcategory', sa.String(length=50), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.Column('utime', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('template_id')
    )
    op.create_index(op.f('ix_incident_templates_category'), 'incident_templates', ['category'], unique=False)
    op.create_index(op.f('ix_incident_templates_template_id'), 'incident_templates', ['template_id'], unique=False)

    # 创建sop_templates表
    op.create_table(
        'sop_templates',
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.Column('utime', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('template_id')
    )
    op.create_index(op.f('ix_sop_templates_category'), 'sop_templates', ['category'], unique=False)
    op.create_index(op.f('ix_sop_templates_template_id'), 'sop_templates', ['template_id'], unique=False)

    # 创建query_history表
    op.create_table(
        'query_history',
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('source_docs', sa.JSON(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('ctime', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('query_id')
    )
    op.create_index(op.f('ix_query_history_query_id'), 'query_history', ['query_id'], unique=False)
    op.create_index(op.f('ix_query_history_user_id'), 'query_history', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_query_history_user_id'), table_name='query_history')
    op.drop_index(op.f('ix_query_history_query_id'), table_name='query_history')
    op.drop_table('query_history')

    op.drop_index(op.f('ix_sop_templates_template_id'), table_name='sop_templates')
    op.drop_index(op.f('ix_sop_templates_category'), table_name='sop_templates')
    op.drop_table('sop_templates')

    op.drop_index(op.f('ix_incident_templates_template_id'), table_name='incident_templates')
    op.drop_index(op.f('ix_incident_templates_category'), table_name='incident_templates')
    op.drop_table('incident_templates')

    op.drop_index(op.f('ix_chunks_doc_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_collection_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_chunk_id'), table_name='chunks')
    op.drop_table('chunks')

    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_org_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_doc_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_doc_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_collection_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_author_id'), table_name='documents')
    op.drop_table('documents')

    op.drop_index(op.f('ix_collections_collection_id'), table_name='collections')
    op.drop_table('collections')
