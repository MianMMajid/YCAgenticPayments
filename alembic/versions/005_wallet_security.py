"""Add wallet security tables.

Revision ID: 005
Revises: 004
Create Date: 2025-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create wallet security tables."""
    
    # Create wallet_security_configs table
    op.create_table(
        'wallet_security_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('wallet_id', sa.String(length=255), nullable=False),
        sa.Column('multi_sig_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('multi_sig_threshold_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='50000.00'),
        sa.Column('required_approvers', sa.Numeric(), nullable=False, server_default='2'),
        sa.Column('time_lock_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('time_lock_duration_hours', sa.Numeric(), nullable=False, server_default='24'),
        sa.Column('time_lock_threshold_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='100000.00'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_by', sa.String(length=255), nullable=True),
        sa.Column('pause_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_security_configs_wallet_id', 'wallet_security_configs', ['wallet_id'], unique=True)
    
    # Create wallet_operations table
    op.create_table(
        'wallet_operations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=False),
        sa.Column('wallet_id', sa.String(length=255), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('recipient_id', sa.String(length=255), nullable=False),
        sa.Column('operation_data', sa.JSON(), nullable=True),
        sa.Column('required_approvals', sa.Numeric(), nullable=False, server_default='1'),
        sa.Column('current_approvals', sa.Numeric(), nullable=False, server_default='0'),
        sa.Column('approvers', sa.JSON(), nullable=True),
        sa.Column('time_lock_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('initiated_by', sa.String(length=255), nullable=False),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_operations_transaction_id', 'wallet_operations', ['transaction_id'])
    
    # Create wallet_audit_logs table
    op.create_table(
        'wallet_audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('wallet_id', sa.String(length=255), nullable=False),
        sa.Column('operation_id', sa.String(length=255), nullable=True),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_audit_logs_wallet_id', 'wallet_audit_logs', ['wallet_id'])


def downgrade() -> None:
    """Drop wallet security tables."""
    op.drop_index('ix_wallet_audit_logs_wallet_id', table_name='wallet_audit_logs')
    op.drop_table('wallet_audit_logs')
    
    op.drop_index('ix_wallet_operations_transaction_id', table_name='wallet_operations')
    op.drop_table('wallet_operations')
    
    op.drop_index('ix_wallet_security_configs_wallet_id', table_name='wallet_security_configs')
    op.drop_table('wallet_security_configs')
