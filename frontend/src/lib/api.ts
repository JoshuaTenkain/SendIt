const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  auth: {
    signup: (data: { email: string; password: string; first_name?: string; last_name?: string }) =>
      fetchApi('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      fetchApi('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  },
  addresses: {
    list: () => fetchApi('/addresses'),
    create: (data: any) => fetchApi('/addresses', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: any) =>
      fetchApi(`/addresses/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: string) => fetchApi(`/addresses/${id}`, { method: 'DELETE' }),
  },
  quotes: {
    create: (data: any) => fetchApi('/quotes', { method: 'POST', body: JSON.stringify(data) }),
    createGuest: (data: any) =>
      fetchApi('/quotes/guest', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) => fetchApi(`/quotes/${id}`),
    getByToken: (token: string) => fetchApi(`/quotes/by-token/${token}`),
    email: (id: string, email: string) =>
      fetchApi(`/quotes/${id}/email`, {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
  },
  bookings: {
    create: (data: any, idempotencyKey: string) =>
      fetchApi('/bookings', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Idempotency-Key': idempotencyKey },
      }),
    createGuest: (data: any, idempotencyKey: string) =>
      fetchApi('/bookings/guest', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Idempotency-Key': idempotencyKey },
      }),
    list: () => fetchApi('/bookings'),
    get: (id: string) => fetchApi(`/bookings/${id}`),
    getByToken: (token: string) => fetchApi(`/bookings/by-token/${token}`),
    initiatePayment: (id: string) => fetchApi(`/bookings/${id}/payment`, { method: 'POST' }),
    initiatePaymentGuest: (token: string) =>
      fetchApi(`/bookings/guest/${token}/payment`, { method: 'POST' }),
    cancel: (id: string, reason?: string) =>
      fetchApi(`/bookings/${id}/cancel`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
  },
  tracking: {
    get: (bookingId: string) => fetchApi(`/tracking/${bookingId}`),
    public: (shortCode: string) => fetchApi(`/tracking/public/${shortCode}`),
  },
  admin: {
    getCouriers: () => fetchApi('/admin/couriers'),
    updateCourier: (id: string, data: any) =>
      fetchApi(`/admin/couriers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    getBookings: () => fetchApi('/admin/bookings'),
    getTransactions: () => fetchApi('/admin/transactions'),
    getRevenue: () => fetchApi('/admin/revenue'),
  },
};
