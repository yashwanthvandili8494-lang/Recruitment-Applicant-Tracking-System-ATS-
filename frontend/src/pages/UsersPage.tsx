/**
 * Admin user management page.
 */

import { useState, useEffect } from 'react';
import api from '../services/api';
import type { User, UserListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import { Shield, Plus, Search, Loader2, UserPlus, ToggleLeft, ToggleRight } from 'lucide-react';
import toast from 'react-hot-toast';

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'recruiter' });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page_size: '100' });
      if (search) params.append('search', search);
      const { data } = await api.get<UserListResponse>(`/users?${params}`);
      setUsers(data.users);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, [search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/users', form);
      toast.success('User created');
      setShowCreate(false);
      setForm({ name: '', email: '', password: '', role: 'recruiter' });
      fetchUsers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const toggleActive = async (userId: string, isActive: boolean) => {
    try {
      await api.patch(`/users/${userId}`, { is_active: !isActive });
      toast.success(isActive ? 'User deactivated' : 'User activated');
      fetchUsers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const roleColors: Record<string, string> = {
    admin: 'bg-red-50 text-red-700',
    recruiter: 'bg-blue-50 text-blue-700',
    hiring_manager: 'bg-purple-50 text-purple-700',
    interviewer: 'bg-cyan-50 text-cyan-700',
    candidate: 'bg-green-50 text-green-700',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">User Management</h1>
          <p className="text-surface-500 mt-1">{users.length} users</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <UserPlus className="w-4 h-4" /> Add User
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-10"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-surface-50 border-b border-surface-100">
              <tr>
                <th className="table-header">User</th>
                <th className="table-header">Role</th>
                <th className="table-header">Status</th>
                <th className="table-header">Joined</th>
                <th className="table-header w-16">Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-surface-50/50">
                  <td className="table-cell">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 gradient-primary rounded-full flex items-center justify-center text-white text-xs font-bold">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-surface-900">{user.name}</p>
                        <p className="text-xs text-surface-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className={`status-badge text-xs px-2.5 py-0.5 ${roleColors[user.role] || 'bg-gray-50 text-gray-700'}`}>
                      {user.role.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </span>
                  </td>
                  <td className="table-cell">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${user.is_active ? 'text-green-600' : 'text-surface-400'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-surface-300'}`} />
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="table-cell text-xs text-surface-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="table-cell">
                    <button
                      onClick={() => toggleActive(user.id, user.is_active)}
                      className={`p-1 rounded-lg transition-colors ${user.is_active ? 'text-green-600 hover:bg-green-50' : 'text-surface-400 hover:bg-surface-100'}`}
                    >
                      {user.is_active ? <ToggleRight className="w-6 h-6" /> : <ToggleLeft className="w-6 h-6" />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 animate-fade-in">
            <h3 className="text-lg font-semibold text-surface-900 mb-4">Create Staff User</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="label-text">Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" required />
              </div>
              <div>
                <label className="label-text">Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-field" required />
              </div>
              <div>
                <label className="label-text">Password</label>
                <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input-field" required minLength={8} />
              </div>
              <div>
                <label className="label-text">Role</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="input-field">
                  <option value="recruiter">Recruiter</option>
                  <option value="hiring_manager">Hiring Manager</option>
                  <option value="interviewer">Interviewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Create User</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
