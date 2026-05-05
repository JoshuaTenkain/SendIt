# SEND-IT User Guide

## Welcome to SEND-IT

SEND-IT is a courier aggregation platform that helps you compare shipping quotes from multiple courier services, book shipments, and track your parcels - all in one place.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Addresses](#managing-addresses)
3. [Getting Quotes](#getting-quotes)
4. [Booking Shipments](#booking-shipments)
5. [Making Payments](#making-payments)
6. [Tracking Shipments](#tracking-shipments)
7. [Admin Portal](#admin-portal)
8. [FAQs](#faqs)
9. [Support](#support)

---

## Getting Started

### Creating an Account

1. Navigate to http://localhost:3000 (or your deployment URL)
2. Click **"Sign Up"**
3. Fill in your details:
   - Email address
   - Password (minimum 8 characters)
   - First name (optional)
   - Last name (optional)
   - Phone number (optional)
4. Click **"Create Account"**
5. You'll be automatically logged in and redirected to your dashboard

### Logging In

1. Go to the login page
2. Enter your email and password
3. Click **"Login"**
4. You'll be redirected to your dashboard

### Dashboard Overview

Your dashboard shows:
- **All your bookings** with status badges
- **Quick actions:**
  - Create new quote
  - Manage addresses
  - Logout
- **Booking cards** displaying:
  - Booking ID
  - Status (pending payment, paid, in transit, delivered)
  - Service level
  - Total price
  - Tracking reference (when available)

---

## Managing Addresses

Addresses are required for creating quotes. You need at least two addresses (pickup and delivery).

### Adding an Address

1. Click **"Addresses"** in the navigation bar
2. Click **"Add Address"**
3. Fill in the address form:
   - **Label:** e.g., "Home", "Office", "Warehouse"
   - **Address Line 1:** Street address (required)
   - **Address Line 2:** Apartment, suite, etc. (optional)
   - **City:** (required)
   - **Province:** (optional)
   - **Postal Code:** (required)
   - **Country Code:** 2-letter code, e.g., "ZA" (required)
4. Click **"Save Address"**

### Viewing Addresses

- All your saved addresses appear as cards
- Each card shows the label and full address
- Empty state message if you have no addresses yet

### Deleting an Address

1. Find the address you want to remove
2. Click the **"Delete"** button (trash icon)
3. Confirm the deletion
4. The address will be removed immediately

**Note:** You cannot delete an address that's being used in active bookings.

---

## Getting Quotes

### Creating a Quote Request

1. Click **"New Quote"** or **"Get Quote"** from the dashboard
2. Fill in the quote form:

   **Addresses:**
   - Select **Pickup Address** from dropdown
   - Select **Delivery Address** from dropdown
   - Both addresses must be different

   **Parcel Details:**
   - **Weight (kg):** Enter weight in kilograms
   - **Length (cm):** Enter length in centimeters
   - **Width (cm):** Enter width in centimeters
   - **Height (cm):** Enter height in centimeters

3. Click **"Get Quotes"**

### Understanding Quote Results

After submitting, you'll see:

**Quote Comparison Table:**
- **Courier Name:** The shipping company
- **Service Level:** Standard, Express, or Overnight
- **Price:** Total price including VAT
- **Estimated Delivery:** Number of days
- **Action:** "Book Now" button

**Sorting:**
- Results are automatically sorted by price (lowest first)
- You can compare different service levels from the same courier

**Quote Expiry:**
- Quotes expire after 30 minutes
- You'll see an expiry time on the results page
- After expiry, you'll need to request a new quote

### Selecting a Quote

1. Review all available quotes
2. Compare prices and delivery times
3. Click **"Book Now"** on your preferred option
4. You'll be redirected to the booking confirmation page

---

## Booking Shipments

### Creating a Booking

When you click "Book Now" on a quote:

1. A booking is created with status **"pending_payment"**
2. You're redirected to the booking details page
3. The booking includes:
   - Unique booking ID
   - Selected service level
   - Pricing breakdown (base price + VAT)
   - Pickup and delivery addresses
   - Parcel details

### Booking Details Page

Shows comprehensive information:

**Status Banner:**
- Color-coded status indicator
- Contextual message about next steps
- Payment button (if payment pending)

**Booking Information:**
- Booking ID
- Service level
- Tracking reference (after payment)
- Creation date

**Pricing:**
- Base price
- VAT amount
- Total amount

**Route Details:**
- Pickup address
- Delivery address
- Parcel dimensions and weight

---

## Making Payments

### Payment Process

1. From the booking details page, click **"Pay Now"**
2. You'll be redirected to PayFast payment gateway
3. Complete payment using:
   - Credit/Debit card
   - Instant EFT
   - Other PayFast methods

### Payment Success

After successful payment:
- You're redirected to the success page
- Booking status changes to **"paid"**
- Shipment is created with the courier
- You receive a tracking reference
- Auto-redirect to booking details after 5 seconds

### Payment Cancellation

If you cancel payment:
- You're redirected to the cancel page
- Booking remains in **"pending_payment"** status
- You can retry payment anytime from booking details
- Auto-redirect to booking details after 5 seconds

### Payment Confirmation

- Payment confirmation happens via webhook
- Usually instant, but may take a few minutes
- Check your booking details page for status updates
- Refresh the page if status hasn't updated

---

## Tracking Shipments

### Viewing Tracking Information

1. Go to your dashboard
2. Click **"View Details"** on any paid booking
3. Scroll to **"Tracking History"** section

### Tracking Timeline

The tracking timeline shows:
- **Status:** Current shipment status
- **Location:** Where the parcel is
- **Description:** Details about the event
- **Timestamp:** When the event occurred

**Timeline Features:**
- Events displayed newest first
- Visual timeline with dots and lines
- Most recent event highlighted
- Full history of all tracking events

### Common Tracking Statuses

- **Picked Up:** Courier collected from sender
- **In Transit:** Package is moving
- **Out for Delivery:** Package on delivery vehicle
- **Delivered:** Successfully delivered
- **Exception:** Issue requiring attention

### Tracking Reference

- Unique reference number for your shipment
- Displayed on booking details page
- Can be used on courier's website for more details
- Available after payment confirmation

---

## Admin Portal

**Note:** Admin features are only available to users with admin privileges.

### Accessing Admin Portal

1. Login with admin credentials
2. Navigate to `/admin`
3. Or click **"Admin"** if you have admin access

### Admin Dashboard Tabs

#### 1. Overview Tab

Shows quick statistics:
- Recent bookings (last 5)
- Courier status summary
- Quick access to key metrics

#### 2. Couriers Tab

Manage courier services:

**Courier List:**
- Courier name and code
- Enabled/disabled status
- Base markup percentage
- Commission percentage
- Rating

**Actions:**
- **Enable/Disable:** Toggle courier availability
- Real-time status updates
- Affects quote generation immediately

#### 3. Bookings Tab

View all platform bookings:

**Booking Table:**
- Booking ID
- Service level
- Status
- Price
- Commission earned
- Tracking reference

**Features:**
- Sorted by newest first
- Limited to 100 most recent
- Status color-coding
- Full booking details

#### 4. Transactions Tab

Monitor all payments:

**Transaction Table:**
- Transaction ID
- Booking reference
- Status (completed, pending, failed)
- Amount
- Payment gateway
- Gateway reference

**Use Cases:**
- Payment reconciliation
- Failed payment investigation
- Revenue tracking

### Revenue Statistics

Top of admin dashboard shows:
- **Total Revenue:** All completed transactions
- **Total Commission:** Platform earnings
- **Total Bookings:** Number of bookings
- **Active Couriers:** Enabled courier count

### Admin Actions

**Enable/Disable Courier:**
1. Go to Couriers tab
2. Find the courier
3. Click **"Enable"** or **"Disable"**
4. Status updates immediately
5. Affects future quote requests

**View Booking Details:**
- Click on any booking ID
- See full booking information
- Access user details
- Review payment status

---

## FAQs

### General Questions

**Q: How long are quotes valid?**
A: Quotes expire after 30 minutes. You'll need to request a new quote after expiry.

**Q: Can I cancel a booking?**
A: Currently, bookings cannot be cancelled through the platform. Contact support for assistance.

**Q: What payment methods are accepted?**
A: We accept all PayFast payment methods including credit cards, debit cards, and instant EFT.

**Q: How do I get a receipt?**
A: Receipts are sent via email after payment confirmation. Check your spam folder if you don't see it.

### Address Questions

**Q: How many addresses can I save?**
A: There's no limit. Save as many addresses as you need.

**Q: Can I edit an address?**
A: Currently, you need to delete and recreate addresses. Update functionality coming soon.

**Q: What if my address isn't found?**
A: Ensure all required fields are filled correctly. Contact support if issues persist.

### Booking Questions

**Q: Why can't I book a quote?**
A: Quotes expire after 30 minutes. Request a new quote if yours has expired.

**Q: Can I change my booking after payment?**
A: No, bookings cannot be modified after payment. Contact support for special requests.

**Q: What if payment fails?**
A: You can retry payment from the booking details page. Ensure your payment method is valid.

### Tracking Questions

**Q: When will I get a tracking number?**
A: Tracking references are generated after payment confirmation, usually within minutes.

**Q: How often is tracking updated?**
A: Tracking updates depend on the courier. Typically every few hours during transit.

**Q: What if tracking shows no updates?**
A: Wait 24 hours after payment. If still no updates, contact support.

### Payment Questions

**Q: Is my payment information secure?**
A: Yes, all payments are processed through PayFast's secure gateway. We don't store card details.

**Q: How long does payment confirmation take?**
A: Usually instant, but can take up to 5 minutes during high traffic.

**Q: Can I get a refund?**
A: Refund requests must be submitted to support with your booking ID.

---

## Support

### Getting Help

**Email Support:**
- support@send-it.example.com
- Response time: 24-48 hours

**Documentation:**
- User Guide (this document)
- API Documentation
- FAQs

**When Contacting Support:**

Include:
1. Your email address
2. Booking ID (if applicable)
3. Screenshot of the issue
4. Detailed description of the problem
5. Steps to reproduce

**Response Times:**
- Email: 24-48 hours
- Urgent issues: 4-8 hours
- Payment issues: Priority handling

### Reporting Bugs

If you encounter a bug:

1. Note the exact steps that caused the issue
2. Take a screenshot
3. Check browser console for errors (F12)
4. Email details to support@send-it.example.com

### Feature Requests

We welcome feature suggestions:
- Email: features@send-it.example.com
- Include use case and benefits
- Describe desired functionality

---

## Tips & Best Practices

### Getting the Best Quotes

1. **Accurate Dimensions:** Measure your parcel carefully
2. **Compare Service Levels:** Balance cost vs. speed
3. **Book Quickly:** Quotes expire in 30 minutes
4. **Save Addresses:** Pre-save frequently used addresses

### Successful Bookings

1. **Verify Addresses:** Double-check pickup and delivery
2. **Correct Parcel Info:** Accurate weight and dimensions
3. **Complete Payment:** Don't leave bookings unpaid
4. **Save Tracking:** Note your tracking reference

### Tracking Shipments

1. **Check Regularly:** Monitor tracking updates
2. **Note Tracking Reference:** Save it somewhere safe
3. **Contact Courier:** For detailed tracking, use courier's site
4. **Report Issues:** Contact support if tracking seems stuck

### Account Security

1. **Strong Password:** Use 12+ characters with mixed case
2. **Logout:** Always logout on shared devices
3. **Secure Email:** Keep your email account secure
4. **Update Info:** Keep contact details current

---

## Glossary

**Booking:** A confirmed shipment order with a courier

**Commission:** Platform fee earned on each booking

**Courier:** Shipping company that delivers parcels

**Idempotency:** Prevents duplicate bookings from same request

**Parcel:** Package or item being shipped

**Quote:** Price estimate from a courier for shipping

**Service Level:** Speed of delivery (Standard, Express, Overnight)

**Tracking Reference:** Unique code to track your shipment

**VAT:** Value Added Tax included in pricing

**Webhook:** Automated payment confirmation from PayFast

---

## Quick Reference

### Common URLs

- **Dashboard:** `/dashboard`
- **Addresses:** `/addresses`
- **New Quote:** `/quote`
- **Booking Details:** `/bookings/{id}`
- **Admin Portal:** `/admin`

### Keyboard Shortcuts

- **Ctrl/Cmd + K:** Quick search (coming soon)
- **Esc:** Close modals
- **Tab:** Navigate form fields

### Status Colors

- 🟢 **Green:** Paid, Delivered, Completed
- 🟡 **Yellow:** Pending Payment
- 🔵 **Blue:** In Transit
- 🔴 **Red:** Cancelled, Failed

---

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Quote comparison
- Booking management
- Payment integration
- Tracking system
- Admin portal

### Upcoming Features
- Email notifications
- Address editing
- Booking cancellation
- Multi-currency support
- Mobile app
- Advanced filtering
- Export reports
- Bulk bookings

---

**Thank you for using SEND-IT!**

For the latest updates and announcements, visit our website or follow us on social media.
