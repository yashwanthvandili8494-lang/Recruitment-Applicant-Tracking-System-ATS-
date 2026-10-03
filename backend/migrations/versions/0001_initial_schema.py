"""Initial schema for RecruitFlow ATS — all 13 core tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_org_role', 'users', ['organization_id', 'role'], unique=False)

    # 3. candidate_profiles
    op.create_table(
        'candidate_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('education', sa.JSON(), nullable=True),
        sa.Column('portfolio_url', sa.String(length=500), nullable=True),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # 4. jobs
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('preferred_skills', sa.Text(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=False),
        sa.Column('work_mode', sa.String(length=50), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('experience_min', sa.Integer(), nullable=True),
        sa.Column('experience_max', sa.Integer(), nullable=True),
        sa.Column('salary_min', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('salary_max', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('openings', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('hiring_manager_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['hiring_manager_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_jobs_org_status', 'jobs', ['organization_id', 'status'], unique=False)
    op.create_index('ix_jobs_department', 'jobs', ['department'], unique=False)
    op.create_index('ix_jobs_deadline', 'jobs', ['deadline'], unique=False)

    # 5. resumes
    op.create_table(
        'resumes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resumes_candidate', 'resumes', ['candidate_id'], unique=False)

    # 6. applications
    op.create_table(
        'applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('resume_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'candidate_id', name='uq_application_job_candidate'),
    )
    op.create_index('ix_applications_candidate', 'applications', ['candidate_id'], unique=False)
    op.create_index('ix_applications_job', 'applications', ['job_id'], unique=False)
    op.create_index('ix_applications_status', 'applications', ['status'], unique=False)

    # 7. application_status_history
    op.create_table(
        'application_status_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=36), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_status_history_application', 'application_status_history', ['application_id'], unique=False)

    # 8. interviews
    op.create_table(
        'interviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('interview_round', sa.Integer(), nullable=False),
        sa.Column('interview_type', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('meeting_location', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interviews_application', 'interviews', ['application_id'], unique=False)
    op.create_index('ix_interviews_time', 'interviews', ['start_time', 'end_time'], unique=False)

    # 9. interview_participants
    op.create_table(
        'interview_participants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('interview_id', 'user_id', name='uq_interview_user'),
    )

    # 10. interview_feedbacks
    op.create_table(
        'interview_feedbacks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('interviewer_id', sa.String(length=36), nullable=False),
        sa.Column('criterion_scores', sa.JSON(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('concerns', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.String(length=50), nullable=False),
        sa.Column('overall_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('interview_id', 'interviewer_id', name='uq_interview_feedback_user'),
    )

    # 11. offers
    op.create_table(
        'offers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('compensation_details', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('issued_by', sa.String(length=36), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('candidate_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['issued_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_offers_application', 'offers', ['application_id'], unique=False)
    op.create_index('ix_offers_status', 'offers', ['status'], unique=False)

    # 12. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_status', 'notifications', ['user_id', 'status'], unique=False)

    # 13. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_org_created', 'audit_logs', ['organization_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_user', 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('offers')
    op.drop_table('interview_feedbacks')
    op.drop_table('interview_participants')
    op.drop_table('interviews')
    op.drop_table('application_status_history')
    op.drop_table('applications')
    op.drop_table('resumes')
    op.drop_table('jobs')
    op.drop_table('candidate_profiles')
    op.drop_table('users')
    op.drop_table('organizations')
