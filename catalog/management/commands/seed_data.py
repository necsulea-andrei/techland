from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Product, ProductImage


class Command(BaseCommand):
    help = 'Seeds the database with at least 30 products across 4 categories'

    def handle(self, *args, **options):
        self.stdout.write("Cleaning previous catalog data...")
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        # 4.categorii conform nisei
        categories_data = [
            {"name": "Processors & CPUs", "description": "High performance consumer and workstation desktop CPUs."},
            {"name": "Memory & Storage", "description": "High-speed DDR5 RAM modules and ultra-fast NVMe PCIe SSDs."},
            {"name": "Industrial PLCs", "description": "Programmable Logic Controllers for automation and plant control."},
            {"name": "I/O & Power Modules", "description": "Digital/Analog expansion units, relays, and DIN-rail power supplies."}
        ]

        categories = {}
        for cat_info in categories_data:
            cat = Category.objects.create(
                name=cat_info["name"],
                slug=slugify(cat_info["name"]),
                description=cat_info["description"]
            )
            categories[cat_info["name"]] = cat

        # Cele 32 de produse din scriptul tau
        products_data = [
            # Categoria 1: Processors & CPUs (8 produse)
            {"category": "Processors & CPUs", "name": "AMD Ryzen 7 7800X3D", "sku": "CPU-AMD-7800X3D", "price": "2199.99", "stock": 15, "description": "8 cores, 16 threads, 3D V-Cache architecture, ideal for intensive workstation and simulation tasks."},
            {"category": "Processors & CPUs", "name": "Intel Core i7-14700K", "sku": "CPU-INT-14700K", "price": "2049.50", "stock": 12, "description": "20 cores (8P + 12E), up to 5.6 GHz, LGA1700 desktop processor."},
            {"category": "Processors & CPUs", "name": "AMD Ryzen 9 7950X", "sku": "CPU-AMD-7950X", "price": "2890.00", "stock": 8, "description": "16 cores, 32 threads, 4.5 GHz base clock, flagship productivity processor."},
            {"category": "Processors & CPUs", "name": "Intel Core i5-14600K", "sku": "CPU-INT-14600K", "price": "1549.00", "stock": 20, "description": "14 cores (6P + 8E), efficient processing for automation host control rigs."},
            {"category": "Processors & CPUs", "name": "AMD Ryzen 5 7600X", "sku": "CPU-AMD-7600X", "price": "1099.00", "stock": 25, "description": "6 cores, 12 threads, AM5 socket with integrated RDNA2 graphics."},
            {"category": "Processors & CPUs", "name": "Intel Core i9-14900KS", "sku": "CPU-INT-14900KS", "price": "3499.00", "stock": 5, "description": "Special edition desktop processor capable of up to 6.2 GHz out of the box."},
            {"category": "Processors & CPUs", "name": "AMD Ryzen 9 7900X3D", "sku": "CPU-AMD-7900X3D", "price": "2450.00", "stock": 7, "description": "12 cores, 24 threads, enhanced L3 cache for demanding computation workloads."},
            {"category": "Processors & CPUs", "name": "Intel Core i3-14100", "sku": "CPU-INT-14100", "price": "620.00", "stock": 30, "description": "Quad-core entry CPU for industrial gateway PCs and lightweight servers."},

            # Categoria 2: Memory & Storage (8 produse)
            {"category": "Memory & Storage", "name": "Samsung 990 PRO 2TB NVMe SSD", "sku": "SSD-SAM-990P-2TB", "price": "899.99", "stock": 25, "description": "PCIe 4.0 NVMe M.2 SSD reaching up to 7450 MB/s sequential read."},
            {"category": "Memory & Storage", "name": "Corsair Vengeance DDR5 32GB (2x16GB) 6000MHz", "sku": "RAM-COR-32GB-D5", "price": "580.00", "stock": 18, "description": "High performance dual-channel DDR5 memory kit with Intel XMP 3.0 support."},
            {"category": "Memory & Storage", "name": "Kingston KC3000 1TB NVMe SSD", "sku": "SSD-KNG-KC3-1TB", "price": "470.00", "stock": 35, "description": "PCIe 4.0 NVMe M.2 with 3D TLC NAND controller for heavy data logging."},
            {"category": "Memory & Storage", "name": "G.Skill Ripjaws S5 64GB (2x32GB) DDR5", "sku": "RAM-GSK-64GB-D5", "price": "1050.00", "stock": 10, "description": "Low profile high capacity memory kit optimized for engineering CAD stations."},
            {"category": "Memory & Storage", "name": "Crucial T700 1TB PCIe Gen5 SSD", "sku": "SSD-CRU-T700-1TB", "price": "980.00", "stock": 8, "description": "Next-generation PCIe 5.0 storage reaching speeds up to 11,700 MB/s."},
            {"category": "Memory & Storage", "name": "Crucial Pro 32GB (2x16GB) DDR4 3200MHz", "sku": "RAM-CRU-32GB-D4", "price": "310.00", "stock": 22, "description": "Standard DDR4 memory modules for legacy computing installations."},
            {"category": "Memory & Storage", "name": "WD Black SN850X 4TB NVMe SSD", "sku": "SSD-WDC-SN8-4TB", "price": "1720.00", "stock": 6, "description": "Massive high-speed solid state drive for system images and telemetry logs."},
            {"category": "Memory & Storage", "name": "TeamGroup T-Force 32GB DDR5 5600MHz", "sku": "RAM-TMG-32GB-D5", "price": "490.00", "stock": 14, "description": "Reliable ECC-on-die DDR5 kit for continuous runtime applications."},

            # Categoria 3: Industrial PLCs (8 produse)
            {"category": "Industrial PLCs", "name": "Siemens SIMATIC S7-1200 CPU 1214C DC/DC/DC", "sku": "PLC-SIE-1214C-DC", "price": "2450.00", "stock": 10, "description": "Compact CPU with 14 DI 24V DC, 10 DO 24V DC, and 2 AI 0-10V DC integrated."},
            {"category": "Industrial PLCs", "name": "Siemens SIMATIC S7-1200 CPU 1212C AC/DC/RLY", "sku": "PLC-SIE-1212C-RL", "price": "1890.00", "stock": 14, "description": "Compact controller with 8 DI 24V DC, 6 DO relay outputs, 2 AI onboard."},
            {"category": "Industrial PLCs", "name": "Schneider Electric Modicon M221 24 IO", "sku": "PLC-SCH-M221-24", "price": "1420.00", "stock": 16, "description": "Logic controller for hardwired architectures with Ethernet communication port."},
            {"category": "Industrial PLCs", "name": "Omron CP1L-EM30DR-D", "sku": "PLC-OMR-CP1L-30", "price": "2100.00", "stock": 9, "description": "Compact PLC with embedded Ethernet interface, 18 inputs and 12 relay outputs."},
            {"category": "Industrial PLCs", "name": "Schneider Electric Modicon M241 40 IO", "sku": "PLC-SCH-M241-40", "price": "2780.00", "stock": 7, "description": "High performance controller for motion control and machine automation."},
            {"category": "Industrial PLCs", "name": "Siemens SIMATIC S7-1500 CPU 1511-1 PN", "sku": "PLC-SIE-1511-PN", "price": "4890.00", "stock": 4, "description": "Standard modular PLC for medium to high complexity manufacturing lines."},
            {"category": "Industrial PLCs", "name": "Omron NX1P2-9024DT", "sku": "PLC-OMR-NX1P2-24", "price": "3150.00", "stock": 6, "description": "EtherCAT and EtherNet/IP integrated machine automation controller."},
            {"category": "Industrial PLCs", "name": "Eaton easyE4 Nano PLC 12/24V DC", "sku": "PLC-EAT-E4-12DC", "price": "680.00", "stock": 25, "description": "Control relay unit for small building and industrial task automation."},

            # Categoria 4: I/O & Power Modules (8 produse)
            {"category": "I/O & Power Modules", "name": "Siemens SM 1223 16 DI / 16 DO Module", "sku": "EXP-SIE-SM1223-16", "price": "1150.00", "stock": 20, "description": "Digital input/output signal board module for SIMATIC S7-1200 expansion."},
            {"category": "I/O & Power Modules", "name": "Mean Well HDR-60-24 DIN Rail PSU 24V 2.5A", "sku": "PSU-MW-HDR60-24", "price": "125.00", "stock": 45, "description": "Ultra slim 60W industrial DIN-rail power supply with universal AC input."},
            {"category": "I/O & Power Modules", "name": "Mean Well NDR-240-24 Industrial PSU 24V 10A", "sku": "PSU-MW-NDR240-24", "price": "295.00", "stock": 30, "description": "Economical 240W DIN-rail power unit with active PFC function."},
            {"category": "I/O & Power Modules", "name": "Phoenix Contact Quint Power Supply 24V 20A", "sku": "PSU-PHX-QUINT-20", "price": "1280.00", "stock": 11, "description": "High reliability power supply with dynamic boost and preventive function monitoring."},
            {"category": "I/O & Power Modules", "name": "Siemens SM 1231 4 AI Analog Module", "sku": "EXP-SIE-SM1231-4A", "price": "980.00", "stock": 15, "description": "4-channel analog input module (voltage/current measurement) for S7-1200."},
            {"category": "I/O & Power Modules", "name": "Schneider Electric TM3 8-Relay Output Module", "sku": "EXP-SCH-TM3-8R", "price": "430.00", "stock": 22, "description": "Expansion I/O module with 8 relay outputs for Modicon M221/M241."},
            {"category": "I/O & Power Modules", "name": "Weidmuller Industrial Ethernet Switch 5-Port", "sku": "NET-WEI-IES-5P", "price": "340.00", "stock": 18, "description": "Unmanaged 5-port RJ45 DIN-rail switch for industrial network topologies."},
            {"category": "I/O & Power Modules", "name": "Finder 24V DC Relay Interface Module 8-Channel", "sku": "RLY-FND-24DC-8C", "price": "190.00", "stock": 40, "description": "Electromechanical relay interface module for PLC output coupling."}
        ]

        for item in products_data:
            # Creare produs cu slug
            product = Product.objects.create(
                category=categories[item["category"]],
                name=item["name"],
                slug=slugify(item["name"]),
                sku=item["sku"],
                price=Decimal(item["price"]),
                stock=item["stock"],
                is_active=True
            )

            #salvare imagine in tabela asociata ProductImage (1:N)
            ProductImage.objects.create(
                product=product,
                image_url=f"products/{item['sku'].lower()}.png",
                is_feature=True
            )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {Category.objects.count()} categories and {Product.objects.count()} products into 10-table schema!"
        ))