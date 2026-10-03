import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from '../components/StatusBadge';

describe('StatusBadge', () => {
  it('renders standard application status correctly', () => {
    render(<StatusBadge status="applied" />);
    expect(screen.getByText('Applied')).toBeInTheDocument();
  });

  it('renders shortlisted status with proper styles', () => {
    render(<StatusBadge status="shortlisted" />);
    const badge = screen.getByText('Shortlisted');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('text-indigo-700');
  });

  it('renders offer statuses correctly', () => {
    render(<StatusBadge status="pending_approval" />);
    expect(screen.getByText('Pending Approval')).toBeInTheDocument();
  });

  it('formats unknown status by replacing underscores and capitalizing', () => {
    render(<StatusBadge status="custom_new_state" />);
    expect(screen.getByText('Custom New State')).toBeInTheDocument();
  });

  it('supports size variants', () => {
    const { rerender } = render(<StatusBadge status="hired" size="sm" />);
    let badge = screen.getByText('Hired');
    expect(badge.className).toContain('text-xs');

    rerender(<StatusBadge status="hired" size="md" />);
    badge = screen.getByText('Hired');
    expect(badge.className).toContain('text-sm');
  });
});
