"""
Interface graphique pour vérification de la loi de Mariotte
Capteur de pression MPX4250 + Arduino
Lycée Denis Diderot - Belfort
Atelier Arduino - Janvier 2026
VERSION AVEC CONNEXION AUTOMATIQUE ET PLEIN ÉCRAN
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
import csv
from datetime import datetime
import numpy as np
import ctypes
import platform

# Activer la prise en charge DPI sur Windows pour un rendu net
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Police selon le système d'exploitation
FONT_FAMILY = 'Segoe UI' if platform.system() == 'Windows' else 'DejaVu Sans'

# ── Palette de couleurs moderne (thème clair) ──
COLORS = {
    'bg_dark':      '#f0f2f5',   # Fond principal clair
    'bg_sidebar':   '#ffffff',   # Sidebar blanche
    'bg_card':      '#ffffff',   # Cartes blanches
    'bg_input':     '#f5f6f8',   # Champs de saisie
    'bg_hover':     '#e8eaed',   # Hover
    'accent':       '#1976d2',   # Bleu accent principal
    'accent2':      '#2e7d32',   # Vert accent secondaire
    'accent_warn':  '#f57c00',   # Orange avertissement
    'accent_red':   '#d32f2f',   # Rouge
    'accent_purple':'#7b1fa2',   # Violet
    'text_primary': '#212121',   # Texte principal noir
    'text_secondary':'#616161',  # Texte secondaire gris
    'text_dim':     '#9e9e9e',   # Texte très discret
    'border':       '#e0e0e0',   # Bordures claires
    'success':      '#2e7d32',   # Vert succès
    'highlight':    '#bbdefb',   # Ligne sélectionnée tableau
    'header_bg':    '#1565c0',   # Fond du header (bleu foncé)
}

class MariotteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Loi de Mariotte - Capteur de pression Arduino")
        self.root.configure(bg=COLORS['bg_dark'])

        # Adapter la taille à l'écran disponible
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculer un facteur d'échelle basé sur la hauteur de l'écran
        # Référence : 1080p -> facteur 1.0
        self.scale = screen_height / 1080
        if self.scale < 0.6:
            self.scale = 0.6

        # Zone utilisable (retirer la barre des tâches Windows ~50px)
        taskbar_height = 50
        usable_height = screen_height - taskbar_height

        # Utiliser 95% de la largeur, et la hauteur utilisable
        window_width = int(screen_width * 0.80)
        window_height = int(usable_height * 0.80)

        # Centrer la fenêtre
        x = (screen_width - window_width) // 2
        y = (usable_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(800, 500)

        # Variable pour gérer le plein écran
        self.is_fullscreen = False

        # Bind F11 pour basculer en plein écran
        self.root.bind("<F11>", self.toggle_fullscreen)
        # Bind Escape pour sortir du plein écran
        self.root.bind("<Escape>", self.end_fullscreen)

        # Variables
        self.serial_port = None
        self.is_connected = False
        self.is_reading = False
        self.volumes = []
        self.pressions = []
        self.current_pression = 0.0

        # Configurer les styles ttk
        self._setup_styles()

        # Configuration de l'interface
        self.setup_ui()

        # Gestionnaire de fermeture de fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        # Thread de lecture
        self.reading_thread = None

        # CONNEXION AUTOMATIQUE AU DÉMARRAGE
        self.root.after(1000, self.auto_connect)

    def _setup_styles(self):
        """Configurer les styles ttk pour un look moderne"""
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (onglets)
        style.configure('TNotebook', background=COLORS['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab',
                        background=COLORS['bg_card'],
                        foreground=COLORS['text_secondary'],
                        font=self._font(10, bold=True),
                        padding=[20, 8])
        style.map('TNotebook.Tab',
                  background=[('selected', COLORS['bg_dark']),
                              ('active', COLORS['bg_hover'])],
                  foreground=[('selected', COLORS['accent']),
                              ('active', COLORS['text_primary'])])

        # Treeview
        row_height = max(30, int(36 * self.scale))
        style.configure('Tableur.Treeview',
                        background='#ffffff',
                        foreground=COLORS['text_primary'],
                        fieldbackground='#ffffff',
                        rowheight=row_height,
                        font=self._font(10),
                        borderwidth=0)
        style.configure('Tableur.Treeview.Heading',
                        background='#d6e4f0',
                        foreground=COLORS['accent'],
                        font=self._font(10, bold=True),
                        borderwidth=1,
                        relief='flat',
                        padding=[0, 6])
        style.map('Tableur.Treeview.Heading',
                  background=[('active', COLORS['bg_hover'])])
        style.map('Tableur.Treeview',
                  background=[('selected', COLORS['highlight'])],
                  foreground=[('selected', COLORS['text_primary'])])

        # Scrollbar
        style.configure('Dark.Vertical.TScrollbar',
                        background=COLORS['bg_card'],
                        troughcolor=COLORS['bg_dark'],
                        borderwidth=0,
                        arrowsize=14)

    def toggle_fullscreen(self, event=None):
        """Basculer entre plein écran et mode fenêtré"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def end_fullscreen(self, event=None):
        """Sortir du plein écran"""
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)
        return "break"

    def find_arduino_port(self):
        """Rechercher automatiquement le port Arduino"""
        ports = serial.tools.list_ports.comports()

        for port in ports:
            if 'arduino' in port.description.lower() or 'ch340' in port.description.lower() or 'usb' in port.description.lower():
                return port.device

        if ports:
            return ports[0].device

        return None

    def auto_connect(self):
        """Connexion automatique à l'Arduino"""
        port = self.find_arduino_port()

        if not port:
            self.log_info("Aucun Arduino detecte!")
            messagebox.showwarning("Attention",
                                  "Aucun Arduino détecté.\n\n"
                                  "Vérifiez que:\n"
                                  "- L'Arduino est branché\n"
                                  "- Les drivers sont installés\n"
                                  "- Le port COM est disponible")
            return

        try:
            self.log_info(f"Arduino detecte sur {port}")
            self.log_info(f"Connexion en cours...")

            # Essayer d'abord 115200
            try:
                self.serial_port = serial.Serial(port, 115200, timeout=2)
                time.sleep(2)
                self.log_info(f"Connexion a {port} (115200 bauds)")
            except:
                # Si échec, essayer 9600
                self.serial_port = serial.Serial(port, 9600, timeout=2)
                time.sleep(2)
                self.log_info(f"Connexion a {port} (9600 bauds)")

            self.is_connected = True
            self.is_reading = True

            self.reading_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.reading_thread.start()

            self.status_indicator.itemconfig(self._status_dot, fill='#69f0ae')
            self.status_label.config(text=f"Connecté ({port})", fg='#69f0ae')
            self.btn_disconnect.config(state=tk.NORMAL, fg='white')
            self.btn_add_point.config(state=tk.NORMAL)
            self.btn_reconnect.config(bg='#546e7a')

            self.log_info(f"Connecte avec succes a {port}")

        except Exception as e:
            self.log_info(f"Erreur de connexion: {e}")
            messagebox.showerror("Erreur", f"Impossible de se connecter à {port}:\n\n{e}")

    def disconnect(self):
        """Déconnecter l'Arduino"""
        self.is_reading = False
        time.sleep(0.5)
        if self.serial_port:
            self.serial_port.close()
        self.is_connected = False

        self.status_indicator.itemconfig(self._status_dot, fill='#ff5252')
        self.status_label.config(text="Déconnecté", fg='#ff5252')
        self.btn_disconnect.config(state=tk.DISABLED, fg='white')
        self.btn_add_point.config(state=tk.DISABLED)
        self.btn_reconnect.config(bg='#2e7d32')

        self.log_info("Deconnecte")

    def reconnect(self):
        """Reconnecter à l'Arduino"""
        if self.is_connected:
            self.disconnect()
            time.sleep(1)
        self.auto_connect()

    def _font(self, base_size, bold=False):
        """Retourne une police mise à l'échelle"""
        size = max(7, int(base_size * 0.72 * self.scale))
        weight = 'bold' if bold else 'normal'
        return (FONT_FAMILY, size, weight)

    def _pad(self, base):
        """Retourne un padding mis à l'échelle"""
        return max(1, int(base * self.scale))

    def _create_styled_button(self, parent, text, command, color, **kwargs):
        """Créer un bouton avec style moderne"""
        state = kwargs.pop('state', tk.NORMAL)
        btn = tk.Button(parent, text=text, command=command,
                       bg=color, fg='white',
                       activebackground=color,
                       activeforeground='white',
                       font=self._font(9, bold=True),
                       relief='flat', bd=0, cursor='hand2',
                       padx=12, pady=6,
                       state=state)

        # Effet hover
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn.config(bg=self._lighten_color(color))
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn.config(bg=color)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    @staticmethod
    def _lighten_color(hex_color, factor=0.15):
        """Éclaircir une couleur hex"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def setup_ui(self):
        """Créer l'interface utilisateur"""

        p = self._pad  # raccourci
        C = COLORS     # raccourci

        # ============ BARRE SUPERIEURE - Header ============
        hbg = C['header_bg']
        header_h = max(50, int(60 * self.scale))
        frame_top = tk.Frame(self.root, bg=hbg, height=header_h)
        frame_top.pack(fill=tk.X)
        frame_top.pack_propagate(False)

        # Conteneur centré dans le header
        header_content = tk.Frame(frame_top, bg=hbg)
        header_content.pack(fill=tk.BOTH, expand=True, padx=p(15))

        # Titre à gauche
        title_frame = tk.Frame(header_content, bg=hbg)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(title_frame, text="LOI DE MARIOTTE",
                font=self._font(15, bold=True),
                bg=hbg, fg='white').pack(side=tk.LEFT, pady=p(5))

        tk.Label(title_frame, text="  P x V = Cte",
                font=self._font(11),
                bg=hbg, fg='#bbdefb').pack(side=tk.LEFT, pady=p(5))

        # Indication plein écran à droite
        tk.Label(header_content, text="F11: Plein ecran",
                bg=hbg, fg='#90caf9',
                font=self._font(8)).pack(side=tk.RIGHT, padx=p(8), pady=p(5))

        # Statut et boutons au centre
        status_frame = tk.Frame(header_content, bg=hbg)
        status_frame.pack(fill=tk.Y, expand=True)

        status_center = tk.Frame(status_frame, bg=hbg)
        status_center.pack(pady=p(5))

        # Indicateur de connexion (petit rond)
        self.status_indicator = tk.Canvas(status_center, width=14, height=14,
                                          bg=hbg, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 6))
        self._status_dot = self.status_indicator.create_oval(2, 2, 12, 12,
                                                             fill='#ffcc80', outline='')

        self.status_label = tk.Label(status_center, text="Connexion...",
                                     bg=hbg, fg='#ffcc80',
                                     font=self._font(10, bold=True))
        self.status_label.pack(side=tk.LEFT, padx=(0, p(10)))

        self.btn_disconnect = self._create_styled_button(
            status_center, "Déconnecter", self.disconnect, C['accent_red'],
            state=tk.DISABLED)
        self.btn_disconnect.pack(side=tk.LEFT, padx=p(3))

        self.btn_reconnect = self._create_styled_button(
            status_center, "Reconnecter", self.reconnect, '#546e7a')
        self.btn_reconnect.pack(side=tk.LEFT, padx=p(3))

        # ============ Ligne de séparation accent ============
        tk.Frame(self.root, bg=C['accent'], height=2).pack(fill=tk.X)

        # ============ FRAME PRINCIPAL avec PanedWindow ============
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=3,
                                   bg=C['border'], bd=0)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # ============ FRAME GAUCHE - Contrôles (scrollable) ============
        frame_left_container = tk.Frame(main_pane, bg=C['bg_sidebar'])

        # Canvas scrollable pour le panneau gauche
        left_canvas = tk.Canvas(frame_left_container, bg=C['bg_sidebar'],
                                highlightthickness=0)
        left_scrollbar = tk.Scrollbar(frame_left_container, orient=tk.VERTICAL,
                                       command=left_canvas.yview)
        frame_left = tk.Frame(left_canvas, bg=C['bg_sidebar'])

        frame_left.bind("<Configure>",
                        lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=frame_left, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll avec la molette de la souris (Windows/macOS et Linux)
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _on_mousewheel_up(event):
            left_canvas.yview_scroll(-1, "units")
        def _on_mousewheel_down(event):
            left_canvas.yview_scroll(1, "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        left_canvas.bind_all("<Button-4>", _on_mousewheel_up)
        left_canvas.bind_all("<Button-5>", _on_mousewheel_down)

        # Adapter la largeur du frame interne au canvas
        def _on_canvas_configure(event):
            left_canvas.itemconfig(left_canvas.find_all()[0], width=event.width)
        left_canvas.bind("<Configure>", _on_canvas_configure)

        # ── Helper pour créer une section (card) ──
        def make_section(parent, title):
            """Créer un cadre de section avec titre stylé"""
            outer = tk.Frame(parent, bg=C['bg_sidebar'])
            outer.pack(fill=tk.X, padx=p(8), pady=p(4))

            # Titre de section
            tk.Label(outer, text=title, font=self._font(9, bold=True),
                    bg=C['bg_sidebar'], fg=C['accent'],
                    anchor='w').pack(fill=tk.X, pady=(0, p(3)))

            # Card
            card = tk.Frame(outer, bg=C['bg_card'],
                           highlightbackground=C['border'],
                           highlightthickness=1)
            card.pack(fill=tk.X)
            return card

        # --- Affichage pression actuelle ---
        pressure_card = make_section(frame_left, "PRESSION ACTUELLE")

        self.pressure_label = tk.Label(pressure_card, text="--.-",
                                      font=(FONT_FAMILY, max(8, int(18 * self.scale)), 'bold'),
                                      bg=C['bg_card'], fg=C['accent'])
        self.pressure_label.pack(pady=(p(8), p(2)))

        tk.Label(pressure_card, text="kPa",
                font=self._font(10), bg=C['bg_card'],
                fg=C['text_secondary']).pack(pady=(0, p(8)))

        # --- Volume ---
        volume_card = make_section(frame_left, "VOLUME DE GAZ")

        tk.Label(volume_card, text="Volume de la seringue (cm³)",
                bg=C['bg_card'], fg=C['text_secondary'],
                font=self._font(9)).pack(pady=(p(6), p(3)))

        entry_frame = tk.Frame(volume_card, bg=C['bg_card'])
        entry_frame.pack(pady=p(3))

        self.volume_entry = tk.Entry(entry_frame, font=self._font(12, bold=True),
                                     width=8, justify='center',
                                     bg=C['bg_input'], fg=C['text_primary'],
                                     insertbackground=C['accent'],
                                     relief='flat', bd=0,
                                     highlightbackground=C['border'],
                                     highlightthickness=2,
                                     highlightcolor=C['accent'])
        self.volume_entry.pack(ipady=4)
        self.volume_entry.insert(0, "60.0")

        # Volumes rapides
        tk.Label(volume_card, text="Volumes rapides",
                bg=C['bg_card'], fg=C['text_dim'],
                font=self._font(8)).pack(pady=(p(6), p(2)))

        quick_buttons_frame = tk.Frame(volume_card, bg=C['bg_card'])
        quick_buttons_frame.pack(pady=p(2))

        self._quick_buttons = {}
        for vol in [20, 25, 30, 35, 40, 45, 50, 55, 60]:
            fg_color = C['success'] if vol == 40 else C['text_secondary']
            font = self._font(8, bold=True) if vol == 40 else self._font(8)
            btn = tk.Button(quick_buttons_frame, text=f"{vol}",
                     command=lambda v=vol: self.set_volume(v),
                     bg=C['bg_hover'], fg=fg_color,
                     activebackground=self._lighten_color(C['bg_hover']),
                     font=font, width=3,
                     relief='flat', bd=0, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            self._quick_buttons[vol] = btn

        # Bouton ajouter mesure
        add_frame = tk.Frame(volume_card, bg=C['bg_card'])
        add_frame.pack(fill=tk.X, padx=p(8), pady=(p(6), p(8)))

        self.btn_add_point = self._create_styled_button(
            add_frame, "AJOUTER MESURE", self.add_point, '#1976d2',
            state=tk.DISABLED)
        self.btn_add_point.pack(fill=tk.X, ipady=4)

        # --- Résultats ---
        results_card = make_section(frame_left, "RESULTATS")

        results_inner = tk.Frame(results_card, bg=C['bg_card'])
        results_inner.pack(fill=tk.X, padx=p(8), pady=p(8))

        # Nombre de mesures
        row1 = tk.Frame(results_inner, bg=C['bg_card'])
        row1.pack(fill=tk.X, pady=p(2))
        tk.Label(row1, text="Mesures", bg=C['bg_card'],
                fg=C['text_secondary'], font=self._font(9),
                anchor='w').pack(side=tk.LEFT)
        self.nb_points_label = tk.Label(row1, text="0", bg=C['bg_card'],
                                       font=self._font(11, bold=True),
                                       fg=C['accent'], anchor='e')
        self.nb_points_label.pack(side=tk.RIGHT)

        # --- Actions ---
        actions_card = make_section(frame_left, "ACTIONS")
        actions_inner = tk.Frame(actions_card, bg=C['bg_card'])
        actions_inner.pack(fill=tk.X, padx=p(6), pady=p(6))

        action_buttons = [
            ("NOUVELLE SERIE",     self.new_serie,       C['accent_warn']),
            ("SAUVEGARDER",        self.save_data,        '#00897b'),
            ("TRACER COURBES",     self.draw_regressions, C['accent_purple']),
            ("VERIFIER LINEARITE", self.check_linearity,  '#7b1fa2'),
            ("QUITTER",            self.quit_application, C['accent_red']),
        ]

        for text, cmd, color in action_buttons:
            btn = self._create_styled_button(actions_inner, text, cmd, color)
            btn.pack(fill=tk.X, pady=p(2), ipady=2)

        # --- Info / Log ---
        info_section = tk.Frame(frame_left, bg=C['bg_sidebar'])
        info_section.pack(fill=tk.X, padx=p(8), pady=p(4))

        tk.Label(info_section, text="LOG", font=self._font(9, bold=True),
                bg=C['bg_sidebar'], fg=C['accent'],
                anchor='w').pack(fill=tk.X, pady=(0, p(3)))

        log_card = tk.Frame(info_section, bg=C['bg_card'],
                           highlightbackground=C['border'],
                           highlightthickness=1)
        log_card.pack(fill=tk.X)

        self.info_text = tk.Text(log_card, height=3,
                                font=self._font(8), bg=C['bg_card'],
                                fg=C['text_secondary'],
                                insertbackground=C['accent'],
                                state=tk.DISABLED, wrap=tk.WORD,
                                relief='flat', bd=0,
                                padx=8, pady=6)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # --- Signature ---
        tk.Label(frame_left, text="Alexis Ruiz | Lycee Diderot",
                font=self._font(8), bg=C['bg_sidebar'],
                fg=C['text_dim']).pack(pady=(p(6), p(8)))

        # Ajouter le panneau gauche au PanedWindow
        left_width = int(self.root.winfo_screenwidth() * 0.22)
        main_pane.add(frame_left_container, width=left_width, minsize=180)

        # ============ FRAME DROITE - Notebook avec onglets ============
        frame_right = tk.Frame(main_pane, bg=C['bg_dark'])
        main_pane.add(frame_right, minsize=300)

        self.notebook = ttk.Notebook(frame_right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Onglet Graphiques ---
        tab_graphiques = tk.Frame(self.notebook, bg=C['bg_dark'])
        self.notebook.add(tab_graphiques, text='   Graphiques   ')

        # Créer deux graphiques côte à côte - TAILLE ADAPTATIVE
        fig_dpi = max(70, int(100 * self.scale))
        self.fig = Figure(dpi=fig_dpi, facecolor='#f0f2f5')

        # Taille de police adaptative pour matplotlib
        ax_label_size = max(8, int(11 * self.scale))
        ax_title_size = max(9, int(13 * self.scale))
        marker_size = max(6, int(10 * self.scale))

        # Style matplotlib clair
        ax_kwargs = dict(facecolor='white')
        text_color = C['text_primary']
        grid_color = '#cccccc'

        # Graphique 1: P = f(V) - À GAUCHE
        self.ax1 = self.fig.add_subplot(121, **ax_kwargs)
        self.ax1.set_xlabel('Volume V (cm³)', fontsize=ax_label_size, fontweight='bold', color=text_color)
        self.ax1.set_ylabel('Pression P (kPa)', fontsize=ax_label_size, fontweight='bold', color=text_color)
        self.ax1.set_title('Pression en fonction du volume', fontsize=ax_title_size, fontweight='bold', color=C['accent'])
        self.ax1.grid(True, alpha=0.3, color=grid_color)
        self.ax1.set_xlim(0, 65)
        self.ax1.tick_params(labelsize=max(7, int(9 * self.scale)), colors=C['text_secondary'])

        # Graphique 2: P = f(1/V) - À DROITE
        self.ax2 = self.fig.add_subplot(122, **ax_kwargs)
        self.ax2.set_xlabel('1/V (cm³^-1)', fontsize=ax_label_size, fontweight='bold', color=text_color)
        self.ax2.set_ylabel('Pression P (kPa)', fontsize=ax_label_size, fontweight='bold', color=text_color)
        self.ax2.set_title('P en fonction de 1/V', fontsize=ax_title_size, fontweight='bold', color=C['accent'])
        self.ax2.grid(True, alpha=0.3, color=grid_color)
        self.ax2.set_xlim(0, 0.05)
        self.ax2.tick_params(labelsize=max(7, int(9 * self.scale)), colors=C['text_secondary'])

        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_graphiques)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Lignes sur les graphiques
        self.line1, = self.ax1.plot([], [], 'o', color=COLORS['accent'],
                                    markersize=marker_size, label='Mesures')
        self.line2, = self.ax2.plot([], [], 'o', color=COLORS['accent2'],
                                    markersize=marker_size, label='Mesures')
        self.regression_line = None
        self.hyperbole_line = None

        # --- Onglet Tableur ---
        tab_tableur = tk.Frame(self.notebook, bg=C['bg_dark'])
        self.notebook.add(tab_tableur, text='   Tableur   ')

        # Titre du tableur
        tableur_header = tk.Frame(tab_tableur, bg=C['bg_dark'])
        tableur_header.pack(fill=tk.X, padx=p(10), pady=(p(10), p(4)))
        tk.Label(tableur_header, text="Tableau des mesures",
                font=self._font(13, bold=True),
                bg=C['bg_dark'], fg=C['text_primary']).pack(side=tk.LEFT)
        tk.Label(tableur_header, text="Double-cliquez sur Volume ou Pression pour modifier",
                font=self._font(9),
                bg=C['bg_dark'], fg=C['text_dim']).pack(side=tk.RIGHT)

        # Treeview pour le tableau de mesures
        tree_frame = tk.Frame(tab_tableur, bg=C['bg_card'],
                             highlightbackground=C['border'],
                             highlightthickness=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=p(10), pady=p(4))

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                    style='Dark.Vertical.TScrollbar')
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(tree_frame, columns=('num', 'volume', 'pression', 'calcul'),
                                 show='headings', yscrollcommand=tree_scroll.set,
                                 style='Tableur.Treeview')
        tree_scroll.config(command=self.tree.yview)

        # Couleurs alternées pour les lignes (contraste plus marqué)
        self.tree.tag_configure('even', background='#ffffff')
        self.tree.tag_configure('odd', background='#eef1f6')

        # Stockage des formules par index de ligne
        self._formulas = {}

        # État du tri pour chaque colonne (True = croissant)
        self._tree_sort_asc = {'num': True, 'volume': True, 'pression': True, 'calcul': True}

        for col_id, col_text in [('num', 'N°'), ('volume', 'A - Volume (cm³)'),
                                  ('pression', 'B - Pression (kPa)'), ('calcul', 'C - Calcul')]:
            self.tree.heading(col_id, text=col_text,
                             command=lambda c=col_id: self._sort_treeview(c))

        self.tree.column('num', width=70, anchor='center', stretch=True)
        self.tree.column('volume', width=200, anchor='center', stretch=True)
        self.tree.column('pression', width=200, anchor='center', stretch=True)
        self.tree.column('calcul', width=200, anchor='center', stretch=True)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Double-clic pour éditer une cellule
        self.tree.bind('<Double-1>', self._on_tree_double_click)

        # Boutons sous le tableau
        btn_frame = tk.Frame(tab_tableur, bg=C['bg_dark'])
        btn_frame.pack(fill=tk.X, padx=p(10), pady=p(6))

        btn_row = tk.Frame(btn_frame, bg=C['bg_dark'])
        btn_row.pack(fill=tk.X, padx=p(4))

        del_btn = self._create_styled_button(
            btn_row, "SUPPRIMER LA LIGNE",
            self._delete_selected_row, C['accent_red'])
        del_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=4, padx=(0, p(3)))

        fill_btn = self._create_styled_button(
            btn_row, "REMPLIR CALCUL VERS LE BAS",
            self._fill_down_formula, C['accent'])
        fill_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=4, padx=(p(3), 0))

        # Aide formules
        help_frame = tk.Frame(tab_tableur, bg=C['bg_dark'])
        help_frame.pack(fill=tk.X, padx=p(14), pady=(0, p(4)))
        tk.Label(help_frame,
                text="Colonne Calcul : double-cliquez et entrez une formule (ex: =A1*B1).  "
                     "A = Volume, B = Pression, le chiffre = n° de ligne.  "
                     "\"Remplir vers le bas\" applique la formule de la ligne 1 a toutes les lignes.",
                bg=C['bg_dark'], fg=C['text_dim'],
                font=self._font(8), wraplength=800, justify='left').pack(anchor='w')

    def read_serial(self):
        """Thread de lecture du port série"""
        while self.is_reading:
            try:
                if self.serial_port and self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8').strip()

                    # Extraire la pression - ACCEPTE DEUX FORMATS
                    if ("Pression:" in line or "P =" in line) and "kPa" in line:
                        try:
                            if "Pression:" in line:
                                pression_str = line.split("Pression:")[1].split("kPa")[0].strip()
                            elif "P =" in line:
                                pression_str = line.split("P =")[1].split("kPa")[0].strip()

                            self.current_pression = float(pression_str)

                            self.root.after(0, self.update_pressure_display, self.current_pression)
                        except (ValueError, IndexError):
                            pass

                time.sleep(0.1)
            except Exception as e:
                print(f"Erreur lecture série: {e}")
                break

    def update_pressure_display(self, pression):
        """Mettre à jour l'affichage de la pression"""
        self.pressure_label.config(text=f"{pression:.1f}")

    def _update_quick_buttons(self):
        """Colorer en bleu les boutons de volume déjà mesurés"""
        C = COLORS
        measured = set(int(v) for v in self.volumes if v == int(v))
        for vol, btn in self._quick_buttons.items():
            if vol in measured:
                btn.config(bg=C['accent'], fg='white')
            else:
                fg_color = C['success'] if vol == 40 else C['text_secondary']
                btn.config(bg=C['bg_hover'], fg=fg_color)

    def set_volume(self, volume):
        """Définir rapidement le volume"""
        self.volume_entry.delete(0, tk.END)
        self.volume_entry.insert(0, str(volume))

    def add_point(self):
        """Ajouter un point de mesure"""
        try:
            volume = float(self.volume_entry.get().replace(',', '.'))
            if volume <= 0:
                messagebox.showerror("Erreur", "Le volume doit être positif!")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Volume invalide!")
            return

        # Attendre stabilisation (5 lectures)
        self.log_info(f"Volume {volume} cm³... Attente stabilisation...")
        self.root.update()

        pression_readings = []
        for i in range(5):
            time.sleep(1.0)
            pression_readings.append(self.current_pression)

        # Moyenne des 5 lectures
        pression_moyenne = sum(pression_readings) / len(pression_readings)

        # Ajouter les données
        self.volumes.append(volume)
        self.pressions.append(pression_moyenne)

        # Ajouter la ligne dans le Treeview (colonne Calcul vide)
        n = len(self.volumes)
        tag = 'even' if n % 2 == 0 else 'odd'
        self.tree.insert('', 'end', values=(n, f"{volume:.1f}", f"{pression_moyenne:.1f}", ""),
                        tags=(tag,))

        # Mise à jour des graphiques
        self.update_plots()

        # Mise à jour des résultats
        self.update_results()
        self._update_quick_buttons()

        # Log
        self.log_info(f"Point: V={volume:.1f} cm³, P={pression_moyenne:.1f} kPa")

    def update_plots(self):
        """Mettre à jour les graphiques"""
        if not self.volumes:
            return

        # Graphique 1: P = f(V)
        self.line1.set_data(self.volumes, self.pressions)

        # Limites FIXES pour le volume: 0 à 65 mL
        self.ax1.set_xlim(0, 65)
        # Limites adaptatives pour la pression
        self.ax1.set_ylim(min(self.pressions) * 0.9, max(self.pressions) * 1.1)

        # Graphique 2: P = f(1/V)
        inv_volumes = [1/v for v in self.volumes]
        self.line2.set_data(inv_volumes, self.pressions)

        # Limites FIXES pour 1/V: 0 à 0.05 mL⁻¹
        self.ax2.set_xlim(0, 0.05)
        # Limites adaptatives pour la pression
        self.ax2.set_ylim(min(self.pressions) * 0.9, max(self.pressions) * 1.1)

        self.canvas.draw()

    def update_results(self):
        """Mettre à jour les résultats statistiques"""
        self.nb_points_label.config(text=str(len(self.volumes)))

    def _refresh_treeview(self):
        """Reconstruire le Treeview à partir de self.volumes et self.pressions"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, (v, p) in enumerate(zip(self.volumes, self.pressions)):
            # Recalculer la formule si elle existe pour cette ligne
            calcul_val = ""
            if i in self._formulas:
                calcul_val = self._eval_formula(self._formulas[i], i)
            tag = 'even' if (i + 1) % 2 == 0 else 'odd'
            self.tree.insert('', 'end',
                           values=(i + 1, f"{v:.1f}", f"{p:.1f}", calcul_val),
                           tags=(tag,))

    def _sort_treeview(self, col):
        """Trier le Treeview par colonne (clic sur l'en-tête)"""
        ascending = self._tree_sort_asc.get(col, True)

        # Récupérer toutes les lignes
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children()]

        # Tri numérique (les cellules vides vont à la fin)
        def sort_key(x):
            try:
                return float(x[0])
            except (ValueError, TypeError):
                return float('inf')
        items.sort(key=sort_key, reverse=not ascending)

        # Réorganiser dans le Treeview
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

        # Réorganiser self.volumes et self.pressions dans le même ordre
        children = self.tree.get_children()
        new_volumes = []
        new_pressions = []
        for item in children:
            vals = self.tree.item(item, 'values')
            new_volumes.append(float(vals[1]))
            new_pressions.append(float(vals[2]))
        self.volumes = new_volumes
        self.pressions = new_pressions

        # Renuméroter et rafraîchir
        self._refresh_treeview()
        self.update_plots()
        self.update_results()

        # Inverser le sens pour le prochain clic
        self._tree_sort_asc[col] = not ascending

        # Mettre à jour l'en-tête avec une flèche
        arrow = ' ▲' if ascending else ' ▼'
        col_texts = {'num': 'N°', 'volume': 'A - Volume (cm³)',
                     'pression': 'B - Pression (kPa)', 'calcul': 'C - Calcul'}
        for c, text in col_texts.items():
            suffix = arrow if c == col else ''
            self.tree.heading(c, text=text + suffix)

    def _on_tree_double_click(self, event):
        """Ouvrir un Entry pour éditer une cellule"""
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return

        col = self.tree.identify_column(event.x)  # '#1', '#2', ...
        col_index = int(col.replace('#', ''))
        if col_index not in (2, 3, 4):  # Volume (2), Pression (3), Calcul (4)
            return

        item = self.tree.identify_row(event.y)
        if not item:
            return

        # Récupérer la position de la cellule
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return

        children = self.tree.get_children()
        row_index = list(children).index(item)

        # Pour la colonne Calcul, afficher la formule brute si elle existe
        if col_index == 4 and row_index in self._formulas:
            current_value = self._formulas[row_index]
        else:
            current_value = self.tree.set(item, col)

        # Créer un Entry flottant
        entry = tk.Entry(self.tree, justify='center',
                        font=self._font(10, bold=True),
                        bg=COLORS['bg_input'], fg=COLORS['accent'],
                        insertbackground=COLORS['accent'],
                        relief='flat',
                        highlightbackground=COLORS['accent'],
                        highlightthickness=2,
                        highlightcolor=COLORS['accent'])
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus_set()

        def _validate(e=None):
            raw = entry.get().strip()
            entry.destroy()

            if col_index == 4:  # Colonne Calcul - formule
                if raw.startswith('='):
                    self._formulas[row_index] = raw
                    result = self._eval_formula(raw, row_index)
                    self.tree.set(item, col, result)
                else:
                    # Valeur directe ou vide
                    if raw == '':
                        self._formulas.pop(row_index, None)
                        self.tree.set(item, col, '')
                    else:
                        self._formulas.pop(row_index, None)
                        self.tree.set(item, col, raw)
                self.log_info(f"Calcul ligne {row_index + 1} : {raw}")
                return

            # Colonnes Volume / Pression
            new_val = raw.replace(',', '.')
            try:
                val = float(new_val)
                if val <= 0:
                    raise ValueError
            except ValueError:
                return

            if col_index == 2:  # Volume
                self.volumes[row_index] = val
            else:  # Pression
                self.pressions[row_index] = val

            self._refresh_treeview()
            self.update_plots()
            self.update_results()
            self.log_info(f"Mesure n{row_index + 1} modifiee")

        def _cancel(e=None):
            entry.destroy()

        entry.bind('<Return>', _validate)
        entry.bind('<Escape>', _cancel)
        entry.bind('<FocusOut>', _validate)

    def _eval_formula(self, formula, row_index):
        """Évaluer une formule style tableur (ex: =A1*B1)"""
        if not formula.startswith('='):
            return formula
        try:
            expr = formula[1:]  # enlever le =
            import re
            # Remplacer A1, B1, etc. par les valeurs correspondantes
            def replace_ref(match):
                col_letter = match.group(1).upper()
                ref_row = int(match.group(2)) - 1  # index 0-based
                if ref_row < 0 or ref_row >= len(self.volumes):
                    return '0'
                if col_letter == 'A':
                    return str(self.volumes[ref_row])
                elif col_letter == 'B':
                    return str(self.pressions[ref_row])
                elif col_letter == 'C':
                    # Référence à une autre cellule calcul
                    if ref_row in self._formulas:
                        return str(self._eval_formula(self._formulas[ref_row], ref_row))
                    return '0'
                return '0'

            expr = re.sub(r'([A-Ca-c])(\d+)', replace_ref, expr)
            # Évaluer l'expression mathématique (seulement opérations de base)
            result = eval(expr, {"__builtins__": {}},
                         {"abs": abs, "round": round, "min": min, "max": max})
            return f"{result:.2f}"
        except Exception:
            return "ERREUR"

    def _fill_down_formula(self):
        """Remplir la colonne Calcul vers le bas depuis la formule de la ligne 1"""
        if not self.volumes:
            return
        if 0 not in self._formulas:
            messagebox.showinfo("Info",
                "Entrez d'abord une formule dans la colonne Calcul de la ligne 1.\n"
                "Exemple : =A1*B1")
            return

        base_formula = self._formulas[0]  # ex: =A1*B1
        import re

        for i in range(len(self.volumes)):
            # Remplacer les numéros de ligne dans la formule
            def adjust_row(match):
                col_letter = match.group(1)
                return f"{col_letter}{i + 1}"
            adapted = re.sub(r'([A-Ca-c])(\d+)', adjust_row, base_formula)
            self._formulas[i] = adapted

        self._refresh_treeview()
        self.log_info(f"Formule \"{base_formula}\" appliquee a {len(self.volumes)} lignes")

    def _delete_selected_row(self):
        """Supprimer la ligne sélectionnée dans le Treeview"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Aucune ligne selectionnee!")
            return

        item = selected[0]
        children = self.tree.get_children()
        row_index = list(children).index(item)

        del self.volumes[row_index]
        del self.pressions[row_index]

        # Réindexer les formules
        new_formulas = {}
        for k, v in self._formulas.items():
            if k < row_index:
                new_formulas[k] = v
            elif k > row_index:
                new_formulas[k - 1] = v
        self._formulas = new_formulas

        self._refresh_treeview()
        self.update_plots()
        self.update_results()
        self._update_quick_buttons()
        self.log_info(f"Mesure n{row_index + 1} supprimee")

    def new_serie(self):
        """Commencer une nouvelle série de mesures"""
        if self.volumes:
            response = messagebox.askyesno("Confirmation",
                                          "Effacer les données actuelles?")
            if not response:
                return

        # Réinitialiser
        self.volumes = []
        self.pressions = []

        # Vider le Treeview et les formules
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._formulas = {}

        # Effacer les graphiques
        ax_label_size = max(8, int(11 * self.scale))
        ax_title_size = max(9, int(13 * self.scale))
        marker_size = max(6, int(10 * self.scale))
        tick_size = max(7, int(9 * self.scale))
        C = COLORS

        self.ax1.clear()
        self.ax1.set_facecolor('white')
        self.ax1.set_xlabel('Volume V (cm³)', fontsize=ax_label_size, fontweight='bold', color=C['text_primary'])
        self.ax1.set_ylabel('Pression P (kPa)', fontsize=ax_label_size, fontweight='bold', color=C['text_primary'])
        self.ax1.set_title('Pression en fonction du volume', fontsize=ax_title_size, fontweight='bold', color=C['accent'])
        self.ax1.grid(True, alpha=0.3, color='#cccccc')
        self.ax1.set_xlim(0, 65)
        self.ax1.tick_params(labelsize=tick_size, colors=C['text_secondary'])
        self.line1, = self.ax1.plot([], [], 'o', color=C['accent'], markersize=marker_size, label='Mesures')

        self.ax2.clear()
        self.ax2.set_facecolor('white')
        self.ax2.set_xlabel('1/V (cm³^-1)', fontsize=ax_label_size, fontweight='bold', color=C['text_primary'])
        self.ax2.set_ylabel('Pression P (kPa)', fontsize=ax_label_size, fontweight='bold', color=C['text_primary'])
        self.ax2.set_title('P en fonction de 1/V', fontsize=ax_title_size, fontweight='bold', color=C['accent'])
        self.ax2.grid(True, alpha=0.3, color='#cccccc')
        self.ax2.set_xlim(0, 0.05)
        self.ax2.tick_params(labelsize=tick_size, colors=C['text_secondary'])
        self.line2, = self.ax2.plot([], [], 'o', color=C['accent2'], markersize=marker_size, label='Mesures')
        self.regression_line = None
        self.hyperbole_line = None

        self.canvas.draw()

        # Réinitialiser les résultats
        self.update_results()

        self._update_quick_buttons()
        self.log_info("Nouvelle serie demarree")

    def save_data(self):
        """Sauvegarder les données"""
        if not self.volumes:
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"mariotte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(['Volume (cm³)', 'Pression (kPa)', 'Calcul'])
                    for i, (v, p) in enumerate(zip(self.volumes, self.pressions)):
                        calcul = self._eval_formula(self._formulas[i], i) if i in self._formulas else ''
                        writer.writerow([f"{v:.2f}", f"{p:.2f}", calcul])

                fig_filename = filename.replace('.csv', '.png')
                self.fig.savefig(fig_filename, dpi=300, bbox_inches='tight',
                                facecolor='white')

                self.log_info(f"Donnees sauvegardees: {filename}")
                messagebox.showinfo("Succes", f"Données sauvegardées!\n{filename}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")

    def draw_regressions(self):
        """Tracer les courbes de régression sur les deux graphiques"""
        if len(self.volumes) < 3:
            messagebox.showwarning("Attention",
                                  "Pas assez de points pour tracer les courbes!\nAu moins 3 points nécessaires.")
            return

        pv_values = [p * v for p, v in zip(self.pressions, self.volumes)]
        pv_moyen = sum(pv_values) / len(pv_values)

        # === GRAPHIQUE 1 : Hyperbole P = k/V ===
        v_min = min(self.volumes)
        v_max = max(self.volumes)
        v_theo = np.linspace(v_min * 0.9, v_max * 1.1, 100)
        p_theo = pv_moyen / v_theo

        if self.hyperbole_line:
            self.hyperbole_line.remove()

        self.hyperbole_line, = self.ax1.plot(v_theo, p_theo, '-',
                                             color=COLORS['accent_warn'],
                                             linewidth=2,
                                             label=f'Hyperbole PxV={pv_moyen:.0f}')
        self.ax1.legend()

        # === GRAPHIQUE 2 : Droite P = f(1/V) ===
        inv_volumes = np.array([1/v for v in self.volumes])
        pressions = np.array(self.pressions)

        coeffs = np.polyfit(inv_volumes, pressions, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        if self.regression_line:
            self.regression_line.remove()

        x_reg = np.linspace(min(inv_volumes) * 0.9, max(inv_volumes) * 1.1, 100)
        y_reg = slope * x_reg + intercept
        self.regression_line, = self.ax2.plot(x_reg, y_reg, '-',
                                              color=COLORS['accent_warn'],
                                              linewidth=2,
                                              label=f'Regression: P = {slope:.1f}/V + {intercept:.1f}')
        self.ax2.legend()

        self.canvas.draw()

        self.log_info(f"Courbes tracees - PxV moyen = {pv_moyen:.1f} kPa.cm³")

    def check_linearity(self):
        """Vérifier la linéarité P = f(1/V) et afficher la régression avec R²"""
        if len(self.volumes) < 3:
            messagebox.showwarning("Attention",
                                  "Pas assez de points pour la régression!")
            return

        inv_volumes = np.array([1/v for v in self.volumes])
        pressions = np.array(self.pressions)

        coeffs = np.polyfit(inv_volumes, pressions, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculer R²
        p_pred = slope * inv_volumes + intercept
        ss_res = np.sum((pressions - p_pred)**2)
        ss_tot = np.sum((pressions - np.mean(pressions))**2)
        r_squared = 1 - (ss_res / ss_tot)

        if not self.regression_line:
            x_reg = np.linspace(min(inv_volumes) * 0.9, max(inv_volumes) * 1.1, 100)
            y_reg = slope * x_reg + intercept
            self.regression_line, = self.ax2.plot(x_reg, y_reg, '-',
                                                 color=COLORS['accent_warn'],
                                                 linewidth=2,
                                                 label=f'Regression: P = {slope:.1f}/V + {intercept:.1f}\nR2 = {r_squared:.4f}')
            self.ax2.legend(facecolor=COLORS['bg_card'], edgecolor=COLORS['border'],
                           labelcolor=COLORS['text_primary'])
            self.canvas.draw()
        else:
            self.regression_line.set_label(f'Regression: P = {slope:.1f}/V + {intercept:.1f}\nR2 = {r_squared:.4f}')
            self.ax2.legend(facecolor=COLORS['bg_card'], edgecolor=COLORS['border'],
                           labelcolor=COLORS['text_primary'])
            self.canvas.draw()

        info = f"VERIFICATION DE LA LINEARITE\n\n"
        info += f"Equation: P = {slope:.1f} x (1/V) + {intercept:.1f}\n\n"
        info += f"Coefficient de determination: R2 = {r_squared:.4f}\n\n"

        if r_squared > 0.99:
            info += "Excellente linearite!\nLa loi de Mariotte est verifiee."
        elif r_squared > 0.95:
            info += "Bonne linearite.\nLa loi de Mariotte est globalement verifiee."
        else:
            info += "Linearite moyenne.\nVerifiez les conditions experimentales."

        messagebox.showinfo("Regression lineaire", info)
        self.log_info(f"Regression: P = {slope:.1f}/V + {intercept:.1f}, R2 = {r_squared:.4f}")

    def log_info(self, message):
        """Ajouter un message dans le log"""
        self.info_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

    def quit_application(self):
        """Quitter proprement l'application"""
        response = messagebox.askyesno("Confirmation",
                                      "Voulez-vous vraiment quitter l'application ?")
        if not response:
            return

        if self.is_reading:
            self.log_info("Arret de la lecture serie...")
            self.is_reading = False
            time.sleep(0.5)

        if self.serial_port and self.serial_port.is_open:
            self.log_info("Fermeture du port serie...")
            self.serial_port.close()

        self.log_info("Fermeture de l'application...")
        self.root.quit()
        self.root.destroy()

def main():
    import sys, os
    root = tk.Tk()
    # Charger l'icône
    if getattr(sys, 'frozen', False):
        ico_path = os.path.join(sys._MEIPASS, 'Mariotte_GUI.ico')
    else:
        ico_path = os.path.join(os.path.dirname(__file__), 'Mariotte_GUI.ico')
    if platform.system() == 'Windows':
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
    else:
        png_path = ico_path.replace('.ico', '.png')
        if os.path.exists(png_path):
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(False, img)
    app = MariotteGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
