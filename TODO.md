# LabelGen Project Roadmap

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

## Phase 2: Core Business Logic 🧠
- [ ] Implement configurable serial number generator:
  - [ ] Read start position and digit count from Config
  - [ ] Generate with leading zeros preserved
  - [ ] Atomic increment to prevent collisions
- [ ] Create bulk scan parser:
  - [ ] Pair alternating Part/Qty barcode scans
  - [ ] Validate Part Number format (XXX-XXXX)
  - [ ] Validate Quantity (positive integer)
- [ ] Implement Product auto-creation (with NULL UPC if not exists)
- [ ] Build SerialNumber batch creation logic

## Phase 3: User Interface Pages 🖥️
- [ ] **Bulk Serial Generation Page** (`/generate/`):
  - [ ] Dynamic table rows (start with 2, auto-add more)
  - [ ] Auto-focus chain: Part → Qty → Part → Qty
  - [ ] Live serial range preview
  - [ ] "Generate & Print" action button
  - [ ] Bulma styling with large scannable inputs
- [ ] **Box Label Page** (`/box-label/`):
  - [ ] Single serial input with auto-submit
  - [ ] Display Serial, Part, UPC
  - [ ] Print button
  - [ ] Recent scans list
- [ ] **Serial Reprint Page** (`/reprint/`):
  - [ ] Serial number search
  - [ ] Display record details
  - [ ] Reprint button
- [ ] **Admin UPC Management** (`/admin/upc/`):
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