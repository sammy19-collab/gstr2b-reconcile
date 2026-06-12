"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'USER');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE uploadtype AS ENUM ('PURCHASE_REGISTER', 'GSTR2B');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE uploadstatus AS ENUM ('PENDING', 'PROCESSING', 'READY', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE runstatus AS ENUM ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE matchcategory AS ENUM (
                'EXACT_MATCH', 'FUZZY_MATCH', 'TAX_MISMATCH',
                'INVOICE_MISMATCH', 'DATE_MISMATCH',
                'MISSING_IN_2B', 'MISSING_IN_BOOKS', 'DUPLICATE'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            role userrole NOT NULL DEFAULT 'USER',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);")

    # Clients table
    op.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR(255) NOT NULL,
            gstin CHAR(15) NOT NULL,
            pan VARCHAR(10),
            contact_email VARCHAR(255),
            contact_phone VARCHAR(20),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_clients_id ON clients (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clients_owner_id ON clients (owner_id);")

    # Uploads table
    op.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id),
            uploader_id INTEGER NOT NULL REFERENCES users(id),
            upload_type uploadtype NOT NULL,
            filename VARCHAR(255) NOT NULL,
            filepath VARCHAR(512) NOT NULL,
            file_size INTEGER NOT NULL,
            row_count INTEGER,
            period VARCHAR(6),
            status uploadstatus NOT NULL DEFAULT 'PENDING',
            error_message VARCHAR(1024),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_uploads_id ON uploads (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_uploads_client_id ON uploads (client_id);")

    # Column mappings table
    op.execute("""
        CREATE TABLE IF NOT EXISTS column_mappings (
            id SERIAL PRIMARY KEY,
            upload_id INTEGER NOT NULL UNIQUE REFERENCES uploads(id),
            mapping JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_column_mappings_id ON column_mappings (id);")

    # Reconciliation runs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_runs (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id),
            initiated_by INTEGER NOT NULL REFERENCES users(id),
            period VARCHAR(6) NOT NULL,
            pr_upload_id INTEGER NOT NULL REFERENCES uploads(id),
            g2b_upload_id INTEGER NOT NULL REFERENCES uploads(id),
            tax_tolerance NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
            fuzzy_threshold INTEGER NOT NULL DEFAULT 80,
            status runstatus NOT NULL DEFAULT 'QUEUED',
            summary JSONB,
            error_message VARCHAR(1024),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_reconciliation_runs_id ON reconciliation_runs (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reconciliation_runs_client_id ON reconciliation_runs (client_id);")

    # Purchase invoices table
    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_invoices (
            id SERIAL PRIMARY KEY,
            upload_id INTEGER NOT NULL REFERENCES uploads(id),
            run_id INTEGER REFERENCES reconciliation_runs(id),
            invoice_number VARCHAR(100) NOT NULL,
            invoice_date DATE,
            supplier_gstin VARCHAR(15),
            supplier_name VARCHAR(255),
            taxable_amount NUMERIC(15, 2),
            igst NUMERIC(15, 2) DEFAULT 0,
            cgst NUMERIC(15, 2) DEFAULT 0,
            sgst NUMERIC(15, 2) DEFAULT 0,
            total_tax NUMERIC(15, 2),
            invoice_type VARCHAR(20),
            place_of_supply VARCHAR(5),
            reverse_charge VARCHAR(1),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_invoices_id ON purchase_invoices (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_invoices_upload_id ON purchase_invoices (upload_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_purchase_invoices_gstin_inv ON purchase_invoices (supplier_gstin, invoice_number);")

    # GSTR-2B invoices table
    op.execute("""
        CREATE TABLE IF NOT EXISTS gstr2b_invoices (
            id SERIAL PRIMARY KEY,
            upload_id INTEGER NOT NULL REFERENCES uploads(id),
            run_id INTEGER REFERENCES reconciliation_runs(id),
            invoice_number VARCHAR(100) NOT NULL,
            invoice_date DATE,
            supplier_gstin VARCHAR(15),
            supplier_name VARCHAR(255),
            taxable_amount NUMERIC(15, 2),
            igst NUMERIC(15, 2) DEFAULT 0,
            cgst NUMERIC(15, 2) DEFAULT 0,
            sgst NUMERIC(15, 2) DEFAULT 0,
            total_tax NUMERIC(15, 2),
            invoice_type VARCHAR(20),
            place_of_supply VARCHAR(5),
            itc_availability VARCHAR(10),
            reason VARCHAR(100),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_gstr2b_invoices_id ON gstr2b_invoices (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gstr2b_invoices_upload_id ON gstr2b_invoices (upload_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gstr2b_invoices_gstin_inv ON gstr2b_invoices (supplier_gstin, invoice_number);")

    # Reconciliation results table
    op.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_results (
            id SERIAL PRIMARY KEY,
            run_id INTEGER NOT NULL REFERENCES reconciliation_runs(id),
            category matchcategory NOT NULL,
            confidence NUMERIC(5, 2),
            purchase_invoice_id INTEGER REFERENCES purchase_invoices(id),
            gstr2b_invoice_id INTEGER REFERENCES gstr2b_invoices(id),
            purchase_data JSONB,
            gstr2b_data JSONB,
            tax_delta NUMERIC(15, 2),
            date_delta_days INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_reconciliation_results_id ON reconciliation_results (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reconciliation_results_run_id ON reconciliation_results (run_id);")

    # Vendor analytics table
    op.execute("""
        CREATE TABLE IF NOT EXISTS vendor_analytics (
            id SERIAL PRIMARY KEY,
            run_id INTEGER NOT NULL REFERENCES reconciliation_runs(id),
            supplier_gstin VARCHAR(15),
            supplier_name VARCHAR(255),
            total_invoices INTEGER NOT NULL DEFAULT 0,
            matched INTEGER NOT NULL DEFAULT 0,
            missing_in_2b INTEGER NOT NULL DEFAULT 0,
            missing_in_books INTEGER NOT NULL DEFAULT 0,
            tax_mismatch INTEGER NOT NULL DEFAULT 0,
            itc_available NUMERIC(15, 2) NOT NULL DEFAULT 0,
            itc_at_risk NUMERIC(15, 2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_analytics_id ON vendor_analytics (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_analytics_run_id ON vendor_analytics (run_id);")

    # Audit logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            resource_id INTEGER,
            details JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs (id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs;")
    op.execute("DROP TABLE IF EXISTS vendor_analytics;")
    op.execute("DROP TABLE IF EXISTS reconciliation_results;")
    op.execute("DROP TABLE IF EXISTS gstr2b_invoices;")
    op.execute("DROP TABLE IF EXISTS purchase_invoices;")
    op.execute("DROP TABLE IF EXISTS reconciliation_runs;")
    op.execute("DROP TABLE IF EXISTS column_mappings;")
    op.execute("DROP TABLE IF EXISTS uploads;")
    op.execute("DROP TABLE IF EXISTS clients;")
    op.execute("DROP TABLE IF EXISTS users;")
    op.execute("DROP TYPE IF EXISTS matchcategory;")
    op.execute("DROP TYPE IF EXISTS runstatus;")
    op.execute("DROP TYPE IF EXISTS uploadstatus;")
    op.execute("DROP TYPE IF EXISTS uploadtype;")
    op.execute("DROP TYPE IF EXISTS userrole;")
