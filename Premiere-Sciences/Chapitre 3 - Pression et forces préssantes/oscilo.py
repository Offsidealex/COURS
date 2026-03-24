import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import matplotlib.animation as animation
import math

# Pour le son
try:
    import sounddevice as sd
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("Module sounddevice non trouvé. Installez-le avec : pip install sounddevice")

class KnobWidget(tk.Canvas):
    """Bouton rotatif style oscilloscope"""
    def __init__(self, parent, values, initial_index=0, label="", callback=None, color="#4a4a4a", voie_name="", range_min="", range_max="", size="normal", **kwargs):
        # Taille du widget selon le paramètre size
        if size == "small":
            width, height = 80, 80
            radius = 20
        elif size == "large":
            width, height = 150, 150
            radius = 42
        else:  # normal
            width, height = 120, 120
            radius = 32

        super().__init__(parent, width=width, height=height, bg='#f0f0f0',
                        highlightthickness=0, **kwargs)

        self.values = values
        self.current_index = initial_index
        self.label = label
        self.callback = callback
        self.knob_color = color
        self.voie_name = voie_name
        self.range_min = range_min
        self.range_max = range_max
        self.size = size

        self.center_x = width // 2
        self.center_y = (height // 2) - 10
        self.radius = radius

        self.draw_knob()

        # Événements
        self.bind("<Button-1>", self.on_left_click)   # Clic gauche = tourne à gauche
        self.bind("<Button-3>", self.on_right_click)  # Clic droit = tourne à droite
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<MouseWheel>", self.on_scroll)
        self.bind("<Button-4>", lambda e: self.on_scroll_unix(1))
        self.bind("<Button-5>", lambda e: self.on_scroll_unix(-1))

        self.last_angle = 0

    def draw_knob(self):
        """Dessine le bouton rotatif"""
        self.delete("all")

        # Ombre du bouton
        shadow_offset = 2
        self.create_oval(
            self.center_x - self.radius + shadow_offset,
            self.center_y - self.radius + shadow_offset,
            self.center_x + self.radius + shadow_offset,
            self.center_y + self.radius + shadow_offset,
            fill='#aaaaaa', outline=''
        )

        # Cercle du bouton - COULEUR UNIE PLEINE
        self.create_oval(
            self.center_x - self.radius,
            self.center_y - self.radius,
            self.center_x + self.radius,
            self.center_y + self.radius,
            fill=self.knob_color, outline='#333333', width=2
        )

        # Calcul de l'angle
        total_positions = len(self.values)
        angle_range = 270
        angle_per_step = angle_range / (total_positions - 1)
        angle = -135 + (self.current_index * angle_per_step)

        # FLÈCHE NOIRE
        angle_rad = math.radians(angle)
        arrow_length = self.radius - 8
        arrow_tip_x = self.center_x + arrow_length * math.cos(angle_rad)
        arrow_tip_y = self.center_y + arrow_length * math.sin(angle_rad)

        # Base de la flèche (triangle)
        arrow_width = 6 if self.size != "small" else 4
        perp_angle = angle_rad + math.pi / 2
        base_x1 = self.center_x + arrow_width * math.cos(perp_angle)
        base_y1 = self.center_y + arrow_width * math.sin(perp_angle)
        base_x2 = self.center_x - arrow_width * math.cos(perp_angle)
        base_y2 = self.center_y - arrow_width * math.sin(perp_angle)

        # Flèche noire
        self.create_polygon(
            base_x1, base_y1,
            base_x2, base_y2,
            arrow_tip_x, arrow_tip_y,
            fill='#000000', outline='#000000'
        )

        # Point central
        point_size = 3 if self.size != "small" else 2
        self.create_oval(
            self.center_x - point_size, self.center_y - point_size,
            self.center_x + point_size, self.center_y + point_size,
            fill='#222222', outline='#000000'
        )

        # FLÈCHES GAUCHE ET DROITE (sauf pour small)
        if self.size != "small" and self.range_min and self.range_max:
            # Flèche gauche
            left_x = 15 if self.size != "large" else 20
            left_y = self.center_y + 5
            self.create_line(left_x, left_y, left_x, left_y + 10,
                            fill='#000000', width=2)
            self.create_line(left_x, left_y + 10, left_x - 3, left_y + 7,
                            fill='#000000', width=2)
            self.create_line(left_x, left_y + 10, left_x + 3, left_y + 7,
                            fill='#000000', width=2)
            font_size = 7 if self.size != "large" else 8
            self.create_text(
                left_x, left_y + 22,
                text=self.range_min, fill='#000000',
                font=('Arial', font_size, 'bold')
            )

            # Flèche droite
            right_x = int(self.winfo_reqwidth()) - 15 if self.size != "large" else int(self.winfo_reqwidth()) - 20
            right_y = self.center_y + 5
            self.create_line(right_x, right_y, right_x, right_y + 10,
                            fill='#000000', width=2)
            self.create_line(right_x, right_y + 10, right_x - 3, right_y + 7,
                            fill='#000000', width=2)
            self.create_line(right_x, right_y + 10, right_x + 3, right_y + 7,
                            fill='#000000', width=2)
            self.create_text(
                right_x, right_y + 22,
                text=self.range_max, fill='#000000',
                font=('Arial', font_size, 'bold')
            )

        # Nom de la voie
        if self.voie_name:
            font_size = 7 if self.size == "small" else (9 if self.size == "normal" else 10)
            y_offset = 10 if self.size == "small" else 15
            self.create_text(
                self.center_x, self.center_y * 2 + y_offset,
                text=self.voie_name, fill='#000000',
                font=('Arial', font_size, 'bold')
            )

    def on_left_click(self, event):
        """Clic gauche = tourne à gauche (décrémente)"""
        self.decrement()

    def on_right_click(self, event):
        """Clic droit = tourne à droite (incrémente)"""
        self.increment()

    def on_drag(self, event):
        dx = event.x - self.center_x
        dy = event.y - self.center_y
        angle = math.degrees(math.atan2(dy, dx))

        angle_diff = angle - self.last_angle

        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        if abs(angle_diff) > 30:
            if angle_diff > 0:
                self.increment()
            else:
                self.decrement()
            self.last_angle = angle

    def on_scroll(self, event):
        if event.delta > 0:
            self.increment()
        else:
            self.decrement()

    def on_scroll_unix(self, direction):
        if direction > 0:
            self.increment()
        else:
            self.decrement()

    def increment(self):
        if self.current_index < len(self.values) - 1:
            self.current_index += 1
            self.draw_knob()
            if self.callback:
                self.callback(self.values[self.current_index])

    def decrement(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.draw_knob()
            if self.callback:
                self.callback(self.values[self.current_index])

    def set_index(self, index):
        if 0 <= index < len(self.values):
            self.current_index = index
            self.draw_knob()


class OscilloscopeSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Oscilloscope - Lycée Denis Diderot")

        # Obtenir la résolution de l'écran
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Définir la taille de la fenêtre
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.85)

        # Centrer la fenêtre
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#f0f0f0')

        # Paramètres du signal - VALEURS INITIALES
        self.tension_efficace = 6.0
        self.frequence = 50
        self.phase_offset = 0
        self.vertical_offset = 0

        # Paramètres de grille oscilloscope
        self.div_verticales = 8
        self.div_horizontales = 10

        # CALIBRES RÉALISTES
        self.echelles_volts = [5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005]

        self.echelles_temps = [
            100000, 50000, 25000, 10000, 5000, 2500, 1000, 500, 250,
            100, 50, 25, 10, 5, 2.5, 1,
            0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.0025, 0.001,
            0.0005, 0.00025, 0.0001, 0.00005, 0.000025, 0.00001, 0.000005
        ]

        # Valeurs pour les déplacements
        self.position_h_values = list(range(-50, 51, 5))
        self.position_v_values = list(range(-50, 51, 5))

        # Index actuels - VALEURS INITIALES
        self.index_temps = 13  # 5 ms
        self.index_volts = 0   # 5 V
        self.index_position_h = len(self.position_h_values) // 2
        self.index_position_v = len(self.position_v_values) // 2

        # Son - IMPORTANT: initialiser dans le bon ordre
        self.sound_phase = 0
        self.sound_playing = False
        self.sound_stream = None

        self.updating = False

        self.creer_interface()

        # Animation avec cache_frame_data=False pour éviter l'avertissement
        self.ani = animation.FuncAnimation(
            self.fig, self.update_graphique,
            interval=50, blit=False, cache_frame_data=False
        )

    def creer_interface(self):
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main_frame, width=400, bg='#f0f0f0')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        # === CADRE BLEU AVEC BORDURE MINIMALE ===
        scope_container = tk.Frame(left_frame, bg='#4466aa', relief=tk.FLAT, borderwidth=0)
        scope_container.pack(fill=tk.BOTH, expand=True)

        # Titre en haut
        title_frame = tk.Frame(scope_container, bg='#4466aa', height=25)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="Lycée Denis Diderot", bg='#4466aa',
                fg='#ffffff', font=('Arial', 11, 'bold')).pack(pady=3)

        # Frame pour le graphique avec bordure noire de 5mm (19 pixels)
        graph_container = tk.Frame(scope_container, bg='#000000')
        graph_container.pack(fill=tk.BOTH, expand=True, padx=19, pady=19)

        # === OSCILLOSCOPE TRÈS AGRANDI ===
        available_height = int(self.root.winfo_screenheight() * 0.85 - 100)
        available_width = int(self.root.winfo_screenwidth() * 0.9 - 500)

        scope_size = min(available_height, available_width)
        fig_size = scope_size / 100

        self.fig = Figure(figsize=(fig_size, fig_size), dpi=100, facecolor='#000000')
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
        self.ax = self.fig.add_subplot(111)

        # Style oscilloscope
        self.ax.set_facecolor('#000000')
        self.ax.spines['bottom'].set_color('#ffffff')
        self.ax.spines['top'].set_color('#ffffff')
        self.ax.spines['left'].set_color('#ffffff')
        self.ax.spines['right'].set_color('#ffffff')
        self.ax.tick_params(colors='#ffffff', which='both')

        # Enlever les graduations numériques
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])

        self.ax.set_xlabel('', fontsize=1)
        self.ax.set_ylabel('', fontsize=1)
        self.ax.set_title('', fontsize=1)

        # Ligne du signal - ROUGE
        self.line, = self.ax.plot([], [], color='#ff0000', linewidth=2.5,
                                  antialiased=True, zorder=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # === INFO EN BAS ===
        info_overlay_frame = tk.Frame(scope_container, bg='#4466aa')
        info_overlay_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=5)

        self.ch1_label = tk.Label(info_overlay_frame, text="", bg='#4466aa',
                                 fg='#ffffff', font=('Arial', 10, 'bold'), anchor='w')
        self.ch1_label.pack(side=tk.LEFT)

        middle_frame = tk.Frame(info_overlay_frame, bg='#4466aa')
        middle_frame.pack(side=tk.LEFT, expand=True)

        self.time_label = tk.Label(middle_frame, text="", bg='#4466aa',
                                   fg='#ffffff', font=('Arial', 10, 'bold'))
        self.time_label.pack()

        # === CONTRÔLES ===
        tk.Label(right_frame, text="PARAMÈTRES", bg='#f0f0f0',
                 font=('Arial', 13, 'bold')).pack(pady=(0, 10))

        # === TENSION EFFICACE ===
        ueff_frame = tk.LabelFrame(right_frame, text="Tension efficace Ueff (V)",
                                   bg='#f0f0f0', font=('Arial', 9, 'bold'),
                                   padx=10, pady=8)
        ueff_frame.pack(fill=tk.X, pady=3)

        ueff_control = tk.Frame(ueff_frame, bg='#f0f0f0')
        ueff_control.pack(fill=tk.X)

        tk.Button(ueff_control, text="−", command=lambda: self.change_ueff(-0.1),
                 font=('Arial', 11, 'bold'), width=3, bg='#d0d0d0').pack(side=tk.LEFT, padx=2)

        self.ueff_var = tk.DoubleVar(value=self.tension_efficace)
        self.ueff_spinbox = tk.Spinbox(
            ueff_control, from_=0, to=15, increment=0.1,
            textvariable=self.ueff_var, font=('Courier', 11, 'bold'),
            fg='#000000', justify=tk.CENTER, width=10,
            command=self.update_ueff
        )
        self.ueff_spinbox.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.ueff_spinbox.bind('<Return>', lambda e: self.update_ueff())

        tk.Button(ueff_control, text="+", command=lambda: self.change_ueff(0.1),
                 font=('Arial', 11, 'bold'), width=3, bg='#d0d0d0').pack(side=tk.LEFT, padx=2)

        # === FRÉQUENCE ===
        freq_frame = tk.LabelFrame(right_frame, text="Fréquence f (Hz)",
                                   bg='#f0f0f0', font=('Arial', 9, 'bold'),
                                   padx=10, pady=8)
        freq_frame.pack(fill=tk.X, pady=3)

        freq_control = tk.Frame(freq_frame, bg='#f0f0f0')
        freq_control.pack(fill=tk.X)

        tk.Button(freq_control, text="−", command=lambda: self.change_freq(-10),
                 font=('Arial', 11, 'bold'), width=3, bg='#d0d0d0').pack(side=tk.LEFT, padx=2)

        self.freq_var = tk.DoubleVar(value=self.frequence)
        self.freq_spinbox = tk.Spinbox(
            freq_control, from_=1, to=20000, increment=1,
            textvariable=self.freq_var, font=('Courier', 11, 'bold'),
            fg='#000000', justify=tk.CENTER, width=10,
            command=self.update_freq
        )
        self.freq_spinbox.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.freq_spinbox.bind('<Return>', lambda e: self.update_freq())

        tk.Button(freq_control, text="+", command=lambda: self.change_freq(10),
                 font=('Arial', 11, 'bold'), width=3, bg='#d0d0d0').pack(side=tk.LEFT, padx=2)

        # BOUTON SON
        sound_btn_frame = tk.Frame(freq_frame, bg='#f0f0f0')
        sound_btn_frame.pack(pady=(8, 0))

        if SOUND_AVAILABLE:
            self.sound_button = tk.Button(
                sound_btn_frame, text="🔊 Écouter le son",
                command=self.toggle_sound,
                bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'),
                relief=tk.RAISED, borderwidth=3, padx=12, pady=4,
                cursor='hand2'
            )
            self.sound_button.pack()

        # Séparateur
        separator = tk.Frame(right_frame, height=2, bg='#cccccc')
        separator.pack(fill=tk.X, pady=10)

        # === TITRE RÉGLAGES ===
        reglages_header = tk.Frame(right_frame, bg='#e0e0e0', relief=tk.RAISED, borderwidth=1)
        reglages_header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(reglages_header, text="RÉGLAGES OSCILLOSCOPE", bg='#e0e0e0',
                 font=('Arial', 11, 'bold'), pady=6).pack()

        # === BOUTONS ROTATIFS EN DEUX COLONNES ===
        knobs_container = tk.Frame(right_frame, bg='#f0f0f0')
        knobs_container.pack(fill=tk.BOTH, expand=True)

        # COLONNE 1 : POSITION VERTICALE + VOLTS/DIV
        col1 = tk.Frame(knobs_container, bg='#f0f0f0')
        col1.pack(side=tk.LEFT, expand=True, padx=5)

        # Position verticale (petit, rouge)
        tk.Label(col1, text="POSITION Y", bg='#f0f0f0',
                 font=('Arial', 8, 'bold')).pack(pady=(0, 3))

        self.position_v_knob = KnobWidget(
            col1,
            values=self.position_v_values,
            initial_index=self.index_position_v,
            label="POSITION_V",
            callback=self.on_position_v_change,
            color='#ff8888',
            voie_name='↑↓',
            range_min='',
            range_max='',
            size='small'
        )
        self.position_v_knob.pack(pady=(0, 10))

        # VOLTS/DIV (normal, rouge)
        tk.Label(col1, text="VOLTS / DIV.", bg='#f0f0f0',
                 font=('Arial', 9, 'bold')).pack(pady=(0, 3))

        self.volts_knob = KnobWidget(
            col1,
            values=self.echelles_volts,
            initial_index=self.index_volts,
            label="VOLTS/DIV",
            callback=self.on_volts_change,
            color='#ff8888',
            voie_name='Y1',
            range_min='5V',
            range_max='5mV',
            size='normal'
        )
        self.volts_knob.pack()

        # COLONNE 2 : POSITION HORIZONTALE + TIME/DIV
        col2 = tk.Frame(knobs_container, bg='#f0f0f0')
        col2.pack(side=tk.LEFT, expand=True, padx=5)

        # Position horizontale (large, bleu)
        tk.Label(col2, text="POSITION HORIZ.", bg='#f0f0f0',
                 font=('Arial', 9, 'bold')).pack(pady=(0, 3))

        self.position_h_knob = KnobWidget(
            col2,
            values=self.position_h_values,
            initial_index=self.index_position_h,
            label="POSITION_H",
            callback=self.on_position_h_change,
            color='#66dddd',
            voie_name='← →',
            range_min='←',
            range_max='→',
            size='large'
        )
        self.position_h_knob.pack(pady=(0, 10))

        # TIME/DIV (normal, cyan)
        tk.Label(col2, text="SEC / DIV.", bg='#f0f0f0',
                 font=('Arial', 9, 'bold')).pack(pady=(0, 3))

        self.temps_knob = KnobWidget(
            col2,
            values=self.echelles_temps,
            initial_index=self.index_temps,
            label="TIME/DIV",
            callback=self.on_temps_change,
            color='#66dddd',
            voie_name='BASE DE TEMPS',
            range_min='100s',
            range_max='5ns',
            size='normal'
        )
        self.temps_knob.pack()

        self.update_info()

        # Boutons en bas
        btn_frame = tk.Frame(right_frame, bg='#f0f0f0')
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Réinitialiser", bg='#d0d0d0',
                 command=self.reinitialiser, font=('Arial', 9),
                 relief=tk.RAISED, borderwidth=2).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Quitter", bg='#d0d0d0',
                 command=self.quit_app, font=('Arial', 9),
                 relief=tk.RAISED, borderwidth=2).pack(fill=tk.X, pady=2)

    def on_position_h_change(self, value):
        """Callback du bouton de position horizontale"""
        self.index_position_h = self.position_h_values.index(value)
        temps_div = self.echelles_temps[self.index_temps]
        self.phase_offset = value * temps_div * 0.05

    def on_position_v_change(self, value):
        """Callback du bouton de position verticale"""
        self.index_position_v = self.position_v_values.index(value)
        volts_div = self.echelles_volts[self.index_volts]
        self.vertical_offset = value * volts_div * 0.02

    def change_ueff(self, delta):
        new_val = max(0, min(15, self.tension_efficace + delta))
        self.ueff_var.set(round(new_val, 2))
        self.update_ueff()

    def change_freq(self, delta):
        new_val = max(1, min(20000, self.frequence + delta))
        self.freq_var.set(int(new_val))
        self.update_freq()

    def update_ueff(self):
        try:
            self.tension_efficace = float(self.ueff_var.get())
            self.tension_efficace = max(0, min(15, self.tension_efficace))
            self.update_info()
        except:
            pass

    def update_freq(self):
        try:
            self.frequence = float(self.freq_var.get())
            self.frequence = max(1, min(20000, self.frequence))
            self.update_info()
        except:
            pass

    # === SECTION AUDIO COMPLÈTE ===

    def generate_audio_callback(self, outdata, frames, time_info, status):
        """Callback pour générer le son en temps réel"""
        if status:
            print(f"Audio status: {status}")

        try:
            # Générer le temps
            t = (np.arange(frames) + self.sound_phase) / 44100.0
            self.sound_phase += frames

            # Générer le signal sinusoïdal
            signal = 0.4 * np.sin(2 * np.pi * self.frequence * t)

            # Remplir le buffer de sortie
            outdata[:] = signal.reshape(-1, 1)

        except Exception as e:
            print(f"Erreur callback: {e}")
            outdata.fill(0)

    def toggle_sound(self):
        """Active/désactive le son"""
        if not SOUND_AVAILABLE:
            return

        if self.sound_playing:
            self.stop_sound()
        else:
            self.start_sound()

    def start_sound(self):
        """Démarre la lecture du son"""
        try:
            print(f"\n=== Démarrage du son à {self.frequence} Hz ===")

            # Réinitialiser la phase
            self.sound_phase = 0

            # Arrêter tout son existant
            sd.stop()

            # Créer le stream audio
            self.sound_stream = sd.OutputStream(
                samplerate=44100,
                channels=1,
                dtype='float32',
                callback=self.generate_audio_callback,
                blocksize=2048,
                latency='low'
            )

            # Démarrer le stream
            self.sound_stream.start()
            self.sound_playing = True
            self.sound_button.config(text="🔇 Arrêter le son", bg='#f44336')

            print("✓ Son démarré avec succès!")
            print(f"  Fréquence: {self.frequence} Hz")
            print(f"  Sample rate: 44100 Hz")
            print(f"  Canaux: 1 (mono)")

        except Exception as e:
            print(f"✗ Erreur lors du démarrage du son:")
            print(f"  {type(e).__name__}: {e}")

            if self.sound_stream:
                try:
                    self.sound_stream.close()
                except:
                    pass
                self.sound_stream = None

            self.sound_playing = False
            self.sound_button.config(text="🔊 Écouter le son", bg='#4CAF50')

    def stop_sound(self):
        """Arrête la lecture du son"""
        print("\n=== Arrêt du son ===")

        try:
            self.sound_playing = False

            if self.sound_stream:
                self.sound_stream.stop()
                self.sound_stream.close()
                self.sound_stream = None
                print("✓ Stream audio fermé")

            sd.stop()

            if SOUND_AVAILABLE:
                self.sound_button.config(text="🔊 Écouter le son", bg='#4CAF50')

            print("✓ Son arrêté")

        except Exception as e:
            print(f"✗ Erreur lors de l'arrêt: {e}")

    # === FIN SECTION AUDIO ===

    def on_volts_change(self, value):
        self.index_volts = self.echelles_volts.index(value)
        self.update_info()

    def on_temps_change(self, value):
        self.index_temps = self.echelles_temps.index(value)
        self.update_info()

    def format_time_value(self, ms_value):
        """Formate la valeur de temps"""
        if ms_value >= 1000:
            return f"{ms_value/1000:.0f} s"
        elif ms_value >= 1:
            return f"{ms_value:.0f} ms"
        elif ms_value >= 0.001:
            return f"{ms_value*1000:.0f} µs"
        else:
            return f"{ms_value*1000000:.0f} ns"

    def format_volts_value(self, v_value):
        """Formate la valeur de tension"""
        if v_value >= 1:
            return f"{v_value:.0f} V"
        else:
            return f"{v_value*1000:.0f} mV"

    def update_info(self):
        volts_value = self.echelles_volts[self.index_volts]
        temps_value = self.echelles_temps[self.index_temps]

        self.ch1_label.config(text=f"CH1  {self.format_volts_value(volts_value)}")
        self.time_label.config(text=f"M  {self.format_time_value(temps_value)}")

    def dessiner_grille_oscilloscope(self, xlim, ylim):
        """Dessine la grille"""

        for line in self.ax.lines[1:]:
            line.remove()

        x_min, x_max = xlim
        y_min, y_max = ylim

        x_range = x_max - x_min
        y_range = y_max - y_min

        x_div = x_range / self.div_horizontales
        y_div = y_range / self.div_verticales

        # SOUS-DIVISIONS
        for i in range(self.div_horizontales * 5 + 1):
            x = x_min + i * (x_div / 5)
            self.ax.axvline(x=x, color='#777777', linewidth=0.5, alpha=0.8, zorder=1)

        for i in range(self.div_verticales * 5 + 1):
            y = y_min + i * (y_div / 5)
            self.ax.axhline(y=y, color='#777777', linewidth=0.5, alpha=0.8, zorder=1)

        # DIVISIONS PRINCIPALES
        for i in range(self.div_horizontales + 1):
            x = x_min + i * x_div
            self.ax.axvline(x=x, color='#ffffff', linewidth=1.0, alpha=0.6, zorder=2)

        for i in range(self.div_verticales + 1):
            y = y_min + i * y_div
            self.ax.axhline(y=y, color='#ffffff', linewidth=1.0, alpha=0.6, zorder=2)

        # Axes centraux
        self.ax.axhline(y=0, color='#ffffff', linewidth=1.5, alpha=0.8, zorder=3)
        self.ax.axvline(x=x_min + x_range/2, color='#ffffff', linewidth=1.5, alpha=0.7, zorder=3)

    def update_graphique(self, frame):
        volts_div = self.echelles_volts[self.index_volts]
        temps_div = self.echelles_temps[self.index_temps]

        y_max = volts_div * (self.div_verticales / 2)
        x_max = temps_div * self.div_horizontales

        # Signal avec décalages horizontal et vertical
        t = np.linspace(self.phase_offset, x_max + self.phase_offset, 2000) / 1000
        umax = self.tension_efficace * np.sqrt(2)
        u = umax * np.sin(2 * np.pi * self.frequence * t) + self.vertical_offset

        self.line.set_data((t * 1000) - self.phase_offset, u)

        xlim = (0, x_max)
        ylim = (-y_max, y_max)

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        self.dessiner_grille_oscilloscope(xlim, ylim)

        return self.line,

    def reinitialiser(self):
        if self.sound_playing:
            self.stop_sound()

        # Remettre les valeurs initiales
        self.tension_efficace = 6.0
        self.frequence = 50
        self.index_temps = 13  # 5 ms
        self.index_volts = 0   # 5 V
        self.index_position_h = len(self.position_h_values) // 2
        self.index_position_v = len(self.position_v_values) // 2
        self.phase_offset = 0
        self.vertical_offset = 0

        self.ueff_var.set(self.tension_efficace)
        self.freq_var.set(self.frequence)

        self.volts_knob.set_index(self.index_volts)
        self.temps_knob.set_index(self.index_temps)
        self.position_h_knob.set_index(self.index_position_h)
        self.position_v_knob.set_index(self.index_position_v)

        self.update_info()

    def quit_app(self):
        if self.sound_playing:
            self.stop_sound()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = OscilloscopeSimulator(root)
    root.mainloop()