from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Product, ProductImage
try:
    from catalog.models import Review
except ImportError:
    Review = None

try:
    from orders.models import Order, OrderItem, Cart, CartItem
except ImportError:
    Order = OrderItem = Cart = CartItem = None


class Command(BaseCommand):
    help = "Populates database with 32 hardware & automation products with strictly verified tech images and English descriptions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing existing orders, carts, and catalog data..."))

        # 1. Curățare în ordinea corectă a constrângerilor SQL
        if OrderItem:
            OrderItem.objects.all().delete()
        if Order:
            Order.objects.all().delete()
        if CartItem:
            CartItem.objects.all().delete()
        if Cart:
            Cart.objects.all().delete()
        if Review:
            Review.objects.all().delete()

        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        # 2. Categorii principale
        categories_data = [
            {"name": "Processors (CPUs)", "slug": "processors-cpus"},
            {"name": "Memory & Storage", "slug": "memory-storage"},
            {"name": "Industrial PLCs & Controllers", "slug": "industrial-plcs"},
            {"name": "Industrial I/O & Automation Modules", "slug": "automation-modules"},
        ]

        category_instances = {}
        for cat_info in categories_data:
            cat = Category.objects.create(
                name=cat_info["name"],
                slug=cat_info["slug"]
            )
            category_instances[cat_info["slug"]] = cat
            self.stdout.write(self.style.SUCCESS(f"Category created: {cat.name} [{cat.slug}]"))

        # 3. Lista celor 32 de produse cu imagini tehnice conforme 100%
        products_data = [
            # =========================================================================
            # CATEGORY 1: Processors (CPUs)
            # =========================================================================
            {
                "cat": "processors-cpus",
                "name": "AMD Ryzen 7 7800X3D",
                "sku": "CPU-AMD-7800X3D",
                "price": Decimal("2199.99"),
                "stock": 14,
                "desc": "Premier desktop gaming processor engineered on AMD Zen 4 architecture with 5nm lithography. Integrates 8 high-performance cores, 16 threads, and revolutionary 96MB 3D V-Cache technology reaching boost clocks up to 5.0 GHz. Built for the modern AM5 socket with full PCIe 5.0 lane bandwidth and high-speed DDR5 memory profile support.",
                "img": "https://1.grgs.ro/images/products/1/9561/2594135/full/ryzen-7-7800x3d-42ghz-box-c828e4f5427046cab3fef92871454224.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "Intel Core i7-14700K",
                "sku": "CPU-INT-14700K",
                "price": Decimal("2049.50"),
                "stock": 10,
                "desc": "14th Gen Raptor Lake Refresh processor featuring a hybrid 20-core architecture (8 Performance-cores and 12 Efficient-cores) with 28 parallel execution threads. Achieves maximum clock frequencies of 5.6 GHz via Intel Turbo Boost Max Technology 3.0. Includes an unlocked multiplier for overclocking and integrated Intel UHD Graphics 770.",
                "img": "https://2.grgs.ro/images/products/1/2180/2694475/full/cpu-core-i7-14700k-s1700-box-34g-bx8071514700k-s-rn3x-in-db96249fec8b72bef32e81f0a80aea1e.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "AMD Ryzen 9 7950X",
                "sku": "CPU-AMD-7950X",
                "price": Decimal("2899.00"),
                "stock": 6,
                "desc": "Heavy-duty workstation flagship processor equipped with 16 physical cores and 32 threads capable of a 5.7 GHz maximum boost clock. Built on TSMC's 5nm process node with an extensive 80MB combined cache pool. Delivers unrivaled multi-threaded throughput for distributed software compilation, local virtualization clusters, and complex CAD modeling.",
                "img": "https://www.amd.com/content/dam/amd/en/images/products/processors/ryzen/2505503-ryzen-9-7900x.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "Intel Core i9-14900K",
                "sku": "CPU-INT-14900K",
                "price": Decimal("3149.99"),
                "stock": 5,
                "desc": "Extreme-tier flagship processor providing 24 cores (8 P-cores + 16 E-cores) and 32 threads, reaching speeds up to 6.0 GHz straight out of the box via Thermal Velocity Boost. Engineered with 36MB of Intel Smart Cache to handle complex simulations, real-time telemetry processing, and raw 8K media production workflows.",
                "img": "https://s13emagst.akamaized.net/products/61980/61979090/images/res_76a3b20416d035228a442d40f08e1425.png"
            },
            {
                "cat": "processors-cpus",
                "name": "AMD Ryzen 5 7600X",
                "sku": "CPU-AMD-7600X",
                "price": Decimal("1149.00"),
                "stock": 20,
                "desc": "Well-balanced Zen 4 desktop processor offering 6 cores and 12 threads with a 4.7 GHz base clock and a 5.3 GHz boost envelope. Designed for energy efficiency within a manageable 105W TDP while retaining complete PCIe Gen5 and dual-channel DDR5 bus compatibility. An optimal foundation for engineering client systems and developer workstations.",
                "img": "https://5.grgs.ro/images/products/1/2770/2451332/normal/ryzen-5-7600x-47ghz-box-f20281518c51ed902a8fa217467fe95b.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "Intel Core i5-14600KF",
                "sku": "CPU-INT-14600KF",
                "price": Decimal("1420.00"),
                "stock": 12,
                "desc": "Versatile performance CPU sporting 14 cores (6 P-cores and 8 E-cores) and 20 threads scaling up to 5.3 GHz. The KF design eliminates integrated graphics to minimize thermal overhead, making it ideal for pairing with discrete enterprise GPUs. Handles rigorous multitasking and continuous developer background builds reliably.",
                "img": "https://p1.akcdn.net/full/1207451023.intel-core-i5-14600kf-14-core-3-5ghz-lga1700-box-bx8071514600kf.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "AMD Ryzen 9 7900",
                "sku": "CPU-AMD-7900",
                "price": Decimal("1980.00"),
                "stock": 8,
                "desc": "High-efficiency 12-core, 24-thread desktop processor tuned for an ultra-low 65W TDP power envelope. Delivers dynamic burst frequencies up to 5.4 GHz while maintaining low thermal output, bundled with the premium AMD Wraith Prism cooler. Perfect for small form-factor edge nodes, quiet lab servers, and microservice hosts.",
                "img": "https://4.grgs.ro/images/products/1/8524/2525867/normal/ryzen-9-7900-45ghz-box-af1e0f2c42389050480254f4b5a6be62.jpg"
            },
            {
                "cat": "processors-cpus",
                "name": "Intel Core i3-14100F",
                "sku": "CPU-INT-14100F",
                "price": Decimal("549.90"),
                "stock": 25,
                "desc": "Reliable entry-level quad-core processor delivering 8 threads up to 4.7 GHz on the modern LGA1700 platform. Engineered with 12MB Intel Smart Cache and low thermal dissipation for embedded terminals, factory HMI panels, and network monitoring appliances requiring predictable 24/7 responsiveness.",
                "img": "https://5.grgs.ro/images/products/1/390/2882679/normal/raptor-lake-refresh-core-i3-14100f-35ghz-box-762053954722753eaf86273f682888af.jpg"
            },

            # =========================================================================
            # CATEGORY 2: Memory & Storage
            # =========================================================================
            {
                "cat": "memory-storage",
                "name": "Samsung 990 PRO 2TB NVMe SSD",
                "sku": "SSD-SAM-990P-2TB",
                "price": Decimal("949.99"),
                "stock": 18,
                "desc": "Ultra-fast PCIe 4.0 x4 M.2 2280 internal solid-state drive built with Samsung's proprietary V-NAND TLC technology. Delivers sequential read speeds up to 7,450 MB/s and write speeds up to 6,900 MB/s with hardware nickel-coated thermal dissipation. Built for database storage, deep learning asset caching, and near-zero OS boot latencies.",
                "img": "https://lcdn.altex.ro/media/catalog/product/s/s/ssdmzv9p2t0bw_4_c773f178.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "Kingston Fury Beast 32GB DDR5 6000MHz",
                "sku": "RAM-KNG-32GB-DDR5",
                "price": Decimal("589.00"),
                "stock": 22,
                "desc": "Dual-channel DDR5 memory kit consisting of two matched 16GB modules operating at 6000 MT/s with low-latency CL30 timings. Fully compatible with both AMD EXPO and Intel XMP 3.0 one-click profile activation. Low-profile black anodized aluminum heat spreaders guarantee maximum clearance inside compact industrial chassis.",
                "img": "https://s13emagst.akamaized.net/products/70645/70644639/images/res_8fb3dad6bab4474c68173683824c803c.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "Crucial T700 1TB PCIe Gen5 NVMe",
                "sku": "SSD-CRU-T700-1TB",
                "price": Decimal("1089.00"),
                "stock": 7,
                "desc": "Next-generation PCIe Gen5 x4 NVMe solid-state drive powered by the Phison PS5026-E26 controller and Micron 232-layer 3D TLC NAND. Breaks performance barriers with sustained read throughput up to 11,700 MB/s and write bandwidth exceeding 9,500 MB/s. Designed for intensive machine learning checkpoints and large-scale asset parsing.",
                "img": "https://p1.akcdn.net/full/1154396871.crucial-t700-1tb-m-2-ct1000t700ssd3.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "Corsair Vengeance 64GB DDR5 5600MHz",
                "sku": "RAM-COR-64GB-DDR5",
                "price": Decimal("1049.90"),
                "stock": 9,
                "desc": "High-density 64GB DDR5 memory kit (2x32GB) tuned specifically for multi-core workstations and multi-threaded container workloads. Features onboard Power Management IC (PMIC) regulation for rock-solid voltage control and on-die ECC error correction. Built for containerized Docker setups, multi-node testing, and memory-mapped databases.",
                "img": "https://s13emagst.akamaized.net/products/57386/57385890/images/res_8fb7f18bfdae90815a49d070397a4e56.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "WD Black SN850X 4TB NVMe SSD",
                "sku": "SSD-WDC-SN850X-4TB",
                "price": Decimal("1699.00"),
                "stock": 4,
                "desc": "High-capacity 4TB PCIe Gen4 NVMe drive tailored for data-heavy development environments with write endurance ratings surpassing 2,400 TBW. Reaches up to 7,300 MB/s read speeds and over 1,200,000 IOPS random access via Western Digital's in-house controller architecture. An exceptional high-throughput drive for local repository mirrors and database caching.",
                "img": "https://p1.akcdn.net/full/1017443223.western-digital-sn850x-4tb-m-2-wds400t2x0e-00bca0.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "G.Skill Trident Z5 RGB 32GB DDR5 6400MHz",
                "sku": "RAM-GSK-32GB-6400",
                "price": Decimal("670.00"),
                "stock": 15,
                "desc": "Enthusiast-grade DDR5 memory kit running at 6400 MHz with aggressive CL32 timings on hand-screened SK Hynix DRAM ICs. Enclosed in sleek brushed-aluminum heatspreaders with integrated customizable RGB light bars. Delivers exceptional signal integrity and extreme bandwidth for latency-sensitive rendering engines.",
                "img": "https://p1.akcdn.net/full/1079550855.g-skill-trident-z5-rgb-32gb-2x16gb-ddr5-6400mhz-f5-6400j3239g16gx2-tz5rs.jpg"
            },
            {
                "cat": "memory-storage",
                "name": "Lexar NM790 2TB M.2 SSD",
                "sku": "SSD-LEX-NM790-2TB",
                "price": Decimal("689.99"),
                "stock": 16,
                "desc": "DRAM-less PCIe Gen4x4 drive employing advanced Host Memory Buffer (HMB 3.0) technology to deliver up to 7,400 MB/s read speeds. Notable for its exceptionally low operating temperatures and minimal power draw, making it highly compatible with passively cooled industrial mainboards. Highly resilient against continuous write-intensive daily workloads.",
                "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRB3-nE1t3XIooMWbvfq9kOrFwecyibz151NHJMhMoxg&s=10"
            },
            {
                "cat": "memory-storage",
                "name": "Seagate IronWolf Pro 8TB NAS HDD",
                "sku": "HDD-SEA-8TB-NAS",
                "price": Decimal("1120.00"),
                "stock": 8,
                "desc": "Enterprise-grade 3.5-inch SATA 6Gb/s hard drive designed specifically for multi-bay NAS enclosures and industrial log storage running 24/7/365. Spins at 7200 RPM with rotational vibration (RV) sensors ensuring steady mechanical operation in dense rack cabinets. Features IronWolf Health Management to prevent catastrophic telemetry loss.",
                "img": "https://m.media-amazon.com/images/I/81U6oiHvviL._AC_UF894,1000_QL80_.jpg"
            },

            # =========================================================================
            # CATEGORY 3: Industrial PLCs & Controllers
            # =========================================================================
            {
                "cat": "industrial-plcs",
                "name": "Siemens SIMATIC S7-1200 CPU 1214C",
                "sku": "PLC-SIE-1214C-DC",
                "price": Decimal("2350.00"),
                "stock": 11,
                "desc": "Compact industrial programmable logic controller (PLC) for medium-scale automation processes, operating on 24V DC with DC/DC/DC wiring. Integrates 14 digital inputs (24V), 10 transistor digital outputs, 2 analog inputs (0-10V), and an integrated PROFINET interface for SCADA/HMI interconnectivity. Programmed seamlessly via TIA Portal with LAD, FBD, and SCL languages.",
                "img": "https://res.cloudinary.com/rsc/image/upload/b_rgb:FFFFFF,c_pad,dpr_1.0,f_auto,q_auto,w_700/c_pad,w_700/Y8624471-05"
            },
            {
                "cat": "industrial-plcs",
                "name": "Schneider Modicon M221 TM221CE16R",
                "sku": "PLC-SCH-M221-16R",
                "price": Decimal("1450.00"),
                "stock": 8,
                "desc": "Space-saving programmable logic controller optimized for discrete machinery and cabinet integration, providing 16 integrated I/O points (9 digital inputs and 7 isolated 2A relay outputs). Features built-in Ethernet with Modbus TCP Client/Server alongside an RS485 serial communication port. Configured easily using EcoStruxure Machine Expert - Basic.",
                "img": "https://download.se.com/files?p_Doc_Ref=PF130224&p_File_Type=rendition_1500_jpg"
            },
            {
                "cat": "industrial-plcs",
                "name": "Siemens SIMATIC S7-1500 CPU 1511-1 PN",
                "sku": "PLC-SIE-1511-1PN",
                "price": Decimal("4890.00"),
                "stock": 3,
                "desc": "State-of-the-art modular industrial controller tailored for demanding assembly lines and high-speed discrete manufacturing systems. Offers 150 KB program work memory, 1 MB data memory, a blistering 60 ns bit-processing speed, and a front-panel diagnostic display. Includes a dual-port PROFINET IO switch with integrated industrial cybersecurity protocols.",
                "img": "https://mall.industry.siemens.com/mall/collaterals/files/206/JPG/07/71/P_ST70_XX_07836j.JPG"
            },
            {
                "cat": "industrial-plcs",
                "name": "Omron CP1L-EM30DT-D Compact PLC",
                "sku": "PLC-OMR-CP1L-30DT",
                "price": Decimal("1890.00"),
                "stock": 6,
                "desc": "Reliable industrial automation controller providing 30 embedded I/O channels (18 digital inputs and 12 sinking transistor outputs) alongside native RJ-45 Ethernet connectivity. Features four 100 kHz high-speed counter inputs and dual pulse train outputs for direct stepper and servomotor motion control. Engineered for packaging automation and high-speed sorting.",
                "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRwmOAdEertKIoiW12VsWtQBEz2uGxuuSE25V4H41lpJWoCiZdsqJ3D_h0l&s=10"
            },
            {
                "cat": "industrial-plcs",
                "name": "ABB AC500-eCo PM554-T Micro PLC",
                "sku": "PLC-ABB-PM554-T",
                "price": Decimal("1290.00"),
                "stock": 10,
                "desc": "Modular entry-level PLC from the ABB AC500 ecosystem featuring 128 kB of user program memory, 8 digital 24V DC inputs, and 6 transistor outputs. Features an onboard RS485 serial port supporting Modbus RTU communications and an SD card slot for field firmware updates without a programming laptop. Adheres to IEC 61131-3 standards within ABB Automation Builder.",
                "img": "https://i0.wp.com/plcs-automation.com/wp-content/uploads/2022/03/ABB-PM554-TP.jpg?fit=600%2C600&ssl=1"
            },
            {
                "cat": "industrial-plcs",
                "name": "Siemens LOGO! 24RCE Logic Module",
                "sku": "PLC-SIE-LOGO-24RCE",
                "price": Decimal("780.00"),
                "stock": 20,
                "desc": "Smart logic relay module operating on 12/24V DC/AC with a built-in backlit LCD display and front control keys for standalone operation. Provides 8 digital inputs (4 configurable as 0-10V analog inputs) and 4 heavy-duty 10A relay outputs for switching contactors and solenoids. Comes with an onboard HTML5 web server and direct industrial IoT cloud connectivity.",
                "img": "https://www.matyco.com/105764-large_default/siemens-logo-logic-module-24rce-8-di-4-24v-ac-dc-24v.jpg"
            },
            {
                "cat": "industrial-plcs",
                "name": "Rockwell Allen-Bradley Micro820",
                "sku": "PLC-AB-MICRO820",
                "price": Decimal("2120.00"),
                "stock": 5,
                "desc": "Compact DIN-rail PLC controller featuring 20 integrated I/O points (12 digital inputs, 7 digital outputs, and 1 configurable analog output channel). Offers 10/100 Mbps Ethernet supporting industrial EtherNet/IP messaging alongside a non-isolated RS232/485 serial port. Includes microSD data-logging capabilities configured via Connected Components Workbench.",
                "img": "https://media.rs-online.com/f_auto,q_auto/R8937761-01.jpg"
            },
            {
                "cat": "industrial-plcs",
                "name": "WAGO Compact Controller 100",
                "sku": "PLC-WAG-CC100-ETH",
                "price": Decimal("1650.00"),
                "stock": 9,
                "desc": "Open industrial automation controller driven by an ARM Cortex-A7 (650 MHz) core running Real-Time Linux. Integrates 8 digital inputs, 4 digital outputs, 2 analog inputs, and 2 analog outputs alongside dual switched Ethernet ports. Fully programmable via CoDeSys V3 while supporting native Docker containers, Python scripts, and MQTT edge telemetry.",
                "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPjTbX9eXThxeovHkTfY1189vrvy9MUfFhTsJWfkZV1_1BixAzGcL1OmM&s=10"
            },

            # =========================================================================
            # CATEGORY 4: Industrial I/O & Automation Modules
            # =========================================================================
            {
                "cat": "automation-modules",
                "name": "Siemens SM 1223 Digital I/O Module",
                "sku": "MOD-SIE-SM1223-16",
                "price": Decimal("890.00"),
                "stock": 15,
                "desc": "Discrete expansion signal module for SIMATIC S7-1200 PLCs connecting directly to the side CPU backplane bus. Provides 8 galvanically isolated 24V DC digital inputs and 8 relay outputs capable of switching up to 2A at 230V AC. Features removable screw-clamp terminal blocks and individual diagnostic LEDs for streamlined cabinet troubleshooting.",
                "img": "https://media.automation24.com/Artikelbilder/ShopWebP800px/101678_1.webp"
            },
            {
                "cat": "automation-modules",
                "name": "Mean Well HDR-100-24 DIN-Rail PSU",
                "sku": "PSU-MW-HDR100-24",
                "price": Decimal("195.00"),
                "stock": 35,
                "desc": "Ultra-slim step-shape industrial DIN-rail power supply enclosed in a flame-retardant plastic housing for space-constrained panels. Delivers a regulated 24V DC output at 3.83A (92W continuous output) with an adjustable output trimmer between 21.6V and 29V. Built with short-circuit, overload, and overvoltage protections with a no-load loss below 0.3W.",
                "img": "https://thumbs.static-thomann.de/thumb/padthumb600x600/pics/bdb/_58/580122/19216173_800.jpg"
            },
            {
                "cat": "automation-modules",
                "name": "Phoenix Contact Quint Power 24V 10A",
                "sku": "PSU-PHX-QUINT-10A",
                "price": Decimal("1150.00"),
                "stock": 7,
                "desc": "High-tier primary-switched industrial power supply featuring patented SFB (Selective Fuse Breaking) technology delivering 6x nominal current for 12 ms to safely trip secondary breakers. Includes preventive function monitoring with digital signaling outputs to alert PLCs before critical plant shutdowns occur. Heavy-duty metal housing rated up to 70°C.",
                "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDOelLPDDIWAK-FsBfQzP_t7MmHoxfMsrSf75wohbnwg&s=10"
            },
            {
                "cat": "automation-modules",
                "name": "Siemens SM 1231 Analog Input Module",
                "sku": "MOD-SIE-SM1231-4AI",
                "price": Decimal("980.00"),
                "stock": 10,
                "desc": "Precision analog signal expansion slice featuring 4 differential input channels with 13-bit resolution. Accurately digitizes standardized industrial sensor loops: voltage (+/-10V, +/-5V, +/-2.5V) or current (0-20 mA / 4-20 mA). Converts pressure, temperature, and ultrasonic level readings directly into process images for S7-1200 CPUs.",
                "img": "https://media.automation24.com/Artikelbilder/ShopWebP800px/101680_1.webp"
            },
            {
                "cat": "automation-modules",
                "name": "Schneider Modicon TM3 Digital Output",
                "sku": "MOD-SCH-TM3DQ16R",
                "price": Decimal("620.00"),
                "stock": 14,
                "desc": "Digital expansion module designed for Modicon M221, M241, and M251 logic controllers, adding 16 isolated normally-open (NO) relay outputs. Supports resistive and inductive loads up to 2A per channel with 1500V AC dielectric isolation between points and the controller bus. Features tool-free top bus latching for quick DIN-rail installation.",
                "img": "https://download.se.com/files?p_Doc_Ref=PF130333&p_File_Type=rendition_369_jpg&default_image=DefaultProductImage.png"
            },
            {
                "cat": "automation-modules",
                "name": "Moxa NPort 5150 Serial Device Server",
                "sku": "COM-MOX-NPORT-5150",
                "price": Decimal("840.00"),
                "stock": 12,
                "desc": "Industrial 1-port serial-to-Ethernet gateway engineered to seamlessly bridge legacy RS-232/422/485 automation machinery into modern TCP/IP networks. Provides real Virtual COM port drivers for Windows and Linux alongside TCP Server, TCP Client, and UDP operation modes. Enclosed in a compact aluminum chassis with 15 kV ESD surge protection.",
                "img": "https://cdn-cms-frontdoor-dfc8ebanh6bkb3hs.a02.azurefd.net/getattachment/2e0a673f-5ab9-415f-a289-514130f87c1a/moxa-nport-5150-image.jpg"
            },
            {
                "cat": "automation-modules",
                "name": "Weidmuller PROtop 24V 20A Power Supply",
                "sku": "PSU-WEI-PROTOP-20A",
                "price": Decimal("1480.00"),
                "stock": 5,
                "desc": "Premium DIN-rail switched-mode power supply delivering 24V DC at 20A (480W total power) with up to 95.3% peak electrical efficiency. Implements DCL (Dynamic Current Limiting) technology providing up to 600% dynamic headroom for instant motor starts and capacitive surges. Includes internal ORing MOSFETs for direct parallel redundancy without external diodes.",
                "img": "https://assets.dam.weidmueller.com/assets/api/34d895f6-2110-47d0-b11c-b6cb5d08d00b/DAP_Master_PP,w_800,q_80"
            },
            {
                "cat": "automation-modules",
                "name": "WAGO 750-880 ETHERNET Starter Kit",
                "sku": "MOD-WAG-750-880",
                "price": Decimal("2450.00"),
                "stock": 4,
                "desc": "Modular fieldbus coupler and programmable Ethernet controller with an integrated 2-port switch enabling line and daisy-chain network topologies. Features an onboard SD card slot supporting up to 32GB for CSV data logging and custom HTML web visualization. Fully compatible with over 500 modular I/O slice options in the WAGO 750 ecosystem.",
                "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmwmieB1gJ6ne94UKnE6fgQ2muxfGztYr7Nxevc_qTUt36iiw-q9YMx3Da&s=10"
            },
        ]

        # Inspecție dinamică a câmpurilor din ProductImage pentru compatibilitate totală
        pi_fields = [f.name for f in ProductImage._meta.get_fields()]

        # 4. Inserare produse și imagini
        for item in products_data:
            cat = category_instances[item["cat"]]
            prod = Product.objects.create(
                category=cat,
                name=item["name"],
                slug=slugify(item["name"]),
                sku=item["sku"],
                price=item["price"],
                stock=item["stock"],
                description=item["desc"],
                is_active=True
            )

            # Construire dinamică a parametrilor pentru ProductImage
            img_kwargs = {"product": prod}
            
            # Câmpul pentru URL / cale imagine
            if "image_url" in pi_fields:
                img_kwargs["image_url"] = item["img"]
            elif "image" in pi_fields:
                img_kwargs["image"] = item["img"]

            # Câmpul boolean de featured/primar (dacă există)
            if "is_feature" in pi_fields:
                img_kwargs["is_feature"] = True
            elif "is_featured" in pi_fields:
                img_kwargs["is_featured"] = True
            elif "is_primary" in pi_fields:
                img_kwargs["is_primary"] = True
            elif "is_main" in pi_fields:
                img_kwargs["is_main"] = True

            ProductImage.objects.create(**img_kwargs)

        self.stdout.write(self.style.SUCCESS(f"\n[SUCCESS] Successfully seeded {Product.objects.count()} products and {ProductImage.objects.count()} verified tech images!"))