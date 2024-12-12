import sqlite3
import csv
import qrcode
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import tkinter as tk
from tkinter import messagebox, filedialog


# Database setup and initialization
def initialize_db():
    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ticket_number TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            time TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Generate QR Code and Barcode and save ticket as PDF
def generate_ticket_pdf(ticket_info):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add Ticket Header
    pdf.cell(200, 10, txt="PyEvents - Event Ticket", ln=True, align='C')
    pdf.ln(10)

    # Add Name and Ticket Number
    pdf.cell(200, 10, txt=f"Name: {ticket_info['Name']}", ln=True)
    pdf.cell(200, 10, txt=f"Ticket Number: {ticket_info['Ticket Number']}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {ticket_info['Status']}", ln=True)
    pdf.cell(200, 10, txt=f"Time: {ticket_info['Time']}", ln=True)

    # Validate the ticket number length (12 digits for EAN-13)
    ticket_number = ticket_info['Ticket Number']
    if len(ticket_number) != 12:
        messagebox.showerror("Invalid Ticket Number", "Ticket number must be 12 digits for EAN-13 barcode.")
        return

    # Generate Barcode (EAN-13 Format)
    try:
        barcode_format = barcode.get_barcode_class('ean13')
        barcode_image = barcode_format(ticket_number, writer=ImageWriter())
        barcode_filename = f"barcode_{ticket_number}.png"
        barcode_image.save(barcode_filename)
    except barcode.errors.NumberOfDigitsError:
        messagebox.showerror("Invalid Barcode", "The ticket number is invalid for EAN-13 barcode.")
        return

    # Add Barcode Image to PDF
    pdf.ln(10)
    pdf.image(barcode_filename, x=10, w=80)  # Adjust size as needed

    # Generate QR Code
    qr = qrcode.make(ticket_number)
    qr_filename = f"qr_{ticket_number}.png"
    qr.save(qr_filename)

    # Add QR Code to PDF
    pdf.ln(10)
    pdf.image(qr_filename, x=10, w=50)  # Adjust size as needed

    # Output PDF File
    ticket_pdf_filename = f"ticket_{ticket_number}.pdf"
    pdf.output(ticket_pdf_filename)
    messagebox.showinfo("Ticket Saved", f"Ticket saved as {ticket_pdf_filename}")

# Export Attendance Data to CSV
def export_to_csv():
    filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not filename:
        return
    
    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, ticket_number, status, time FROM participants")
    data = cursor.fetchall()
    
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Ticket Number", "Status", "Time"])
        writer.writerows(data)
    
    conn.close()
    messagebox.showinfo("Export Successful", f"Data exported to {filename}")

# Export Attendance Data to PDF
def export_to_pdf():
    filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not filename:
        return
    
    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, ticket_number, status, time FROM participants")
    data = cursor.fetchall()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Attendance Report", ln=True, align='C')
    pdf.ln(10)  # Line break

    for record in data:
        line = f"Name: {record[0]}, Ticket Number: {record[1]}, Status: {record[2]}, Time: {record[3]}"
        pdf.cell(0, 10, txt=line, ln=True)

    pdf.output(filename)
    conn.close()
    messagebox.showinfo("Export Successful", f"Data exported to {filename}")

# Kiosk Mode Window
def kiosk_mode():
    root = tk.Tk()
    root.title("PyEvents - Kiosk Mode")
    root.attributes("-fullscreen", True)  # Enable full-screen mode

    def exit_kiosk():
        if messagebox.askyesno("Exit", "Are you sure you want to exit kiosk mode?"):
            root.attributes("-fullscreen", False)  # Exit full-screen mode
            root.destroy()

    tk.Label(root, text="Welcome to PyEvents", font=("Arial", 24)).pack(pady=20)
    tk.Label(root, text="Scan your QR code or enter Ticket Number to check-in.", font=("Arial", 16)).pack(pady=10)
    
    # Input for barcode number
    ticket_entry = tk.Entry(root, font=("Arial", 18), width=20)
    ticket_entry.pack(pady=20)

    def check_in():
        ticket_number = ticket_entry.get()
        if ticket_number:
            conn = sqlite3.connect('participants.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, status FROM participants WHERE ticket_number=?", (ticket_number,))
            ticket_info = cursor.fetchone()
            conn.close()

            if ticket_info:
                messagebox.showinfo("Checked In", f"Welcome {ticket_info[0]}! Status: {ticket_info[1]}")
            else:
                messagebox.showerror("Invalid Ticket", "Ticket number not found.")
        else:
            messagebox.showwarning("Input Required", "Please enter a ticket number.")

    tk.Button(root, text="Check-In", command=check_in, width=20, bg="green", fg="white").pack(pady=5)
    tk.Button(root, text="Exit Kiosk Mode", command=exit_kiosk, width=20, bg="red", fg="white").pack(pady=20)

    root.mainloop()

# Create Participant Window
def create_participant():
    def save_participant():
        name = name_entry.get()
        ticket_number = ticket_number_entry.get()
        status = status_var.get()

        if not name or not ticket_number:
            messagebox.showwarning("Input Required", "Please enter both Name and Ticket Number.")
            return

        # Save new participant to database
        conn = sqlite3.connect('participants.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO participants (name, ticket_number, status, time) VALUES (?, ?, ?, ?)",
                       (name, ticket_number, status, ""))
        conn.commit()
        conn.close()

        # Generate and save the PDF ticket
        new_participant = {
            "Name": name,
            "Ticket Number": ticket_number,
            "Status": status,
            "Time": "",
        }
        generate_ticket_pdf(new_participant)

        messagebox.showinfo("Participant Added", f"{name} added successfully!")

        # Close window after saving
        new_participant_window.destroy()

    # Create the new participant window
    new_participant_window = tk.Toplevel()
    new_participant_window.title("Create New Participant")

    tk.Label(new_participant_window, text="Name:").pack(pady=5)
    name_entry = tk.Entry(new_participant_window, font=("Arial", 14))
    name_entry.pack(pady=5)

    tk.Label(new_participant_window, text="Ticket Number:").pack(pady=5)
    ticket_number_entry = tk.Entry(new_participant_window, font=("Arial", 14))
    ticket_number_entry.pack(pady=5)

    tk.Label(new_participant_window, text="Status:").pack(pady=5)
    status_var = tk.StringVar(value="Absent")
    status_menu = tk.OptionMenu(new_participant_window, status_var, "Absent", "Here", "Excluded", "Travel")
    status_menu.pack(pady=5)

    save_button = tk.Button(new_participant_window, text="Save Participant", command=save_participant, width=20, bg="green", fg="white")
    save_button.pack(pady=20)

# Main Menu
def main():
    root = tk.Tk()
    root.title("PyEvents")

    tk.Button(root, text="Create New Participant", command=create_participant, width=20, bg="blue", fg="white").pack(pady=5)
    tk.Button(root, text="Export to CSV", command=export_to_csv, width=20, bg="green", fg="white").pack(pady=5)
    tk.Button(root, text="Export to PDF", command=export_to_pdf, width=20, bg="green", fg="white").pack(pady=5)
    tk.Button(root, text="Kiosk Mode", command=kiosk_mode, width=20, bg="orange", fg="white").pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    initialize_db()
    main()