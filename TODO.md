# LabelGen Project Roadmap

## Phase 1: Core Foundation 🏗️ ✅ COMPLETED
- [x] Initialize Django project and app structure
- [x] Set up Bulma.io CSS framework in base templates
- [x] Define Models:
  - [x] `Product` (PartNumber PK, UPC nullable)
  - [x] `SerialNumber` (SerialNumber PK, PartNumber FK, UPC denormalized, CreatedAt)
  - [x] `Config` (for serial start position and digit count)
- [x] Create migrations
- [x] Set up Django admin for Product and Config management

## Phase 2: Core Business Logic 🧠 ✅ COMPLETED
- [x] Implement configurable serial number generator:
  - [x] Read start position and digit count from Config
  - [x] Generate with leading zeros preserved
  - [x] Atomic increment to prevent collisions
- [x] Create bulk scan parser:
  - [x] Pair alternating Part/Qty barcode scans
  - [x] Validate Part Number format (XXX-XXXX)
  - [x] Validate Quantity (positive integer)
- [x] Implement Product auto-creation (with NULL UPC if not exists)
- [x] Build SerialNumber batch creation logic

## Phase 3: User Interface Pages 🖥️ ✅ COMPLETED
- [x] **Bulk Serial Generation Page** (`/generate/`):
  - [x] Dynamic table rows (start with 2, auto-add more)
  - [x] Auto-focus chain: Part → Qty → Part → Qty
  - [x] Live serial range preview
  - [x] "Generate & Print" action button
  - [x] Bulma styling with large scannable inputs
- [x] **Box Label Page** (`/box-label/`):
  - [x] Single serial input with auto-submit
  - [x] Display Serial, Part, UPC
  - [x] Print button
  - [x] Recent scans list
- [x] **Serial Reprint Page** (`/reprint/`):
  - [x] Serial number search
  - [x] Display record details
  - [x] Reprint button
- [ ] **Admin UPC Management** (`/admin/upc/`):
  - [ ] Password protection (Django auth) _(Using built-in Django admin for now)_
  - [ ] CSV upload (PartNumber,UPC format)
  - [ ] Manual edit table with inline editing
  - [ ] Add/delete Part-UPC associations
  - [ ] Password protection (Django auth)
  - [ ] CSV upload (PartNumber,UPC format)
  - [ ] Manual edit table with inline editing
  - [ ] Add/delete Part-UPC associations

## Phase 4: Printing Bridge (Go) 𝖇
- [ ] **Confirm printer model with client (Zebra/ZPL or other)**
- [ ] Initialize Go module `labelgen-bridge`
- [ ] Implement `/printers` endpoint (list system printers)
- [ ] Implement `/print` endpoint:
  - [ ] Accept printer command string
  - [ ] Accept target printer name
  - [ ] Send to system printer
- [ ] Test Windows `.exe` compilation
- [ ] Test macOS/Linux builds

## Phase 5: Integration & Label Templates 🔗
- [ ] Build JavaScript Print Controller:
  - [ ] Handle `localhost:5000` API calls
  - [ ] CORS handling
  - [ ] Error handling (bridge not running, printer not found)
  - [ ] Store printer selection in localStorage
- [ ] Create label templates (format TBD based on printer type):
  - [ ] Inventory label (serial number only with barcode)
  - [ ] Box label (serial, part, UPC with barcodes - omit UPC if null)
- [ ] Integrate print calls into all three pages

## Phase 6: Testing & Polish ✨
- [ ] Test hands-free bulk scanning workflow
- [ ] Test serial generation with different digit counts
- [ ] Test UPC upload and manual editing
- [ ] Error handling:
  - [ ] Invalid barcode format
  - [ ] Serial not found
  - [ ] Go bridge not running
  - [ ] Printer not found
- [ ] Refine Bulma styling for industrial warehouse use
- [ ] Mobile/tablet responsive design
- [ ] Audio/visual feedback for scan errors