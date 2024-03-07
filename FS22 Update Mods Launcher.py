import os
import ftplib
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import keyring
import threading
from tkinter import ttk

class FTPDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("FS22 Mods Updater")
        self.root.geometry("385x385")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure('TButton', font=('calibri', 10, 'bold'), foreground='blue') 

        self.host_label = ttk.Label(root, text="Hôte FTP :")
        self.host_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.host_entry = ttk.Entry(root)
        self.host_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.port_label = ttk.Label(root, text="Port :")
        self.port_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.port_entry = ttk.Entry(root)
        self.port_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.username_label = ttk.Label(root, text="Nom d'utilisateur :")
        self.username_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = ttk.Entry(root)
        self.username_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.password_label = ttk.Label(root, text="Mot de passe :")
        self.password_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ttk.Entry(root, show="*")
        self.password_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.save_var = tk.BooleanVar()
        self.save_checkbox = ttk.Checkbutton(root, text="Mémoriser les informations de connexion", variable=self.save_var)
        self.save_checkbox.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.folder_label = ttk.Label(root, text="Dossier local :")
        self.folder_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.folder_entry = ttk.Entry(root)
        self.folder_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
        self.browse_button = ttk.Button(root, text="Parcourir", command=self.browse_folder)
        self.browse_button.grid(row=5, column=2, padx=10, pady=10)

        self.connect_button = ttk.Button(root, text="Lancer la mise à jour des mods", command=self.start_download)
        self.connect_button.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        self.cancel_button = ttk.Button(root, text="Annuler le téléchargement", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        self.progress_label = ttk.Label(root, text="")
        self.progress_label.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        self.cancel = False
        self.download_thread = None

        self.load_credentials()

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)

    def start_download(self):
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showinfo("Information", "Le téléchargement est déjà en cours.")
            return
        self.download_thread = threading.Thread(target=self.connect_ftp)
        self.download_thread.start()

    def connect_ftp(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        username = self.username_entry.get()
        password = self.password_entry.get()
        folder = self.folder_entry.get()

        if self.save_var.get():
            self.save_credentials()

        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            ftp.cwd('/')
            files = ftp.nlst()
            total_files = len(files)
            downloaded_files = 0

            self.cancel_button.config(state=tk.NORMAL)

            for file in files:
                if not self.cancel:
                    local_file = os.path.join(folder, file)
                    if not os.path.exists(local_file):
                        with open(local_file, 'wb') as f:
                            ftp.retrbinary('RETR ' + file, f.write)
                        downloaded_files += 1
                    else:
                        try:
                            ftp_time_str = ftp.voidcmd("MDTM " + file)[4:].strip()
                            ftp_time = datetime.strptime(ftp_time_str, "%Y%m%d%H%M%S.%f")
                        except ValueError as e:
                            print("Error parsing FTP time:", e)
                            continue

                        local_time = datetime.fromtimestamp(os.path.getmtime(local_file))
                        if ftp_time > local_time:
                            with open(local_file, 'wb') as f:
                                ftp.retrbinary('RETR ' + file, f.write)
                            downloaded_files += 1

                    self.progress_label.config(text=f"Nombre de fichiers téléchargés : {downloaded_files}/{total_files}")

                else:
                    break

            ftp.quit()
            messagebox.showinfo("Téléchargement terminé", f"{downloaded_files} fichiers téléchargés.")
            self.progress_label.config(text="")
            self.cancel_button.config(state=tk.DISABLED)
            self.cancel = False

        except ftplib.all_errors as e:
            messagebox.showerror("Erreur", f"Erreur de connexion FTP : {e}")

    def cancel_download(self):
        self.cancel = True
        self.cancel_button.config(state=tk.DISABLED)

    def save_credentials(self):
        keyring.set_password("ftp_credentials", "username", self.username_entry.get())
        keyring.set_password("ftp_credentials", "password", self.password_entry.get())
        keyring.set_password("ftp_credentials", "host", self.host_entry.get())
        keyring.set_password("ftp_credentials", "port", self.port_entry.get())
        keyring.set_password("ftp_credentials", "folder", self.folder_entry.get())

    def load_credentials(self):
        username = keyring.get_password("ftp_credentials", "username")
        password = keyring.get_password("ftp_credentials", "password")
        host = keyring.get_password("ftp_credentials", "host")
        port = keyring.get_password("ftp_credentials", "port")
        folder = keyring.get_password("ftp_credentials", "folder")

        if username and password and host and port and folder:
            self.username_entry.insert(0, username)
            self.password_entry.insert(0, password)
            self.host_entry.insert(0, host)
            self.port_entry.insert(0, port)
            self.folder_entry.insert(tk.END, folder)
            self.save_var.set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = FTPDownloader(root)
    root.mainloop()
