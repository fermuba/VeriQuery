# Database Configuration Components - Frontend

## 📱 Components Overview

Three lightweight, production-ready React components for secure database configuration with Azure Key Vault:

### 1. **PermissionValidator.jsx** (169 lines)
Displays read-only permission validation results with:
- ✅ Status indicator (read-only vs write access)
- 📋 Permission check details for each database type
- 📝 Auto-generated SQL code for creating read-only users
- ⚠️ Warning messages if write permissions detected
- 📋 Copy-to-clipboard functionality for SQL snippets

### 2. **DatabaseWizard.jsx** (343 lines)
Multi-step wizard for database configuration:
- 🔢 4-step workflow: Input → Validate → Permissions → Success
- 📊 Progress indicator showing current step
- 🔐 Real-time permission validation
- 💾 Automatic save to Azure Key Vault
- ✨ Smooth animations and transitions

### 3. **DatabaseModal.jsx** (48 lines)
Modal container for DatabaseWizard:
- 🎨 Clean backdrop and overlay
- ⌨️ Keyboard accessible close button
- 📱 Responsive sizing
- 🎬 Smooth animations

### 4. **DatabaseConfigPanel.jsx** (263 lines)
Dashboard for managing all database configurations:
- 📊 List all saved databases
- ✓ Verify connection status
- 🗑️ Delete configurations
- 🔐 Display Key Vault storage status
- ℹ️ Security information box

---

## 🚀 Quick Start

### Import Components
```jsx
import DatabaseConfigPanel from '@/components/database/DatabaseConfigPanel'
import DatabaseModal from '@/components/database/DatabaseModal'
import DatabaseWizard from '@/components/database/DatabaseWizard'
import PermissionValidator from '@/components/database/PermissionValidator'
```

### Use DatabaseConfigPanel (Recommended)
```jsx
export default function ConfigurationPage() {
  return (
    <div className="p-6">
      <DatabaseConfigPanel />
    </div>
  )
}
```

### Use DatabaseWizard Directly
```jsx
export default function AddDatabase() {
  return (
    <DatabaseWizard
      onSuccess={(config) => console.log('Saved:', config)}
      onCancel={() => console.log('Cancelled')}
    />
  )
}
```

### Use DatabaseModal with Custom Button
```jsx
export default function AdminPanel() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Add Database
      </button>
      <DatabaseModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSuccess={(config) => {
          console.log('Database saved:', config)
          // Refresh database list, show notification, etc
        }}
      />
    </>
  )
}
```

---

## 🎨 Component Architecture

```
DatabaseConfigPanel
├── ✓ List of saved databases
├── ✓ Add Database button → opens DatabaseModal
│   └── DatabaseModal (overlay + close button)
│       └── DatabaseWizard (4-step workflow)
│           ├── Step 1: Input form
│           ├── Step 2: Validation (API call)
│           ├── Step 3: PermissionValidator
│           │   └── Permission details + SQL snippets
│           └── Step 4: Success message
└── ✓ Database detail actions (verify, delete)
```

---

## 📋 Component Props

### PermissionValidator
```jsx
<PermissionValidator
  permissions={{
    is_readonly: true,
    readonly_message: "✓ Read-only confirmed",
    permission_details: {
      db_type: "SQL Server",
      checks: [
        { name: "User Identity", status: "✓ PASS", has_permission: true },
        { name: "INSERT", status: "✗ FAIL", has_permission: false }
      ]
    },
    warnings: ["Warning message"]
  }}
  isLoading={false}
  onContinue={() => {}}
  onCancel={() => {}}
/>
```

### DatabaseWizard
```jsx
<DatabaseWizard
  onSuccess={(config) => {
    // config = { success, message, stored_in_keyvault, is_readonly, ... }
  }}
  onCancel={() => {}}
/>
```

### DatabaseModal
```jsx
<DatabaseModal
  isOpen={boolean}
  onClose={() => {}}
  onSuccess={(config) => {}}
/>
```

### DatabaseConfigPanel
```jsx
<DatabaseConfigPanel />  // No props needed
```

---

## 🎬 Animations

All components use Framer Motion for smooth transitions:

| Animation | Usage |
|-----------|-------|
| `initial={{ opacity: 0, scale: 0.95 }}` | Modal entry |
| `animate={{ opacity: 1, scale: 1 }}` | Component appear |
| `exit={{ opacity: 0, scale: 0.95 }}` | Component leave |
| `transition={{ delay: idx * 0.05 }}` | Stagger list items |
| `transition={{ type: 'spring', damping: 25 }}` | Bouncy modal |

---

## 🎨 Styling System

All components use the existing design system:

### CSS Classes Used
- `bento-card` - Main card component
- `bg-foreground` / `text-foreground` - Text colors
- `bg-primary` / `text-primary-foreground` - Primary actions
- `bg-success` / `text-success` - Success states
- `bg-warning` / `text-warning` - Warning states
- `bg-destructive` / `text-destructive` - Delete actions
- `bg-muted` / `text-muted-foreground` - Disabled/secondary
- `rounded` - Border radius
- `transition-colors` - Smooth color changes

### No External CSS Files
- ✅ Uses Tailwind CSS from existing project
- ✅ No new imports or dependencies
- ✅ Consistent with current design system

---

## 🔗 API Integration

### Endpoints Used

| Endpoint | Method | Component |
|----------|--------|-----------|
| `/api/databases/test` | POST | DatabaseWizard (step 1 validation) |
| `/api/databases/credentials/validate` | POST | DatabaseWizard (step 2 permissions) |
| `/api/databases/save` | POST | DatabaseWizard (step 3 save) |
| `/api/databases/credentials/{db}/verify` | POST | DatabaseConfigPanel |
| `/api/databases/credentials/{db}` | DELETE | DatabaseConfigPanel |

### Request/Response Handling
- ✅ Error messages displayed in UI
- ✅ Loading states with spinners
- ✅ Auto-disable buttons while loading
- ✅ Success animations on completion

---

## 📱 Responsive Design

- ✅ Mobile: Stack vertically, full width buttons
- ✅ Tablet: 2-column grid for database list
- ✅ Desktop: Full multi-column layout
- ✅ Modal: Always centered with padding
- ✅ All components scroll independently

---

## 🔒 Security Features

### What's Implemented
1. **Password Input** - Uses `type="password"` with `••••••••` masking
2. **No Local Storage** - Credentials sent directly to API
3. **HTTPS Ready** - Compatible with `https://` URLs
4. **CORS Handling** - API configured for cross-origin requests
5. **Error Handling** - No sensitive data in error messages

### Best Practices
- ✅ Never log credentials to console
- ✅ Don't store passwords in component state longer than needed
- ✅ Use environment variables for API URLs
- ✅ Validate read-only before saving
- ✅ Warn users about write permissions

---

## 🐛 Troubleshooting

### Modal Won't Close
```jsx
// Make sure you're calling onClose
<DatabaseModal onClose={() => setIsOpen(false)} />
```

### Components Not Styled
```jsx
// Ensure Tailwind CSS is imported in main App.jsx
import './App.css'  // Contains tailwind directives
```

### API Calls Failing
```jsx
// Check that backend is running on port 8888
// Verify CORS is enabled in FastAPI:
// app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### Permissions Not Showing
```jsx
// PermissionValidator only shows if permissions prop is provided
// Make sure API returns permission_details
```

---

## 📦 File Structure

```
frontend/src/components/database/
├── PermissionValidator.jsx      (169 lines)
├── DatabaseWizard.jsx           (343 lines)
├── DatabaseModal.jsx            (48 lines)
└── DatabaseConfigPanel.jsx      (263 lines)

Total: 823 lines of clean, production-ready code
```

---

## 🚀 Deployment

### Development
```bash
npm run dev  # Already running with HMR
```

### Production Build
```bash
npm run build
npm run preview
```

### Environment Variables
```env
VITE_API_URL=https://api.example.com:8888
```

Update API calls if using env variable:
```jsx
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888'
fetch(`${API_URL}/api/databases/save`, ...)
```

---

## 💡 Tips & Tricks

### Custom Success Handler
```jsx
<DatabaseConfigPanel />
// Or intercept with modal:
<DatabaseModal
  onSuccess={(config) => {
    if (config.is_readonly) {
      showNotification('✓ Secure read-only connection!')
    } else {
      showNotification('⚠ Remember to create read-only user')
    }
  }}
/>
```

### Pre-fill Form
```jsx
// To modify DatabaseWizard to accept initial values,
// update useState to:
const [formData, setFormData] = useState(initialConfig || { ... })
```

### Disable Wizard Steps
```jsx
// Add canSkipPermissions prop to DatabaseWizard
// and conditional step jumping logic
```

---

## 📝 License & Support

**Product:** Forensic Data Guardian  
**Component:** Database Configuration Frontend  
**Version:** 1.0  
**Last Updated:** March 2026  

For backend integration: See `KEYVAULT_IMPLEMENTATION.md`
