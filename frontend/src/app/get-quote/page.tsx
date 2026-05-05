'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Package, ArrowLeft, ArrowRight, Check, Clock, Shield, Truck } from 'lucide-react';
import { api } from '@/lib/api';

/**
 * Guest 4-step quote & booking wizard.
 * Steps:
 *  1. Parcel details
 *  2. Pickup + delivery addresses
 *  3. Compare courier rates
 *  4. Review + customer contact + checkout
 */

type AddressForm = {
  line1: string;
  line2: string;
  suburb: string;
  city: string;
  province: string;
  postal_code: string;
  country_code: string;
  type: string;
};

const emptyAddress: AddressForm = {
  line1: '',
  line2: '',
  suburb: '',
  city: '',
  province: 'Gauteng',
  postal_code: '',
  country_code: 'ZA',
  type: 'residential',
};

const SA_PROVINCES = [
  'Gauteng',
  'Western Cape',
  'KwaZulu-Natal',
  'Eastern Cape',
  'Free State',
  'Limpopo',
  'Mpumalanga',
  'North West',
  'Northern Cape',
];

type Parcel = {
  weight_kg: string;
  length_cm: string;
  width_cm: string;
  height_cm: string;
  value_zar: string;
  description: string;
};

const emptyParcel: Parcel = {
  weight_kg: '',
  length_cm: '',
  width_cm: '',
  height_cm: '',
  value_zar: '',
  description: '',
};

type Urgency = 'same_day' | 'overnight' | 'economy' | '';

const STEPS = ['Parcel', 'Addresses', 'Rates', 'Review'] as const;

function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="flex items-center justify-between mb-8">
      {STEPS.map((step, i) => {
        const n = i + 1;
        const done = n < current;
        const active = n === current;
        return (
          <li key={step} className="flex-1 flex items-center">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 font-semibold
                ${done ? 'bg-primary-600 border-primary-600 text-white' : ''}
                ${active ? 'border-primary-600 text-primary-600 bg-white' : ''}
                ${!done && !active ? 'border-gray-300 text-gray-400 bg-white' : ''}`}
            >
              {done ? <Check className="h-5 w-5" /> : n}
            </div>
            <span className={`ml-3 text-sm ${active ? 'font-semibold text-gray-900' : 'text-gray-500'}`}>
              {step}
            </span>
            {i < STEPS.length - 1 && <div className="flex-1 h-px bg-gray-300 mx-4" />}
          </li>
        );
      })}
    </ol>
  );
}

function AddressFields({
  value,
  onChange,
  prefix,
}: {
  value: AddressForm;
  onChange: (v: AddressForm) => void;
  prefix: string;
}) {
  const set = (k: keyof AddressForm) => (e: any) => onChange({ ...value, [k]: e.target.value });
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="md:col-span-2">
        <label className="block text-sm font-medium mb-2">Street address</label>
        <input required value={value.line1} onChange={set('line1')} className="input" placeholder={`${prefix} street address`} />
      </div>
      <div>
        <label className="block text-sm font-medium mb-2">Suburb</label>
        <input value={value.suburb} onChange={set('suburb')} className="input" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-2">City</label>
        <input required value={value.city} onChange={set('city')} className="input" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-2">Province</label>
        <select value={value.province} onChange={set('province')} className="input">
          {SA_PROVINCES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium mb-2">Postal code</label>
        <input required value={value.postal_code} onChange={set('postal_code')} className="input" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-2">Address type</label>
        <select value={value.type} onChange={set('type')} className="input">
          <option value="residential">Residential</option>
          <option value="business">Business</option>
        </select>
      </div>
    </div>
  );
}

function fmtR(cents: number | string) {
  const n = typeof cents === 'number' ? cents : parseFloat(cents);
  return `R ${(n / 100).toFixed(2)}`;
}

export default function GetQuotePage() {
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [parcel, setParcel] = useState<Parcel>(emptyParcel);
  const [urgency, setUrgency] = useState<Urgency>('');
  const [pickup, setPickup] = useState<AddressForm>(emptyAddress);
  const [delivery, setDelivery] = useState<AddressForm>(emptyAddress);

  const [quote, setQuote] = useState<any>(null); // server quote with results + access_token
  const [selectedRate, setSelectedRate] = useState<any>(null);

  const [customer, setCustomer] = useState({ email: '', phone: '', consent: false });

  const goto = (n: number) => {
    setError('');
    setStep(n);
  };

  const submitQuote = async () => {
    setError('');
    setLoading(true);
    try {
      const payload = {
        pickup,
        delivery,
        parcel: {
          weight_kg: parseFloat(parcel.weight_kg),
          length_cm: parseFloat(parcel.length_cm),
          width_cm: parseFloat(parcel.width_cm),
          height_cm: parseFloat(parcel.height_cm),
          value_zar: parcel.value_zar ? parseFloat(parcel.value_zar) : null,
          description: parcel.description || null,
        },
        urgency: urgency || null,
        email: null,
        consent: false,
      };
      const result = await api.quotes.createGuest(payload);
      setQuote(result);
      setStep(3);
    } catch (e: any) {
      setError(e.message || 'Could not get rates');
    } finally {
      setLoading(false);
    }
  };

  const submitBooking = async () => {
    if (!selectedRate) return;
    setError('');
    setLoading(true);
    try {
      const idempotencyKey = crypto.randomUUID();
      const booking = await api.bookings.createGuest(
        {
          quote_token: quote.access_token,
          courier_id: selectedRate.courier_id,
          courier_service_level: selectedRate.service_level,
          email: customer.email,
          phone: customer.phone || null,
        },
        idempotencyKey
      );
      // Kick off PayFast
      const payment = await api.bookings.initiatePaymentGuest(booking.access_token);
      // Stash booking access token so /track can fetch status post-payment
      if (typeof window !== 'undefined') {
        localStorage.setItem(`bt:${booking.public_short_code}`, booking.access_token);
      }
      // Build POST form + submit to PayFast
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = payment.action_url;
      Object.entries(payment.fields || {}).forEach(([k, v]) => {
        const i = document.createElement('input');
        i.type = 'hidden';
        i.name = k;
        i.value = String(v);
        form.appendChild(i);
      });
      document.body.appendChild(form);
      form.submit();
    } catch (e: any) {
      setError(e.message || 'Booking failed');
      setLoading(false);
    }
  };

  // --- Step renderers ----------------------------------------------------

  const parcelValid =
    Number(parcel.weight_kg) > 0 &&
    Number(parcel.length_cm) > 0 &&
    Number(parcel.width_cm) > 0 &&
    Number(parcel.height_cm) > 0;
  const pickupValid = pickup.line1 && pickup.city && pickup.postal_code;
  const deliveryValid = delivery.line1 && delivery.city && delivery.postal_code;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2">
            <Package className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
          </Link>
          <Link href="/login" className="text-sm text-gray-600 hover:text-primary-600">
            Have an account? Sign in
          </Link>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-2">Get a shipping quote</h1>
        <p className="text-gray-600 mb-6">
          No sign-up needed. We&apos;ll compare rates across couriers and email you the tracking link.
        </p>

        <StepIndicator current={step} />

        {error && (
          <div className="card mb-4 bg-red-50 border border-red-200 text-red-800">{error}</div>
        )}

        {/* Step 1 — Parcel */}
        {step === 1 && (
          <div className="card space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-4">What are you sending?</h2>
              <input
                value={parcel.description}
                onChange={(e) => setParcel({ ...parcel, description: e.target.value })}
                className="input mb-4"
                placeholder="Short description (e.g. Laptop, documents)"
              />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Weight (kg)</label>
                  <input type="number" step="0.1" min="0.1" value={parcel.weight_kg}
                    onChange={(e) => setParcel({ ...parcel, weight_kg: e.target.value })}
                    className="input" placeholder="5.0" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Length (cm)</label>
                  <input type="number" step="0.1" min="1" value={parcel.length_cm}
                    onChange={(e) => setParcel({ ...parcel, length_cm: e.target.value })}
                    className="input" placeholder="30" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Width (cm)</label>
                  <input type="number" step="0.1" min="1" value={parcel.width_cm}
                    onChange={(e) => setParcel({ ...parcel, width_cm: e.target.value })}
                    className="input" placeholder="20" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Height (cm)</label>
                  <input type="number" step="0.1" min="1" value={parcel.height_cm}
                    onChange={(e) => setParcel({ ...parcel, height_cm: e.target.value })}
                    className="input" placeholder="10" />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium mb-2">Declared value (ZAR, optional)</label>
                <input type="number" step="0.01" min="0" value={parcel.value_zar}
                  onChange={(e) => setParcel({ ...parcel, value_zar: e.target.value })}
                  className="input max-w-xs" placeholder="For insurance cover" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Urgency (optional)</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { v: 'same_day', label: 'Same day', Icon: Clock },
                  { v: 'overnight', label: 'Overnight', Icon: Truck },
                  { v: 'economy', label: 'Economy', Icon: Shield },
                ].map(({ v, label, Icon }) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setUrgency(urgency === v ? '' : (v as Urgency))}
                    className={`p-4 rounded-lg border-2 text-left transition ${
                      urgency === v
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-5 w-5 text-primary-600 mb-2" />
                    <div className="font-medium">{label}</div>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-end">
              <button disabled={!parcelValid} onClick={() => goto(2)} className="btn btn-primary">
                Continue <ArrowRight className="h-4 w-4 ml-1 inline" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Addresses */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Pickup address</h2>
              <AddressFields value={pickup} onChange={setPickup} prefix="Pickup" />
            </div>
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Delivery address</h2>
              <AddressFields value={delivery} onChange={setDelivery} prefix="Delivery" />
            </div>
            <div className="flex justify-between">
              <button onClick={() => goto(1)} className="btn bg-gray-100 hover:bg-gray-200">
                <ArrowLeft className="h-4 w-4 mr-1 inline" /> Back
              </button>
              <button
                disabled={!pickupValid || !deliveryValid || loading}
                onClick={submitQuote}
                className="btn btn-primary"
              >
                {loading ? 'Comparing couriers…' : 'Compare rates'}{' '}
                <ArrowRight className="h-4 w-4 ml-1 inline" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — Rates */}
        {step === 3 && quote && (
          <div className="space-y-4">
            {(!quote.results?.quotes || quote.results.quotes.length === 0) && (
              <div className="card text-center py-12 text-gray-500">
                No couriers matched. Try different dimensions or postal codes.
              </div>
            )}
            {quote.results?.quotes?.map((q: any, idx: number) => (
              <button
                key={idx}
                onClick={() => setSelectedRate(q)}
                className={`card w-full text-left transition ${
                  selectedRate === q ? 'border-primary-600 ring-2 ring-primary-200' : 'hover:shadow-md'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-lg font-semibold">{q.courier_name}</div>
                    <div className="text-sm text-gray-600">
                      {q.service_level_display || q.service_level} • {q.estimated_delivery_days}{' '}
                      {q.estimated_delivery_days === 1 ? 'day' : 'days'}
                    </div>
                    {q.reliability_score != null && (
                      <div className="text-xs text-gray-500 mt-1">
                        Reliability: {(q.reliability_score * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary-600">{fmtR(q.price_total)}</div>
                    <div className="text-xs text-gray-500">incl. VAT</div>
                  </div>
                </div>
              </button>
            ))}
            <div className="flex justify-between">
              <button onClick={() => goto(2)} className="btn bg-gray-100 hover:bg-gray-200">
                <ArrowLeft className="h-4 w-4 mr-1 inline" /> Back
              </button>
              <button disabled={!selectedRate} onClick={() => goto(4)} className="btn btn-primary">
                Continue <ArrowRight className="h-4 w-4 ml-1 inline" />
              </button>
            </div>
          </div>
        )}

        {/* Step 4 — Review + contact */}
        {step === 4 && selectedRate && (
          <div className="space-y-4">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Order summary</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Courier</div>
                  <div className="font-medium">{selectedRate.courier_name}</div>
                </div>
                <div>
                  <div className="text-gray-500">Service</div>
                  <div className="font-medium">{selectedRate.service_level_display || selectedRate.service_level}</div>
                </div>
                <div>
                  <div className="text-gray-500">From</div>
                  <div className="font-medium">{pickup.city}, {pickup.postal_code}</div>
                </div>
                <div>
                  <div className="text-gray-500">To</div>
                  <div className="font-medium">{delivery.city}, {delivery.postal_code}</div>
                </div>
                <div>
                  <div className="text-gray-500">Parcel</div>
                  <div className="font-medium">
                    {parcel.weight_kg} kg, {parcel.length_cm}×{parcel.width_cm}×{parcel.height_cm} cm
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Delivery</div>
                  <div className="font-medium">
                    {selectedRate.estimated_delivery_days}{' '}
                    {selectedRate.estimated_delivery_days === 1 ? 'day' : 'days'}
                  </div>
                </div>
              </div>
              <div className="mt-6 border-t pt-4 flex justify-between items-center">
                <div className="text-lg">Total</div>
                <div className="text-3xl font-bold text-primary-600">{fmtR(selectedRate.price_total)}</div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Your contact details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Email *</label>
                  <input
                    type="email"
                    required
                    value={customer.email}
                    onChange={(e) => setCustomer({ ...customer, email: e.target.value })}
                    className="input"
                    placeholder="you@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Mobile (optional)</label>
                  <input
                    value={customer.phone}
                    onChange={(e) => setCustomer({ ...customer, phone: e.target.value })}
                    className="input"
                    placeholder="+27 ..."
                  />
                </div>
              </div>
              <label className="mt-4 flex items-start gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={customer.consent}
                  onChange={(e) => setCustomer({ ...customer, consent: e.target.checked })}
                  className="mt-1"
                />
                <span>
                  I agree to SEND-IT processing my details under its Privacy Policy (POPIA) to provide
                  this quote and shipment.
                </span>
              </label>
            </div>

            <div className="flex justify-between">
              <button onClick={() => goto(3)} className="btn bg-gray-100 hover:bg-gray-200">
                <ArrowLeft className="h-4 w-4 mr-1 inline" /> Back
              </button>
              <button
                disabled={!customer.email || !customer.consent || loading}
                onClick={submitBooking}
                className="btn btn-primary"
              >
                {loading ? 'Redirecting to PayFast…' : 'Pay & book'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
