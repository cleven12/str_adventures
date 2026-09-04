# Structured Adventures — Backend Re-engineering Notes

## What Changed from visitkili

### Booking App — Complete Overhaul

**Before (visitkili):**
- Booking create → DPO API call → redirect to DPO payment page
- PaymentTransaction model with gateway state machine
- dpo_callback webhook endpoint (csrf_exempt)
- booking_checkout / group_checkout views (DPO redirect)

**After (Structured Adventures):**
- Booking create → save to DB → email staff + client → redirect to "received" page
- Staff review in admin → confirm → agree price → generate DPO link manually
- Staff paste DPO URL into admin → use admin action to email client
- Client pays via DPO off-site → staff manually tick payment_confirmed

### Models Changed

| Model | Before | After |
|-------|--------|-------|
| `Booking` | Had DPO token fields, payment_status, PaymentProvider | Has `dpo_payment_url` (staff-pasted), `payment_confirmed` (staff-ticked), `quoted_price_usd` |
| `GroupMember` | Had payment_status enum, DPO tokens | Has `dpo_payment_url`, `payment_confirmed`, `status` = pending/accepted/rejected/cancelled |
| `PaymentTransaction` | Automated gateway audit trail | Removed → replaced by `PaymentRecord` (manual staff entry) |
| `ContactEnquiry` | Was part of core app | Moved into booking app, topic choices added |

### Views Removed
- `booking_checkout` — no longer needed (no DPO redirect from Django)
- `group_checkout` — same
- `booking_confirm` (old) — now `booking_status` (just shows status)
- `group_confirm` — same
- `dpo_callback` — GONE. Zero webhook endpoints.

### New Admin Actions (staff workflow)
1. **"✓ Confirm selected bookings"** — sets status=confirmed, emails client
2. **"→ Send DPO payment link to client"** — emails the pasted DPO URL
3. **"$ Mark payment confirmed"** — sets payment_confirmed=True
4. **"✓ Accept selected join requests"** — group member accept + emails client
5. **"✗ Reject selected join requests"** — group member reject

### Email Templates Added
| Template | Trigger |
|----------|---------|
| `booking_received_client.html` | Client submits booking form |
| `booking_received_staff.html` | Same — staff notification |
| `booking_confirmed_client.html` | Staff confirms booking in admin |
| `booking_dpo_link.html` | Staff sends DPO link via admin action |
| `group_join_received_client.html` | Client submits group join |
| `group_join_received_staff.html` | Same — staff notification |
| `group_join_accepted_client.html` | Staff accepts member in admin |
| `group_dpo_link.html` | Staff sends DPO link for group member |
| `contact_staff.html` | Contact form submission |
| `contact_received_client.html` | Same — auto-reply to client |

### Email Templates Removed
- `payment_success.html`
- `payment_failed.html`
- `admin_payment_received.html`

## Staff Workflow (step by step)

### Individual Booking
1. Client fills booking form → status=`pending` → staff + client get email
2. Staff open booking in Django admin
3. Staff call/WhatsApp client, confirm dates and price
4. Staff enter `quoted_price_usd` and generate DPO link at merchant.dpo.group
5. Staff paste URL into `dpo_payment_url` field → save
6. Staff click **"→ Send DPO Link to Client"** admin action
7. Client receives email with payment button → pays on DPO
8. DPO emails confirmation to staff (from DPO dashboard notification)
9. Staff come back to admin → click **"$ Mark Payment Confirmed"**

### Group Join
Same flow but:
- Step 3: Staff click **"✓ Accept"** admin action first (reserves spot)
- Steps 4-9: Same as above

## DPO Custom URL Setup

Log in to https://merchant.dpo.group/
→ Payment Links → Create Payment Link
→ Set amount in USD, description = booking ref + tour name
→ Copy the URL
→ Paste into Django admin booking record

The URL format is typically:
`https://pay.dpo.group/link/XXXXXXXXXXXX`

## Environment Variables to Remove
```
DPO_SERVICE_TYPE=
DPO_API_URL=
DPO_PAYMENT_URL=
DPO_REDIRECT_BASE_URL=
```

## Environment Variables to Add/Change
```
SITE_NAME=Structured Adventures
SITE_DOMAIN=structuredadventures.com
WHATSAPP_NUMBER=+255XXXXXXXXX
STAFF_EMAILS=ops@structuredadventures.com,reservations@structuredadventures.com
CONTACT_EMAIL=info@structuredadventures.com
DEFAULT_FROM_EMAIL=Structured Adventures <noreply@structuredadventures.com>
```

## Migration
```bash
python manage.py makemigrations booking
python manage.py migrate
```

Note: If migrating from existing visitkili DB:
- Old `payment_status` data will be lost (it's all 'pending' anyway for new site)
- Old DPO token fields are gone — no issue for fresh deployment
- Run on fresh DB: `python manage.py migrate` directly
