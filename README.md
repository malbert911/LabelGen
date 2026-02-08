# LabelGen 🏷️

LabelGen is a full-stack inventory management bridge that transforms bulk barcode scans into sequential serial numbers and routes print jobs to local hardware.

## 🏗️ Architecture
- **Backend:** Django (Python) - Logic, Serial Number Generation, and DB Management.
- **Local Bridge:** Go - A lightweight binary (`.exe`) that listens for print requests on `localhost:5000` and talks to system printers.
- **Frontend:** Django Templates + JavaScript + Bulma.io CSS - Handles scanning, printer selection, and CORS requests to the local bridge.

## 🚀 Key Workflow

### 1. Bulk Serial Generation (Inventory Labels)
1. Worker scans a sheet with alternating Part/Qty barcodes:
   ```
   232-9983    (Part Number)
   12          (Quantity)
   243-0012    (Part Number)
   1           (Quantity)
   ```
2. Django generates sequential serial numbers (e.g., `000500`, `000501`, etc.)
3. Creates/updates Product records with Part Number
4. Stores SerialNumber records (Serial → Part → UPC if available)
5. Sends print commands to Go bridge for inventory labels (serial only)

### 2. Box Label Printing (Shipping)
1. Worker scans a Serial Number barcode
2. Django retrieves SerialNumber record with Part Number and UPC
3. Generates box label with all three values (omits UPC if blank)
4. Sends print command to Go bridge

### 3. Serial Number Reprint
1. Worker enters/scans a Serial Number
2. System reprints inventory label (serial only)

## 📊 Database Schema

**Product Table:**
- PartNumber (PK) - e.g., `232-9983`
- UPC (nullable) - e.g., `012345678901`

**SerialNumber Table:**
- SerialNumber (PK) - e.g., `000500` (configurable digit count)
- PartNumber (FK → Product)
- UPC (nullable, denormalized)
- CreatedAt

**Configuration:**
- Serial start position (default: `000500`)
- Serial digit count (default: 6, can be 10, 12, etc.)

## 🖥️ User Pages

1. **Bulk Serial Generation** (`/generate/`)
   - Hands-free scanning with dynamic rows
   - Auto-advance focus: Part → Qty → Part → Qty
   - Live preview of serial ranges
   
2. **Box Label Print** (`/box-label/`)
   - Single serial scan input
   - Auto-submit on scan complete
   - Displays Serial, Part, UPC

3. **Serial Reprint** (`/reprint/`)
   - Search by serial number
   - Reprint damaged inventory labels

4. **Admin: UPC Management** (`/admin/upc/`)
   - Password protected
   - CSV upload for bulk Part→UPC mapping
   - Manual edit interface

## 🛠️ Tech Stack
- Django 5.x / SQLite (Local/Dev)
- Go (Local Printer Bridge)
- Bulma.io (CSS Framework)
- Vanilla JavaScript (no frameworks)
- Printer command language TBD (ZPL if Zebra printers confirmed by client)

## 📁 Project Files
- `REQUIREMENTS.md` - Detailed specs, workflows, and Mermaid diagrams
- `TODO.md` - Implementation roadmap
- `.ai-context.md` - AI coding instructions