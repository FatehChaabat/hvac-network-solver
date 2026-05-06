from fpdf import FPDF
from datetime import datetime
import os

class DuctReport(FPDF):
    def header(self):
        # On n'affiche le header complet que sur la page 1
        if self.page_no() == 1:
            self.set_font("Helvetica", "B", 20)
            self.set_text_color(0, 0, 0)  # Titre principal en NOIR
            self.cell(0, 15, "TECHNICAL REPORT: AIRFLOW SIMULATION", ln=True, align='C')
            
            # Ligne de soulignement noire UNIQUEMENT pour le titre principal
            self.set_draw_color(0, 0, 0)
            self.line(30, self.get_y(), 180, self.get_y())
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} | Generated on {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C")

def export_to_pdf(results, filename="report_aeraulique.pdf", image_path=None):
    pdf = DuctReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Configuration des couleurs
    COLOR_TITLE = (0, 153, 51) # VERT
    COLOR_BG = (240, 240, 240) 
    
    # Largeurs des colonnes pour tables 1 et 3
    col_w_label = 90
    col_w_val = 95

    # --- TABLE 1: NETWORK SUMMARY ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 10, "1. NETWORK SUMMARY", ln=True) # Soulignement supprimé ici
    pdf.ln(2)
    
    # En-tête Table 1
    pdf.set_fill_color(*COLOR_BG)
    pdf.set_font("Helvetica", "B", 11) 
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_w_label, 10, " Parameter", 1, 0, "L", True)
    pdf.cell(col_w_val, 10, " Value", 1, 1, "L", True)

    UNIT_MAP = {"m3h": "(m3/h)", "pa": "(Pa)", "watts": "(W)", "euros": "(EUR)"}
    
    for k, v in results["summary"].items():
        parts = k.rsplit("_", 1)
        if len(parts) > 1 and parts[1].lower() in UNIT_MAP:
            label = f" {parts[0].replace('_', ' ').capitalize()} {UNIT_MAP[parts[1].lower()]}"
        else:
            label = f" {k.replace('_', ' ').capitalize()}"
        
        pdf.set_font("Helvetica", "B", 11) 
        pdf.cell(col_w_label, 9, label, 1)
        pdf.set_font("Helvetica", "", 11) 
        pdf.cell(col_w_val, 9, f" {v}", 1, ln=True)

    pdf.ln(10)

    # --- TABLE 2: DUCT DETAILS ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 10, "2. DUCT DETAILS", ln=True) # Soulignement supprimé ici
    pdf.ln(2)
    
    # En-tête Table 2
    pdf.set_fill_color(*COLOR_BG)
    pdf.set_font("Helvetica", "B", 10) 
    pdf.set_text_color(0, 0, 0)
    
    w = [60, 40, 40, 45] 
    pdf.cell(w[0], 10, " Duct name", 1, 0, "L", True)
    pdf.cell(w[1], 10, "Air flow (m3/h)", 1, 0, "C", True)
    pdf.cell(w[2], 10, "Velocity (m/s)", 1, 0, "C", True)
    pdf.cell(w[3], 10, "Pressure loss (Pa)", 1, 1, "C", True)

    # Données
    for d in results["results"]:
        pdf.set_font("Helvetica", "B", 10) 
        pdf.cell(w[0], 9, f" {d['duct']}", 1)
        pdf.set_font("Helvetica", "", 10) 
        pdf.cell(w[1], 9, f"{d['flow_m3h']:.1f}", 1, 0, "C")
        pdf.cell(w[2], 9, f"{d['velocity_ms']:.2f}", 1, 0, "C")
        pdf.cell(w[3], 9, f"{d['delta_p_pa']:.2f}", 1, 1, "C")

    pdf.ln(10)

    # --- TABLE 3: SOLVER METADATA ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 10, "3. SOLVER METADATA", ln=True) # Soulignement supprimé ici
    pdf.ln(2)
    
    # En-tête Table 3
    pdf.set_fill_color(*COLOR_BG)
    pdf.set_font("Helvetica", "B", 11) 
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_w_label, 10, " Performance Metric", 1, 0, "L", True)
    pdf.cell(col_w_val, 10, " Result", 1, 1, "L", True)

    meta_units = {"sec": "(s)", "m3s": "(m3/s)"}
    
    for k, v in results["solver_metadata"].items():
        parts = k.rsplit("_", 1)
        if len(parts) > 1 and parts[1] in meta_units:
            label = f" {parts[0].replace('_', ' ').capitalize()} {meta_units[parts[1]]}"
        else:
            label = f" {k.replace('_', ' ').capitalize()}"

        pdf.set_font("Helvetica", "B", 11) 
        pdf.cell(col_w_label, 9, label, 1)
        pdf.set_font("Helvetica", "", 11) 
        pdf.cell(col_w_val, 9, f" {str(v)}", 1, ln=True)

    # --- 4. NETWORK DIAGRAM ---
    if image_path:
        # Vérification de l'espace restant (210mm est la hauteur A4 standard)
        # Si on est déjà en bas de page (y > 150), on change de page
        if pdf.get_y() > 150:
            pdf.add_page()
        else:
            pdf.ln(10) # Juste un petit espace si on reste sur la même page

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*COLOR_TITLE) # VERT
        pdf.cell(0, 10, "4. NETWORK DIAGRAM", ln=True, align='L')
        pdf.ln(5)
        
        # Insertion de l'image
        # On ajuste 'w' pour qu'elle tienne bien
        pdf.image(image_path, x=10, y=None, w=190)

    pdf.output(filename)
    print(f"✅ PDF généré avec succès : {filename}")






def print_console_report(results):
    """Affiche le rapport formaté directement dans le terminal."""
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    END = "\033[0m"

    # --- SECTION 1: NETWORK SUMMARY ---
    print(f"\n{BOLD}{GREEN}===== 1. NETWORK SUMMARY ====={END}")
    # Liste blanche des unités
    UNIT_MAP = {
        "m3h": "(m3/h)",
        "pa": "(Pa)",
        "watts": "(W)",
        "euros": "(€)"
    }

    for k, v in results["summary"].items():
        parts = k.rsplit("_", 1)
        if len(parts) > 1 and parts[1].lower() in UNIT_MAP:
            label = parts[0].replace("_", " ").capitalize()
            unit_str = UNIT_MAP[parts[1].lower()]
            display_key = f"{label} {unit_str}"
        else:
            display_key = k.replace("_", " ").capitalize()
        print(f"   {display_key:<35}: {v}")

    # --- SECTION 2: DUCT DETAILS ---
    print(f"\n{BOLD}{GREEN}===== 2. DUCT DETAILS ====={END}")
    w_name = 25  
    w_flow = 18  
    w_vel  = 18 
    w_loss = 20  
    
    header = (
        f"   {'Duct name':<{w_name}} | "
        f"{'Air flow (m3/h)':<{w_flow}} | "
        f"{'Velocity (m/s)':<{w_vel}} | "
        f"{'Pressure loss (Pa)':<{w_loss}}"
    )
    print(header)
    print("   " + "-" * (len(header) - 3))

    for d in results["results"]:
        print(
            f"   {d['duct']:<{w_name}} | "
            f"{d['flow_m3h']:^{w_flow}.1f} | "
            f"{d['velocity_ms']:^{w_vel}.2f} | "
            f"{d['delta_p_pa']:^{w_loss}.2f}"
        )

    # --- SECTION 3: SOLVER METADATA ---
    print(f"\n{BOLD}{GREEN}===== 3. SOLVER METADATA ====={END}")
    unit_map_meta = {
        "sec": "(s)",
        "m3s": "(m3/s)"
    }

    for k, v in results["solver_metadata"].items():
        parts = k.rsplit("_", 1)
        if len(parts) > 1 and parts[1] in unit_map_meta:
            label = parts[0].replace("_", " ").capitalize()
            unit = unit_map_meta[parts[1]]
            display_key = f"{label} {unit}"
        else:
            display_key = k.replace("_", " ").capitalize()
            
        print(f"   {display_key:<35}: {v}")
    
    print("\n" + "=" * 80 + "\n")