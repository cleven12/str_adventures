# Structured Adventures — Full Django Backend

## Project structure

```
sa_full/
├── apps/
│   ├── booking/          ← REWRITTEN: no payment gateway, enquiry-only
│   │   ├── models.py     ← Booking, GroupMember, GroupDeparture, ContactEnquiry, PaymentRecord
│   │   ├── views.py      ← form capture → DB → email → confirmation page
│   │   ├── forms.py      ← BookingForm, GroupJoinForm, ContactEnquiryForm
│   │   ├── admin.py      ← full staff workflow with 5 admin actions
│   │   ├── urls.py       ← clean, no DPO callback routes
│   │   └── services/     ← (no DPO service — removed)
│   ├── core/             ← REWRITTEN: branding, views, context processors
│   │   ├── models.py     ← SiteSettings, FAQ, TeamMember, JobPosting (unchanged)
│   │   ├── views.py      ← HomeView, about, faq, careers, contact redirect
│   │   ├── urls.py       ← core routes
│   │   ├── context_processors.py ← site_settings, tour_navigation, brand_rating
│   │   ├── middleware.py ← LegacyRedirectMiddleware, RateLimitMiddleware (unchanged)
│   │   ├── seo_engine.py ← full schema engine (unchanged)
│   │   └── services/
│   │       └── email_service.py ← REWRITTEN: no payment emails, DPO link emails added
│   ├── tours/            ← UNCHANGED from visitkili (full SEO model)
│   ├── guide/            ← UNCHANGED (TrekGuide, BlogArticle, mesh)
│   ├── destinations/     ← UNCHANGED
│   ├── itinerary/        ← UNCHANGED
│   └── reviews/          ← REWRITTEN views.py: uses new booking status fields
├── config/
│   ├── settings.py       ← REWRITTEN: SA branding, no DPO API settings
│   └── urls.py           ← REWRITTEN: no ai_chat, no indexing routes
├── templates/emails/     ← 10 email templates (Structured Adventures branded)
├── requirements.txt
└── .env.example
```

## What changed from visitkili

### Removed entirely
- `apps/ai_chat/` — not needed
- `apps/indexing/` — can be re-added later if Google Indexing API is needed
- `apps/booking/services/dpo_service.py` — NO gateway calls from Django
- `booking_checkout`, `group_checkout`, `dpo_callback` views — gone
- `PaymentTransaction` model — replaced by `PaymentRecord` (manual staff entry)

### Booking flow (NEW)
```
Client fills form
       ↓
Saved to DB (status=pending)
       ↓
Email → staff (with admin link) + client (confirmation)
       ↓
Staff review in Django admin
       ↓
Staff call/WhatsApp client, agree price
       ↓
Staff generate DPO link at merchant.dpo.group
       ↓
Staff paste URL into booking admin → save
       ↓
Staff click "→ Send DPO Link to Client" admin action
       ↓
Client receives email with DPO pay button
       ↓
Client pays on DPO (off-site)
       ↓
Staff click "$ Mark Payment Confirmed" admin action
```

### Admin actions
| Action | Effect |
|--------|--------|
| ✓ Confirm selected bookings | status→confirmed, email client |
| → Send DPO payment link to client | emails dpo_payment_url to client |
| $ Mark payment confirmed | sets payment_confirmed=True |
| ✓ Accept selected join requests | group member accept + email |
| ✗ Reject selected join requests | group member reject |

### Booking model fields (new vs old)
| Old (visitkili) | New (SA) |
|-----------------|----------|
| `payment_status` enum | `payment_confirmed` boolean |
| `payment_transaction_token` | `dpo_payment_url` (staff paste) |
| `dpo_trans_token` | removed |
| `booking_id` (8 chars) | `booking_ref` (SA prefixed) |

## Setup

```bash
# Clone / extract
cd sa_full

# Python env
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Config
cp .env.example .env
# Edit .env — add SECRET_KEY, DB settings, email, Cloudinary

# Database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Dev server
python manage.py runserver
```

## Environment variables (key ones)

```env
SITE_NAME=Structured Adventures
SITE_DOMAIN=structuredadventures.com
WHATSAPP_NUMBER=+255XXXXXXXXX
STAFF_EMAILS=ops@structuredadventures.com,bookings@structuredadventures.com
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DPO_COMPANY_TOKEN=your-dpo-token   # kept for reference, no API calls
```

## Migrations

The booking app has a hand-written migration (`0001_initial.py`).
All other apps keep their existing migrations from visitkili.

```bash
python manage.py migrate booking
python manage.py migrate        # everything else
```

## UI (next phase)

The backend is fully decoupled from any specific frontend approach.
Templates are plain Django templates ready to receive:
- HTMX attributes for dynamic interactions
- Alpine.js for client-side state (filters, accordions, tabs)
- Tailwind CSS (build with Tailwind CLI binary — no Node.js server required)

UI design will be done in v0, HTML generated, then dropped into
`templates/` with Django template syntax added.
