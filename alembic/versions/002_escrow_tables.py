"""Add escrow tables for intelligent escrow agents

Revision ID: 002
Revises: 001
Create Date: 2025-11-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create escrow-related tables."""
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('buyer_agent_id', sa.String(length=255), nullable=False),
        sa.Column('seller_agent_id', sa.String(length=255), nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=False),
        sa.Column('earnest_money', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_purchase_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('state', sa.Enum(
            'INITIATED', 'FUNDED', 'VERIFICATION_IN_PROGRESS', 'VERIFICATION_COMPLETE',
            'SETTLEMENT_PENDING', 'SETTLED', 'DISPUTED', 'CANCELLED',
            name='transactionstate'
        ), nullable=False),
        sa.Column('wallet_id', sa.String(length=255), nullable=True),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('target_closing_date', sa.DateTime(), nullable=False),
        sa.Column('actual_closing_date', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_buyer_agent_id'), 'transactions', ['buyer_agent_id'], unique=False)
    op.create_index(op.f('ix_transactions_seller_agent_id'), 'transactions', ['seller_agent_id'], unique=False)
    op.create_index(op.f('ix_transactions_property_id'), 'transactions', ['property_id'], unique=False)
    op.create_index(op.f('ix_transactions_state'), 'transactions', ['state'], unique=False)
    op.create_index(op.f('ix_transactions_wallet_id'), 'transactions', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)
    
    # Create verification_reports table (must be created before verification_tasks due to FK)
    op.create_table(
        'verification_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('report_type', sa.Enum(
            'TITLE_SEARCH', 'INSPECTION', 'APPRAISAL', 'LENDING',
            name='verificationtype'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'APPROVED', 'REJECTED', 'NEEDS_REVIEW',
            name='reportstatus'
        ), nullable=False),
        sa.Column('findings', sa.JSON(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer_notes', sa.String(length=2000), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_reports_agent_id'), 'verification_reports', ['agent_id'], unique=False)
    op.create_index(op.f('ix_verification_reports_report_type'), 'verification_reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_verification_reports_status'), 'verification_reports', ['status'], unique=False)
    op.create_index(op.f('ix_verification_reports_submitted_at'), 'verification_reports', ['submitted_at'], unique=False)
    
    # Create verification_tasks table
    op.create_table(
        'verification_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('verification_type', sa.Enum(
            'TITLE_SEARCH', 'INSPECTION', 'APPRAISAL', 'LENDING',
            name='verificationtype'
        ), nullable=False),
        sa.Column('assigned_agent_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum(
            'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED',
            name='taskstatus'
        ), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=False),
        sa.Column('payment_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('report_id', sa.String(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['verification_reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_tasks_transaction_id'), 'verification_tasks', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_verification_tasks_assigned_agent_id'), 'verification_tasks', ['assigned_agent_id'], unique=False)
    op.create_index(op.f('ix_verification_tasks_status'), 'verification_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_verification_tasks_verification_type'), 'verification_tasks', ['verification_type'], unique=False)
    op.create_index(op.f('ix_verification_tasks_deadline'), 'verification_tasks', ['deadline'], unique=False)
    
    # Add FK from verification_reports to verification_tasks
    op.create_foreign_key(
        'fk_verification_reports_task_id',
        'verification_reports', 'verification_tasks',
        ['task_id'], ['id']
    )
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('wallet_id', sa.String(length=255), nullable=False),
        sa.Column('payment_type', sa.Enum(
            'EARNEST_MONEY', 'VERIFICATION', 'COMMISSION', 'CLOSING_COST', 'SETTLEMENT',
            name='paymenttype'
        ), nullable=False),
        sa.Column('recipient_id', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED',
            name='paymentstatus'
        ), nullable=False),
        sa.Column('blockchain_tx_hash', sa.String(length=255), nullable=True),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_transaction_id'), 'payments', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_payments_wallet_id'), 'payments', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_payments_payment_type'), 'payments', ['payment_type'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_recipient_id'), 'payments', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_payments_blockchain_tx_hash'), 'payments', ['blockchain_tx_hash'], unique=False)
    
    # Create settlements table
    op.create_table(
        'settlements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('seller_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('buyer_agent_commission', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('seller_agent_commission', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('closing_costs', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('distributions', sa.JSON(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(length=255), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_settlements_transaction_id'), 'settlements', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_settlements_blockchain_tx_hash'), 'settlements', ['blockchain_tx_hash'], unique=False)
    op.create_index(op.f('ix_settlements_executed_at'), 'settlements', ['executed_at'], unique=False)
    
    # Create blockchain_events table
    op.create_table(
        'blockchain_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(length=255), nullable=False),
        sa.Column('block_number', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blockchain_events_transaction_id'), 'blockchain_events', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_blockchain_events_event_type'), 'blockchain_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_blockchain_events_blockchain_tx_hash'), 'blockchain_events', ['blockchain_tx_hash'], unique=False)
    op.create_index(op.f('ix_blockchain_events_timestamp'), 'blockchain_events', ['timestamp'], unique=False)


def downgrade() -> None:
    """Drop escrow-related tables."""
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_blockchain_events_timestamp'), table_name='blockchain_events')
    op.drop_index(op.f('ix_blockchain_events_blockchain_tx_hash'), table_name='blockchain_events')
    op.drop_index(op.f('ix_blockchain_events_event_type'), table_name='blockchain_events')
    op.drop_index(op.f('ix_blockchain_events_transaction_id'), table_name='blockchain_events')
    op.drop_table('blockchain_events')
    
    op.drop_index(op.f('ix_settlements_executed_at'), table_name='settlements')
    op.drop_index(op.f('ix_settlements_blockchain_tx_hash'), table_name='settlements')
    op.drop_index(op.f('ix_settlements_transaction_id'), table_name='settlements')
    op.drop_table('settlements')
    
    op.drop_index(op.f('ix_payments_blockchain_tx_hash'), table_name='payments')
    op.drop_index(op.f('ix_payments_recipient_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_payment_type'), table_name='payments')
    op.drop_index(op.f('ix_payments_wallet_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
    op.drop_table('payments')
    
    op.drop_constraint('fk_verification_reports_task_id', 'verification_reports', type_='foreignkey')
    
    op.drop_index(op.f('ix_verification_tasks_deadline'), table_name='verification_tasks')
    op.drop_index(op.f('ix_verification_tasks_verification_type'), table_name='verification_tasks')
    op.drop_index(op.f('ix_verification_tasks_status'), table_name='verification_tasks')
    op.drop_index(op.f('ix_verification_tasks_assigned_agent_id'), table_name='verification_tasks')
    op.drop_index(op.f('ix_verification_tasks_transaction_id'), table_name='verification_tasks')
    op.drop_table('verification_tasks')
    
    op.drop_index(op.f('ix_verification_reports_submitted_at'), table_name='verification_reports')
    op.drop_index(op.f('ix_verification_reports_status'), table_name='verification_reports')
    op.drop_index(op.f('ix_verification_reports_report_type'), table_name='verification_reports')
    op.drop_index(op.f('ix_verification_reports_agent_id'), table_name='verification_reports')
    op.drop_table('verification_reports')
    
    op.drop_index(op.f('ix_transactions_created_at'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_wallet_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_state'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_property_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_seller_agent_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_buyer_agent_id'), table_name='transactions')
    op.drop_table('transactions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS transactionstate')
    op.execute('DROP TYPE IF EXISTS verificationtype')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
