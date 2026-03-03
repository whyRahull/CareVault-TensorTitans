# Django Tailwind Frontend — CareVault (Revised)

## Key Decisions

| Concern | Decision |
|---|---|
| Tailwind | `django-tailwind` package (compiled, no CDN) |
| Auth | Django session auth. **Only org officials register** (with a one-time token). |
| Org registration | Super-admin generates `OrgRegistrationToken` in Django Admin → org official uses it at `/register/` |
| Employee management | Org-admin panel at `/org/` — add/list/remove employees |
| **Protected routes** | **Monitoring dashboards + detection/WS APIs only** — require org member login |
| **Public routes** | Everything else: incidents list, alerts, missing persons, profile — **no login required** |
| New models | `Organisation`, `OrgRegistrationToken` in a new `organisations` app |
| Existing JWT | Kept untouched (ML service + WebSocket consumer use it internally) |

---

## Auth Flow

```
Super Admin (Django Admin)
  └─ creates OrgRegistrationToken (one-time, expiring)
         │
         ▼
  Org Official visits /register/
  enters: token, org name, their name, password
         │
         ▼
  Organisation + CustomUser (role=org_admin) created
         │
         ▼
  Org Admin Panel (/org/) — adds employees
         │
         ▼
  Employee logs in at /login/
  → can now access monitoring dashboards + detection APIs
```


---

## New / Modified Models

### [NEW] `organisations` app

#### `Organisation`
| Field | Type |
|---|---|
| `name` | `CharField` |
| `created_at` | `DateTimeField(auto_now_add)` |
| `admin` | FK → [CustomUser](file:///d:/Code/carevault-tensortitans/core_api/users/models.py#5-23) |

#### `OrgRegistrationToken`
| Field | Type |
|---|---|
| `token` | `UUIDField(default=uuid4, unique)` |
| `organisation_name` | `CharField` — pre-filled hint |
| `used` | `BooleanField(default=False)` |
| `expires_at` | `DateTimeField` |
| `created_by` | FK → [CustomUser](file:///d:/Code/carevault-tensortitans/core_api/users/models.py#5-23) (the super-admin) |

### [MODIFY] `users.CustomUser`
Add `organisation` FK → `Organisation` (nullable — super-admins have no org).

---

## Page Inventory

| Page | URL | Auth |
|---|---|---|
| Login | `/login/` | Public |
| Org Register | `/register/` | Public (needs token) |
| Home / Dashboard | `/home/` | Public |
| Incidents List | `/incidents/` | Public |
| Incident Detail | `/incidents/<pk>/` | Public |
| Missing Persons | `/missing-persons/` | Public |
| Report Missing | `/missing-persons/new/` | Public |
| Alerts | `/alerts/` | Public |
| Profile | `/profile/` | Public |
| **Org Admin Panel** | `/org/` | ✅ Org admin only |
| **Add Employee** | `/org/add-employee/` | ✅ Org admin only |
| Violence Dashboard | `/incidents/dashboard/violence/` | ✅ **Login required** |
| Hand SOS Dashboard | `/incidents/dashboard/handsos/` | ✅ **Login required** |
| Lost Child Dashboard | `/incidents/dashboard/lostchild/` | ✅ **Login required** |
| WS stream | `/ws/stream/<room>/` | ✅ **Login required** |

---

## Proposed Changes

### `django-tailwind` setup
```bash
pip install django-tailwind
django-admin startapp theme   # inside core_api
python manage.py tailwind init
python manage.py tailwind install
```
`INSTALLED_APPS` gets `'tailwind'` and `'theme'`.

---

### [NEW] `organisations` app
- [models.py](file:///d:/Code/carevault-tensortitans/core_api/users/models.py) — `Organisation`, `OrgRegistrationToken`
- [admin.py](file:///d:/Code/carevault-tensortitans/core_api/users/admin.py) — register both; `OrgRegistrationToken` list shows token + used + expires

---

### [NEW] `web` app
- [views.py](file:///d:/Code/carevault-tensortitans/core_api/users/views.py) — all template views
- `forms.py` — `OrgRegisterForm`, `LoginForm`, `ProfileForm`, `AddEmployeeForm`, `MissingPersonForm`
- [urls.py](file:///d:/Code/carevault-tensortitans/core_api/users/urls.py) — all template routes
- `decorators.py` — `@org_admin_required` decorator

---

### Templates (`web/templates/web/`)
- `base.html` — sidebar + topbar (org name, user avatar, logout)
- `login.html`, `register.html`
- `home.html` — stats cards + dashboard links
- `incidents.html`, `incident_detail.html`
- `missing_persons.html`, `missing_person_form.html`
- `alerts.html`
- `profile.html`
- `org/panel.html` — employee list + remove
- `org/add_employee.html`

---

### [carevault_core/settings.py](file:///d:/Code/carevault-tensortitans/core_api/carevault_core/settings.py)
- Add `'tailwind'`, `'theme'`, `'web'`, `'organisations'`
- `TAILWIND_APP_NAME = 'theme'`
- `LOGIN_URL = '/'`, `LOGIN_REDIRECT_URL = '/home/'`, `LOGOUT_REDIRECT_URL = '/'`

### [carevault_core/urls.py](file:///d:/Code/carevault-tensortitans/core_api/carevault_core/urls.py)
- Mount `web.urls` at `/`

---

## Verification
1. `tailwind install` + `tailwind build` succeeds
2. `python manage.py check` — 0 issues
3. Django Admin → generate an `OrgRegistrationToken`
4. Visit `/register/` with token → org + org_admin user created
5. Login → `/home/` shows real stats
6. Org Admin Panel → add employee → employee can log in
