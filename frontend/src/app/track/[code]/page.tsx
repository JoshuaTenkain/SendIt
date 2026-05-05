'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Package, CheckCircle2, Truck, Clock, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

/**
 * Public tracking page — accessible by the 12-char short code printed on the
 * waybill / receipt. No auth required, no PII displayed.
 */

function StatusIcon({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s.includes('deliver')) return <CheckCircle2 className="h-5 w-5 text-green-600" />;
  if (s.includes('transit') || s.includes('collect') || s.includes('hub')) return <Truck className="h-5 w-5 text-primary-600" />;
  if (s.includes('fail') || s.includes('cancel')) return <AlertCircle className="h-5 w-5 text-red-600" />;
  return <Clock className="h-5 w-5 text-gray-400" />;
}

export default function PublicTrackPage({ params }: { params: { code: string } }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const result = await api.tracking.public(params.code);
        if (mounted) {
          setData(result);
          setError('');
        }
      } catch (e: any) {
        if (mounted) setError(e.message || 'Not found');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const iv = setInterval(load, 30000);
    return () => {
      mounted = false;
      clearInterval(iv);
    };
  }, [params.code]);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <Link href="/" className="flex items-center gap-2">
            <Package className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
          </Link>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Track shipment</h1>
          <p className="text-gray-500 mt-1">
            Reference <span className="font-mono font-semibold">{params.code}</span>
          </p>
        </div>

        {loading && <div className="card">Loading…</div>}
        {error && !loading && (
          <div className="card bg-red-50 border border-red-200 text-red-800">{error}</div>
        )}

        {data && (
          <>
            <div className="card mb-6">
              <div className="flex justify-between items-start flex-wrap gap-4">
                <div>
                  <div className="text-sm text-gray-500">Current status</div>
                  <div className="text-2xl font-semibold capitalize mt-1">
                    {data.status.replace(/_/g, ' ')}
                  </div>
                  {data.tracking_reference && (
                    <div className="text-xs text-gray-500 mt-1">
                      Waybill: {data.tracking_reference}
                    </div>
                  )}
                </div>
                {data.service_level && (
                  <span className="px-3 py-1 rounded-full bg-primary-50 text-primary-700 text-sm">
                    {data.service_level}
                  </span>
                )}
              </div>
            </div>

            <h2 className="text-lg font-semibold mb-4">History</h2>
            {data.events.length === 0 ? (
              <div className="card text-gray-500">
                No tracking events yet. Check back in a few minutes.
              </div>
            ) : (
              <ol className="space-y-3">
                {data.events.map((ev: any, idx: number) => (
                  <li key={idx} className="card flex gap-4">
                    <StatusIcon status={ev.status} />
                    <div className="flex-1">
                      <div className="flex justify-between flex-wrap gap-2">
                        <div className="font-medium capitalize">
                          {ev.status.replace(/-/g, ' ')}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(ev.occurred_at).toLocaleString()}
                        </div>
                      </div>
                      {ev.description && (
                        <div className="text-sm text-gray-600 mt-1">{ev.description}</div>
                      )}
                      {ev.location && (
                        <div className="text-xs text-gray-500 mt-1">{ev.location}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
      </main>
    </div>
  );
}
