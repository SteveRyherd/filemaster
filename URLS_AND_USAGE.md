# FileMaster URLs & Usage Guide

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

2. **Access the application:**
   - Landing Page: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin/new_request
   - Customer Interface: http://localhost:8000/customer?token=YOUR_TOKEN

## 📍 Available URLs

### For Staff/Admin:
- **Landing Page**: http://localhost:8000
  - Overview of the system with links to admin and info about customer access
  
- **Create Request**: http://localhost:8000/admin/new_request
  - Create new document collection requests
  - Select which modules (documents) to include
  - Get a shareable customer URL

### For Customers:
- **Customer Portal**: http://localhost:8000/customer?token=YOUR_TOKEN
  - Replace `YOUR_TOKEN` with the actual token from a request
  - Customers use this link to submit their documents
  - Beautiful, mobile-friendly interface with progress tracking

## 🔄 Typical Workflow

1. **Staff creates a request:**
   - Go to http://localhost:8000/admin/new_request
   - Enter request name (e.g., "John Smith - 2025 Camry")
   - Select required modules (SSN, Driver's License, etc.)
   - Click "Create"
   - A modal will show the full customer URL

2. **Copy and share the URL:**
   - The success modal shows the complete customer URL
   - Click "Copy" to copy it to clipboard
   - Click "Preview" to test it yourself
   - Send this URL to your customer via email/SMS

3. **Customer completes request:**
   - Customer opens the link
   - They see their progress and required documents
   - They complete each module one by one
   - Progress bar updates as they go

## 🧪 Test Script

Run the included test script to automatically create a request and get a customer URL:

```bash
python test_customer_flow.py
```

This will:
- Create a request with SSN module
- Display the customer URL
- Test the API submission

## 📋 Currently Available Modules

- **SSN**: Social Security Number (with encryption)
- **Sample**: Basic text input module
- **Drivers License**: Structure ready, file upload coming soon

## 🎨 Features

- Beautiful automotive-themed design (teal to orange gradient)
- Mobile-responsive interface
- Real-time progress tracking
- Secure data encryption for sensitive fields
- Auto-navigation to next required module
- Access logging for security

## 🔧 Development

- API Documentation: http://localhost:8000/docs (FastAPI automatic docs)
- Module handlers in: `app/modules/*/handler.py`
- Customer interface: `static/customer.html`
- Admin interface: `static/new_request.html`
