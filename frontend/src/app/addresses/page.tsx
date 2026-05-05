'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Package, Plus, Trash2, Edit } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

export default function AddressesPage() {
  const router = useRouter();
  const [addresses, setAddresses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    label: '',
    line1: '',
    line2: '',
    city: '',
    province: '',
    postal_code: '',
    country_code: 'ZA',
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadAddresses();
  }, [router]);

  const loadAddresses = async () => {
    try {
      const data = await api.addresses.list();
      setAddresses(data);
    } catch (err) {
      console.error('Failed to load addresses', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await api.addresses.create(formData);
      setFormData({
        label: '',
        line1: '',
        line2: '',
        city: '',
        province: '',
        postal_code: '',
        country_code: 'ZA',
      });
      setShowForm(false);
      loadAddresses();
    } catch (err: any) {
      setError(err.message || 'Failed to create address');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this address?')) return;

    try {
      await api.addresses.delete(id);
      loadAddresses();
    } catch (err: any) {
      setError(err.message || 'Failed to delete address');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">My Addresses</h1>
          <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
            <Plus className="h-4 w-4 inline mr-2" />
            Add Address
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {showForm && (
          <form onSubmit={handleSubmit} className="card mb-8">
            <h2 className="text-xl font-semibold mb-4">New Address</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Label (optional)</label>
                <input
                  type="text"
                  value={formData.label}
                  onChange={(e) => setFormData({ ...formData, label: e.target.value })}
                  className="input"
                  placeholder="Home, Office, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Address Line 1</label>
                <input
                  type="text"
                  required
                  value={formData.line1}
                  onChange={(e) => setFormData({ ...formData, line1: e.target.value })}
                  className="input"
                  placeholder="123 Main Street"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Address Line 2 (optional)</label>
                <input
                  type="text"
                  value={formData.line2}
                  onChange={(e) => setFormData({ ...formData, line2: e.target.value })}
                  className="input"
                  placeholder="Apartment, suite, etc."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">City</label>
                  <input
                    type="text"
                    required
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="input"
                    placeholder="Cape Town"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Province (optional)</label>
                  <input
                    type="text"
                    value={formData.province}
                    onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                    className="input"
                    placeholder="Western Cape"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Postal Code</label>
                  <input
                    type="text"
                    required
                    value={formData.postal_code}
                    onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                    className="input"
                    placeholder="8001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Country</label>
                  <select
                    value={formData.country_code}
                    onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                    className="input"
                  >
                    <option value="ZA">South Africa</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-4">
                <button type="submit" className="btn btn-primary">
                  Save Address
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        )}

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : addresses.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600 mb-4">No addresses yet</p>
            <button onClick={() => setShowForm(true)} className="btn btn-primary">
              Add Your First Address
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {addresses.map((address) => (
              <div key={address.id} className="card">
                <div className="flex justify-between items-start">
                  <div>
                    {address.label && (
                      <h3 className="text-lg font-semibold mb-2">{address.label}</h3>
                    )}
                    <p className="text-gray-700">{address.line1}</p>
                    {address.line2 && <p className="text-gray-700">{address.line2}</p>}
                    <p className="text-gray-700">
                      {address.city}
                      {address.province && `, ${address.province}`}
                    </p>
                    <p className="text-gray-700">{address.postal_code}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(address.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
