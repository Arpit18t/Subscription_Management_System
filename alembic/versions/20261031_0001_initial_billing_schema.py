"""Initial billing and payments schema with upstream prerequisite contracts.

Revision ID: 20261031_0001
Revises: 
Create Date: 2026-10-31 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20261031_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Upstream Prerequisite Tables (created if not exists for modularity) ---
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        full_name VARCHAR(255) NOT NULL,
        role VARCHAR(32) NOT NULL DEFAULT 'customer',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    CREATE TABLE IF NOT EXISTS products (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        sku VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);

    CREATE TABLE IF NOT EXISTS plans (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        billing_interval VARCHAR(32) NOT NULL DEFAULT 'monthly',
        price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS subscriptions (
        id UUID PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
        status VARCHAR(32) NOT NULL DEFAULT 'active',
        current_period_start TIMESTAMPTZ NOT NULL,
        current_period_end TIMESTAMPTZ NOT NULL,
        next_billing_date TIMESTAMPTZ NOT NULL,
        auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_status_billing ON subscriptions(status, next_billing_date);

    CREATE TABLE IF NOT EXISTS subscription_items (
        id UUID PRIMARY KEY,
        subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
        product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit_price NUMERIC(12, 2) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_sub_items_sub_prod ON subscription_items(subscription_id, product_id);
    """)

    # --- Member 3 Owned Billing & Payments Tables ---

    # 1. discount_rules
    op.create_table(
        'discount_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(length=32), nullable=False),
        sa.Column('discount_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_purchase_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('min_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_usage_count', sa.Integer(), nullable=True),
        sa.Column('current_usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("discount_type IN ('percentage', 'fixed_amount')", name='ck_discount_type_valid'),
        sa.CheckConstraint('discount_value >= 0', name='ck_discount_value_positive'),
        sa.CheckConstraint("(discount_type != 'percentage') OR (discount_value <= 100)", name='ck_discount_percentage_range'),
        sa.CheckConstraint('min_purchase_amount >= 0', name='ck_min_purchase_amount_non_negative'),
        sa.CheckConstraint('min_quantity >= 1', name='ck_min_quantity_positive'),
        sa.CheckConstraint('max_usage_count IS NULL OR current_usage_count <= max_usage_count', name='ck_discount_usage_limit'),
    )
    op.create_index('idx_discount_code', 'discount_rules', ['code'], unique=True)
    op.create_index('idx_discount_active_dates', 'discount_rules', ['is_active', 'start_date', 'end_date'])

    # 2. tax_rules
    op.create_table(
        'tax_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('tax_rate >= 0 AND tax_rate <= 100', name='ck_tax_rate_range'),
    )
    op.create_index('idx_tax_rule_active_validity', 'tax_rules', ['is_active', 'valid_from', 'valid_until'])

    # 3. invoices
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_number', sa.String(length=64), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('subtotal_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('amount_due', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('customer_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('subscription_id', 'billing_period_start', 'billing_period_end', name='uq_subscription_billing_period'),
        sa.CheckConstraint("status IN ('draft', 'confirmed', 'paid', 'cancelled')", name='ck_invoice_status_valid'),
        sa.CheckConstraint('subtotal_amount >= 0', name='ck_invoice_subtotal_non_negative'),
        sa.CheckConstraint('discount_amount >= 0', name='ck_invoice_discount_non_negative'),
        sa.CheckConstraint('tax_amount >= 0', name='ck_invoice_tax_non_negative'),
        sa.CheckConstraint('total_amount >= 0', name='ck_invoice_total_non_negative'),
        sa.CheckConstraint('amount_paid >= 0', name='ck_invoice_amount_paid_non_negative'),
        sa.CheckConstraint('amount_due >= 0', name='ck_invoice_amount_due_non_negative'),
        sa.CheckConstraint('amount_paid <= total_amount', name='ck_invoice_no_overpayment'),
    )
    op.create_index('idx_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('idx_invoice_subscription', 'invoices', ['subscription_id'])
    op.create_index('idx_invoice_customer_status', 'invoices', ['customer_id', 'status'])

    # 4. invoice_items
    op.create_table(
        'invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('product_sku_snapshot', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_snapshot', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('quantity > 0', name='ck_invoice_item_quantity_positive'),
        sa.CheckConstraint('unit_price_snapshot >= 0', name='ck_invoice_item_unit_price_non_negative'),
        sa.CheckConstraint('subtotal >= 0', name='ck_invoice_item_subtotal_non_negative'),
        sa.CheckConstraint('discount_amount >= 0', name='ck_invoice_item_discount_non_negative'),
        sa.CheckConstraint('tax_amount >= 0', name='ck_invoice_item_tax_non_negative'),
        sa.CheckConstraint('total >= 0', name='ck_invoice_item_total_non_negative'),
    )
    op.create_index('idx_invoice_items_invoice', 'invoice_items', ['invoice_id'])

    # 5. invoice_tax_details
    op.create_table(
        'invoice_tax_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tax_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tax_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tax_name_snapshot', sa.String(length=100), nullable=False),
        sa.Column('tax_rate_snapshot', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('taxable_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('taxable_amount >= 0', name='ck_tax_detail_taxable_non_negative'),
        sa.CheckConstraint('tax_amount >= 0', name='ck_tax_detail_tax_amount_non_negative'),
    )
    op.create_index('idx_tax_details_invoice', 'invoice_tax_details', ['invoice_id'])

    # 6. invoice_discount_details
    op.create_table(
        'invoice_discount_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('discount_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discount_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('discount_code_snapshot', sa.String(length=50), nullable=False),
        sa.Column('discount_type_snapshot', sa.String(length=32), nullable=False),
        sa.Column('discount_value_snapshot', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('applied_discount_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('applied_discount_amount >= 0', name='ck_discount_detail_applied_amount_non_negative'),
    )
    op.create_index('idx_discount_details_invoice', 'invoice_discount_details', ['invoice_id'])

    # 7. payments
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='successful'),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('transaction_reference', sa.String(length=255), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('amount > 0', name='ck_payment_amount_positive'),
        sa.CheckConstraint("payment_method IN ('credit_card', 'bank_transfer', 'upi', 'cash')", name='ck_payment_method_valid'),
        sa.CheckConstraint("status IN ('pending', 'successful', 'failed', 'refunded')", name='ck_payment_status_valid'),
    )
    op.create_index('idx_payment_transaction_ref', 'payments', ['transaction_reference'], unique=True)
    op.create_index('idx_payment_idempotency', 'payments', ['idempotency_key'], unique=True)
    op.create_index('idx_payment_invoice_status', 'payments', ['invoice_id', 'status'])

    # 8. billing_runs
    op.create_table(
        'billing_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trigger_source', sa.String(length=64), nullable=False, server_default='manual_api'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='in_progress'),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('subscriptions_evaluated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invoices_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failures_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'failed', 'partially_failed')", name='ck_billing_run_status_valid'),
    )

    # 9. billing_attempts
    op.create_table(
        'billing_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('billing_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('successful', 'failed', 'skipped')", name='ck_billing_attempt_status_valid'),
    )
    op.create_index('idx_billing_attempt_sub_run', 'billing_attempts', ['subscription_id', 'billing_run_id'])


def downgrade() -> None:
    op.drop_table('billing_attempts')
    op.drop_table('billing_runs')
    op.drop_table('payments')
    op.drop_table('invoice_discount_details')
    op.drop_table('invoice_tax_details')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('tax_rules')
    op.drop_table('discount_rules')

