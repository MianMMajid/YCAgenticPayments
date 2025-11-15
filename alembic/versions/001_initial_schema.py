"""Initial schema with all tables and indexes

Revision ID: 001
Revises: 
Create Date: 2025-11-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with indexes."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('phone_number', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('preferred_locations', sa.JSON(), nullable=True),
        sa.Column('max_budget', sa.Integer(), nullable=True),
        sa.Column('min_beds', sa.Integer(), nullable=True),
        sa.Column('min_baths', sa.Integer(), nullable=True),
        sa.Column('property_types', sa.JSON(), nullable=True),
        sa.Column('pre_approved', sa.Boolean(), nullable=True),
        sa.Column('pre_approval_amount', sa.Integer(), nullable=True),
        sa.Column('google_calendar_token', sa.String(length=1000), nullable=True),
        sa.Column('google_calendar_refresh_token', sa.String(length=1000), nullable=True),
        sa.Column('last_active', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)
    
    # Create search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('max_price', sa.Integer(), nullable=True),
        sa.Column('min_price', sa.Integer(), nullable=True),
        sa.Column('min_beds', sa.Integer(), nullable=True),
        sa.Column('min_baths', sa.Integer(), nullable=True),
        sa.Column('property_type', sa.String(length=100), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('total_found', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_user_id'), 'search_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_search_history_created_at'), 'search_history', ['created_at'], unique=False)
    
    # Create risk_analyses table
    op.create_table(
        'risk_analyses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('list_price', sa.Integer(), nullable=False),
        sa.Column('flags', sa.JSON(), nullable=True),
        sa.Column('overall_risk', sa.String(length=50), nullable=True),
        sa.Column('estimated_value', sa.Integer(), nullable=True),
        sa.Column('tax_assessment', sa.Integer(), nullable=True),
        sa.Column('flood_zone', sa.String(length=50), nullable=True),
        sa.Column('crime_score', sa.Integer(), nullable=True),
        sa.Column('data_sources', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_analyses_user_id'), 'risk_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_risk_analyses_property_id'), 'risk_analyses', ['property_id'], unique=False)
    op.create_index(op.f('ix_risk_analyses_created_at'), 'risk_analyses', ['created_at'], unique=False)
    
    # Create viewings table
    op.create_table(
        'viewings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('listing_url', sa.String(length=1000), nullable=True),
        sa.Column('requested_time', sa.String(length=50), nullable=False),
        sa.Column('confirmed_time', sa.String(length=50), nullable=True),
        sa.Column('agent_name', sa.String(length=255), nullable=True),
        sa.Column('agent_email', sa.String(length=255), nullable=True),
        sa.Column('agent_phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('calendar_event_id', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_viewings_user_id'), 'viewings', ['user_id'], unique=False)
    op.create_index(op.f('ix_viewings_status'), 'viewings', ['status'], unique=False)
    op.create_index(op.f('ix_viewings_created_at'), 'viewings', ['created_at'], unique=False)
    
    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('offer_price', sa.Integer(), nullable=False),
        sa.Column('list_price', sa.Integer(), nullable=True),
        sa.Column('closing_days', sa.Integer(), nullable=False),
        sa.Column('closing_date', sa.String(length=50), nullable=True),
        sa.Column('financing_type', sa.String(length=50), nullable=False),
        sa.Column('contingencies', sa.JSON(), nullable=True),
        sa.Column('earnest_money', sa.Integer(), nullable=True),
        sa.Column('special_terms', sa.String(length=2000), nullable=True),
        sa.Column('envelope_id', sa.String(length=255), nullable=True),
        sa.Column('signing_url', sa.String(length=1000), nullable=True),
        sa.Column('template_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.String(length=50), nullable=True),
        sa.Column('signed_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offers_user_id'), 'offers', ['user_id'], unique=False)
    op.create_index(op.f('ix_offers_status'), 'offers', ['status'], unique=False)
    op.create_index(op.f('ix_offers_created_at'), 'offers', ['created_at'], unique=False)
    op.create_index(op.f('ix_offers_envelope_id'), 'offers', ['envelope_id'], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_offers_envelope_id'), table_name='offers')
    op.drop_index(op.f('ix_offers_created_at'), table_name='offers')
    op.drop_index(op.f('ix_offers_status'), table_name='offers')
    op.drop_index(op.f('ix_offers_user_id'), table_name='offers')
    op.drop_table('offers')
    
    op.drop_index(op.f('ix_viewings_created_at'), table_name='viewings')
    op.drop_index(op.f('ix_viewings_status'), table_name='viewings')
    op.drop_index(op.f('ix_viewings_user_id'), table_name='viewings')
    op.drop_table('viewings')
    
    op.drop_index(op.f('ix_risk_analyses_created_at'), table_name='risk_analyses')
    op.drop_index(op.f('ix_risk_analyses_property_id'), table_name='risk_analyses')
    op.drop_index(op.f('ix_risk_analyses_user_id'), table_name='risk_analyses')
    op.drop_table('risk_analyses')
    
    op.drop_index(op.f('ix_search_history_created_at'), table_name='search_history')
    op.drop_index(op.f('ix_search_history_user_id'), table_name='search_history')
    op.drop_table('search_history')
    
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_table('users')
