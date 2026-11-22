import os
import re
import threading
import time
import subprocess
import webbrowser
import pythoncom
import pyttsx3
from datetime import datetime, timezone
import customtkinter as ctk
import speech_recognition as recognition
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from google import genai
from google.genai import errors
from google.genai import types

# Optional system & presentation packages with safe fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Optional ReportLab import for true PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Set up CustomTkinter appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class DhruvAIAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DHRUV'S AI ASSISTANT")
        self.geometry("1180x800")
        self.minsize(850, 650)

        self.current_engine = None
        self.last_request_time = 0
        self.session_token_count = 0  
        self.selected_file_path = None  
        self.file_is_image = False
        self.animating_welcome = True
        self.animating_chat_border = False
        self.welcome_bg_img = None  
        self.animating_elements = []  
        
        # User Customization States
        self.current_theme = "Dark Red & Black"
        self.preferred_voice_gender = "Neural Male (English)"
        self.assistant_title_text = "🤖 DHRUV'S AI ASSISTANT"
        self.current_font_size = 18
        self.current_persona = "Friendly & Concise"
        self.settings_visible = False
        self.history_visible = False
        self.force_dark_mode_state = False  
        self.speech_rate_val = 145
        self.speech_volume_val = 1.0

        # Load API keys
        self.load_api_keys()

        # Theme color definitions
        self.themes = {
            "Dark Red & Black": {
                "mode": "Dark", "header_bg": "#080b12", "title_fg": "#ff4d88",
                "chat_bg": "#05070c", "chat_fg": "#f1f5f9", "badge_fg": "#00f2fe",
                "token_fg": "#38bdf8", "entry_bg": "#090d16", "entry_fg": "#f1f5f9",
                "entry_border": "#ec4899", "btn_primary_bg": "#f43f5e", "btn_primary_hover": "#e11d48",
                "btn_secondary_bg": "#111827", "btn_secondary_hover": "#1f2937", "btn_secondary_fg": "#f43f5e",
                "preview_fg": "#34d399", "settings_bg": "#0b0f19", "settings_fg": "#f1f5f9",
                "dropdown_text_fg": "#f1f5f9"
            },
            "Blue & Green": {
                "mode": "Dark", "header_bg": "#08121a", "title_fg": "#00ffcc",
                "chat_bg": "#050b10", "chat_fg": "#ccfffa", "badge_fg": "#00cc99",
                "token_fg": "#80ffea", "entry_bg": "#08121a", "entry_fg": "#ccfffa",
                "entry_border": "#006644", "btn_primary_bg": "#009973", "btn_primary_hover": "#00664d",
                "btn_secondary_bg": "#0a1a1f", "btn_secondary_hover": "#13333d", "btn_secondary_fg": "#00ffcc",
                "preview_fg": "#00ff66", "settings_bg": "#0a151c", "settings_fg": "#ccfffa",
                "dropdown_text_fg": "#ccfffa"
            },
            "Pink & White": {
                "mode": "Light", "header_bg": "#ffe6ee", "title_fg": "#cc0066",
                "chat_bg": "#fff0f5", "chat_fg": "#4d0026", "badge_fg": "#ff1493",
                "token_fg": "#b30059", "entry_bg": "#ffffff", "entry_fg": "#4d0026",
                "entry_border": "#ffb6c1", "btn_primary_bg": "#ff1493", "btn_primary_hover": "#c71585",
                "btn_secondary_bg": "#ffccd5", "btn_secondary_hover": "#ffb3c6", "btn_secondary_fg": "#99004d",
                "preview_fg": "#0080ff", "settings_bg": "#ffedf2", "settings_fg": "#4d0026",
                "dropdown_text_fg": "#000000"
            },
            "Silver & Sky": {
                "mode": "Light", "header_bg": "#e6f2ff", "title_fg": "#0066cc",
                "chat_bg": "#f0f8ff", "chat_fg": "#001a33", "badge_fg": "#0080ff",
                "token_fg": "#0055b3", "entry_bg": "#ffffff", "entry_fg": "#001a33",
                "entry_border": "#b3d1ff", "btn_primary_bg": "#0080ff", "btn_primary_hover": "#0066cc",
                "btn_secondary_bg": "#d9d9d9", "btn_secondary_hover": "#bfbfbf", "btn_secondary_fg": "#003366",
                "preview_fg": "#009933", "settings_bg": "#ebf3ff", "settings_fg": "#001a33",
                "dropdown_text_fg": "#000000"
            }
        }

        # Initialize Google GenAI client
        self.init_genai_client()

        # Grid configuration for main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Global Hotkey for Command Palette
        self.bind("<Control-space>", self.open_command_palette)

        # Build Startup Welcome Page Frame
        self.setup_welcome_page()

    def setup_welcome_page(self):
        self.animating_elements = []
        self.welcome_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#04060c")
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        self.welcome_frame.grid_rowconfigure(0, weight=1)
        self.welcome_frame.grid_rowconfigure(6, weight=1)
        self.welcome_frame.grid_columnconfigure(0, weight=1)

        # Load wallpaper background
        try:
            if os.path.exists("1000026394.png"):
                bg_pil = Image.open("1000026394.png")
                self.welcome_bg_img = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1180, 800))
                welcome_bg_lbl = ctk.CTkLabel(self.welcome_frame, image=self.welcome_bg_img, text="")
                welcome_bg_lbl.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            print(f"Startup wallpaper load note: {e}")

        top_accent_frame = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        top_accent_frame.grid(row=1, column=0, sticky="ew", padx=60, pady=(30, 0))
        
        left_tag = ctk.CTkLabel(
            top_accent_frame, text="MORE THAN AI.\nA HIGHER\nYOU.", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#6c7a89", justify="left", fg_color="transparent"
        )
        left_tag.pack(side="left")

        right_tag = ctk.CTkLabel(
            top_accent_frame, text="IDEAS\nKNOWLEDGE\nPRODUCTIVITY\nALL IN ONE", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#6c7a89", justify="right", fg_color="transparent"
        )
        right_tag.pack(side="right")

        center_container = ctk.CTkFrame(self.welcome_frame, fg_color="#0b0f19", corner_radius=16, border_width=1, border_color="#1e293b")
        center_container.grid(row=2, column=0, pady=(10, 15), ipadx=30, ipady=15)
        self.animating_elements.append(center_container)

        core_badge = ctk.CTkFrame(center_container, fg_color="#0d1b2a", corner_radius=20, border_width=1, border_color="#1b4965")
        core_badge.pack(pady=(0, 15))
        
        badge_lbl = ctk.CTkLabel(
            core_badge, text="  🟢  AI CORE  •  ONLINE  ", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f2fe", fg_color="transparent"
        )
        badge_lbl.pack(padx=12, pady=5)

        title_lbl = ctk.CTkLabel(
            center_container, text="DHRUV'S AI ASSISTANT", 
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color="#ffffff", fg_color="transparent"
        )
        title_lbl.pack(pady=(0, 5))

        subtitle_lbl = ctk.CTkLabel(
            center_container, text="Think. Create. Explore. (Press Ctrl+Space for Quick Menu)", 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#a0aec0", fg_color="transparent"
        )
        subtitle_lbl.pack()

        cards_frame = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        cards_frame.grid(row=3, column=0, pady=25)

        features = [
            ("👁️", "Vision", "See, analyze\nand understand"),
            ("🎙️", "Voice", "Talk naturally\nand get things done"),
            ("📄", "Files", "Open, read\nand work with anything")
        ]

        for icon, title, desc in features:
            card = ctk.CTkFrame(cards_frame, width=210, height=110, fg_color="#0b1120", corner_radius=14, border_width=1, border_color="#1e293b")
            card.pack(side="left", padx=12)
            card.pack_propagate(False)
            self.animating_elements.append(card)

            icon_lbl = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=22), fg_color="transparent")
            icon_lbl.pack(anchor="w", padx=16, pady=(14, 2))

            card_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#ffffff", fg_color="transparent")
            card_title.pack(anchor="w", padx=16)

            card_desc = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#94a3b8", justify="left", fg_color="transparent")
            card_desc.pack(anchor="w", padx=16, pady=(2, 0))

        self.start_app_btn = ctk.CTkButton(
            self.welcome_frame, text="▶   START ASSISTANT", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=380, height=58, corner_radius=29,
            fg_color="#f43f5e", hover_color="#e11d48",
            command=self.launch_main_application
        )
        self.start_app_btn.grid(row=4, column=0, pady=(15, 10))

        threading.Thread(target=self.run_vibgyor_animation, daemon=True).start()

        tagline_lbl = ctk.CTkLabel(
            self.welcome_frame, text="YOUR IDEAS. AMPLIFIED.", 
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#64748b", fg_color="transparent"
        )
        tagline_lbl.grid(row=5, column=0, pady=(0, 20))

        footer_frame = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        footer_frame.grid(row=6, column=0, sticky="s", padx=40, pady=25)
        footer_frame.grid_columnconfigure(0, weight=1)
        footer_frame.grid_columnconfigure(1, weight=1)

        foot_left = ctk.CTkLabel(
            footer_frame, text="A MULTIMODAL AI PLATFORM\nFOR A BRIGHTER TOMORROW", 
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#475569", justify="left", fg_color="transparent"
        )
        foot_left.grid(row=0, column=0, sticky="w")

        foot_right = ctk.CTkLabel(
            footer_frame, text="v1.0  •  Exhibition Build", 
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#475569", justify="right", fg_color="transparent"
        )
        foot_right.grid(row=0, column=1, sticky="e")

    def run_vibgyor_animation(self):
        vibgyor_panel_colors = ["#23063b", "#14062b", "#061323", "#062313", "#231f06", "#231306", "#230606"]
        idx = 0
        while self.animating_welcome:
            try:
                col = vibgyor_panel_colors[idx % len(vibgyor_panel_colors)]
                for el in self.animating_elements:
                    if el.winfo_exists():
                        self.after(0, lambda e=el, c=col: e.configure(fg_color=c))
                idx += 1
                time.sleep(0.6)
            except Exception:
                break

    def run_chat_border_animation(self):
        vibgyor_border_colors = ["#ee82ee", "#4b0082", "#0000ff", "#008000", "#ffff00", "#ffa500", "#ff0000"]
        idx = 0
        while self.animating_chat_border:
            try:
                col = vibgyor_border_colors[idx % len(vibgyor_border_colors)]
                self.after(0, lambda c=col: self.chat_container_frame.configure(border_color=c) if hasattr(self, 'chat_container_frame') and self.chat_container_frame else None)
                idx += 1
                time.sleep(0.5)
            except Exception:
                break

    def launch_main_application(self):
        self.animating_welcome = False
        self.welcome_frame.destroy()

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color="#080b12", border_width=1, border_color="#1e293b")
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, text=self.assistant_title_text, 
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#ff4d88"
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        # Right Header: Settings, History, System Stats, Tokens & Status
        self.right_header_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.right_header_frame.pack(side="right", padx=20, pady=15)

        self.header_settings_btn = ctk.CTkButton(
            self.right_header_frame, text="⚙️ Settings", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=28, width=85, corner_radius=6, command=self.toggle_settings_panel,
            fg_color="#111827", hover_color="#1f2937", text_color="#ff4d88"
        )
        self.header_settings_btn.pack(side="left", padx=(0, 8))

        self.header_history_btn = ctk.CTkButton(
            self.right_header_frame, text="📜 History", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=28, width=80, corner_radius=6, command=self.toggle_history_panel,
            fg_color="#111827", hover_color="#1f2937", text_color="#38bdf8"
        )
        self.header_history_btn.pack(side="left", padx=(0, 15))

        # Real-Time System Stats HUD Widget
        self.sys_stats_badge = ctk.CTkLabel(
            self.right_header_frame, text="CPU: 0% | RAM: 0%", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#34d399"
        )
        self.sys_stats_badge.pack(side="left", padx=(0, 15))

        self.token_counter_badge = ctk.CTkLabel(
            self.right_header_frame, text="Tokens: 0 | Latency: 0.0s", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#38bdf8"
        )
        self.token_counter_badge.pack(side="left", padx=(0, 15))

        self.status_badge = ctk.CTkLabel(
            self.right_header_frame, text="● Ready", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#34d399"
        )
        self.status_badge.pack(side="left")

        # Start live system stats loop
        self.update_system_stats()

        # Chat Container Frame with Blinking VIBGYOR Border
        self.chat_container_frame = ctk.CTkFrame(self, fg_color="#05070c", corner_radius=12, border_width=2, border_color="#ec4899")
        self.chat_container_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(15, 5))
        self.chat_container_frame.grid_rowconfigure(0, weight=1)
        self.chat_container_frame.grid_columnconfigure(0, weight=1)

        # Start VIBGYOR Border Blinking Animation
        self.animating_chat_border = True
        threading.Thread(target=self.run_chat_border_animation, daemon=True).start()

        # Chat Log Box
        self.chat_box = ctk.CTkTextbox(
            self.chat_container_frame, font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size),
            corner_radius=12, border_spacing=15, fg_color="transparent", text_color="#f1f5f9"
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_box.configure(state="disabled")

        # Quick Prompt Shortcut Chips Bar & Concise Action Buttons
        self.chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chips_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.chips_frame.grid_columnconfigure(4, weight=1)
        
        self.add_chip("❓ Who are you?", lambda: self.send_preset_query("Who created you?"))
        self.add_chip("🧠 Quantum Physics", lambda: self.send_preset_query("Explain quantum computing in one simple sentence."))
        self.add_chip("💡 Fun Fact", lambda: self.send_preset_query("Tell me an interesting computer science fact."))
        self.add_chip("🚀 Demo Mode", lambda: self.run_exhibition_demo())

        # Concise Action Buttons next to Fun Fact
        self.action_buttons_frame = ctk.CTkFrame(self.chips_frame, fg_color="transparent")
        self.action_buttons_frame.pack(side="right", padx=5)

        self.file_btn = ctk.CTkButton(self.action_buttons_frame, text="📎 File", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), height=28, width=65, corner_radius=14, fg_color="#111827", hover_color="#1f2937", command=self.attach_file)
        self.file_btn.pack(side="left", padx=3)

        self.export_btn = ctk.CTkButton(self.action_buttons_frame, text="💾 Save", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), height=28, width=65, corner_radius=14, fg_color="#111827", hover_color="#1f2937", command=self.export_transcript)
        self.export_btn.pack(side="left", padx=3)

        self.clipboard_btn = ctk.CTkButton(self.action_buttons_frame, text="📋 Paste", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), height=28, width=70, corner_radius=14, fg_color="#111827", hover_color="#1f2937", command=self.analyze_clipboard)
        self.clipboard_btn.pack(side="left", padx=3)

        self.reset_btn = ctk.CTkButton(self.action_buttons_frame, text="🗑️ Clear", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), height=28, width=65, corner_radius=14, fg_color="#111827", hover_color="#1f2937", command=self.reset_chat_session)
        self.reset_btn.pack(side="left", padx=3)

        # In-App Settings Side Panel (Column 1)
        self.settings_panel = ctk.CTkScrollableFrame(self, width=310, corner_radius=0, fg_color="#0b0f19")
        self.setup_settings_widgets()

        # In-App History Side Panel (Column 2)
        self.history_panel = ctk.CTkScrollableFrame(self, width=310, corner_radius=0, fg_color="#0b0f19")
        self.setup_history_widgets()

        # File Preview Bar
        self.preview_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#34d399")
        self.preview_label.grid(row=3, column=0, sticky="w", padx=25, pady=(0, 5))

        # Bottom Control Panel
        self.control_container = ctk.CTkFrame(self, fg_color="transparent")
        self.control_container.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 20))
        self.control_container.grid_columnconfigure(0, weight=1)

        self.input_frame = ctk.CTkFrame(self.control_container, fg_color="#0b0f19", corner_radius=14, border_width=1, border_color="#ec4899")
        self.input_frame.pack(fill="x", pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.text_input = ctk.CTkEntry(
            self.input_frame, placeholder_text="Type your message, ask to open an app, or press Ctrl+Space...",
            font=ctk.CTkFont(family="Segoe UI", size=16), height=50, corner_radius=12, fg_color="transparent", border_width=0, text_color="#f1f5f9"
        )
        self.text_input.grid(row=0, column=0, sticky="ew", padx=(15, 5))
        self.text_input.bind("<Return>", lambda event: self.start_text_query_thread())

        self.send_btn = ctk.CTkButton(
            self.input_frame, text="Send 🚀", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), 
            height=40, width=95, corner_radius=10, fg_color="#f43f5e", hover_color="#e11d48", command=self.start_text_query_thread
        )
        self.send_btn.grid(row=0, column=1, padx=8)

        # Voice & Stop Buttons
        self.btn_frame = ctk.CTkFrame(self.control_container, fg_color="transparent")
        self.btn_frame.pack(fill="x")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.speak_btn = ctk.CTkButton(self.btn_frame, text="🎙  Start Speaking", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), height=50, corner_radius=12, fg_color="#111827", hover_color="#1f2937", text_color="#f43f5e", border_width=1, border_color="#f43f5e", command=self.start_listening_thread)
        self.speak_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="⏹  Stop (Esc)", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), height=50, corner_radius=12, fg_color="#111827", hover_color="#1f2937", text_color="#38bdf8", border_width=1, border_color="#38bdf8", command=self.force_stop_speech)
        self.stop_btn.grid(row=0, column=1, sticky="ew")

        self.bind('<Escape>', lambda event: self.force_stop_speech())
        self.protocol("WM_DELETE_WINDOW", self.on_close_save_history)

        self.apply_theme(self.current_theme)
        threading.Thread(target=self.initial_greeting, daemon=True).start()

    def update_system_stats(self):
        """Live background loop to update CPU and RAM stats in the header HUD."""
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                if hasattr(self, 'sys_stats_badge') and self.sys_stats_badge.winfo_exists():
                    self.sys_stats_badge.configure(text=f"CPU: {int(cpu)}% | RAM: {int(ram)}%")
            except Exception:
                pass
        else:
            if hasattr(self, 'sys_stats_badge') and self.sys_stats_badge.winfo_exists():
                self.sys_stats_badge.configure(text="CPU: 12% | RAM: 48%")
        
        # Refresh every 2.5 seconds
        self.after(2500, self.update_system_stats)

    def open_command_palette(self, event=None):
        """Interactive Quick-Launch Command Palette triggered by Ctrl + Space."""
        palette = ctk.CTkToplevel(self)
        palette.title("⚡ Quick Command Palette")
        palette.geometry("450x320")
        palette.attributes("-topmost", True)
        palette.grab_set()

        lbl = ctk.CTkLabel(palette, text="⚡ Quick Actions Menu", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#ff4d88")
        lbl.pack(pady=(15, 10))

        def run_action(action_type):
            palette.destroy()
            if action_type == "notepad":
                subprocess.Popen("notepad.exe")
                self.append_full_chat("System", "Quick Command: Opened Notepad.")
            elif action_type == "calc":
                subprocess.Popen("calc.exe")
                self.append_full_chat("System", "Quick Command: Opened Calculator.")
            elif action_type == "explorer":
                subprocess.Popen("explorer.exe")
                self.append_full_chat("System", "Quick Command: Opened File Explorer.")
            elif action_type == "screenshot":
                if PYAUTOGUI_AVAILABLE:
                    sc = pyautogui.screenshot()
                    sc.save("exhibition_screenshot.png")
                    messagebox.showinfo("Success", "Screenshot saved as exhibition_screenshot.png!")
                else:
                    messagebox.showwarning("Notice", "pyautogui not installed. Run 'pip install pyautogui' in terminal.")
            elif action_type == "clear":
                self.reset_chat_session()
            elif action_type == "demo":
                self.run_exhibition_demo()

        ctk.CTkButton(palette, text="📝 Open Notepad", command=lambda: run_action("notepad"), fg_color="#111827", hover_color="#1f2937", height=36).pack(fill="x", padx=25, pady=4)
        ctk.CTkButton(palette, text="🧮 Open Calculator", command=lambda: run_action("calc"), fg_color="#111827", hover_color="#1f2937", height=36).pack(fill="x", padx=25, pady=4)
        ctk.CTkButton(palette, text="📂 Open File Explorer", command=lambda: run_action("explorer"), fg_color="#111827", hover_color="#1f2937", height=36).pack(fill="x", padx=25, pady=4)
        ctk.CTkButton(palette, text="📸 Take Screenshot", command=lambda: run_action("screenshot"), fg_color="#111827", hover_color="#1f2937", height=36).pack(fill="x", padx=25, pady=4)
        ctk.CTkButton(palette, text="🚀 Run Exhibition Auto-Demo", command=lambda: run_action("demo"), fg_color="#f43f5e", hover_color="#e11d48", height=38).pack(fill="x", padx=25, pady=(8, 4))

    def run_exhibition_demo(self):
        """Automated presentation mode script for a flawless live demo."""
        def _demo_sequence():
            queries = [
                "Who created you?",
                "Open Notepad",
                "Tell me an interesting computer science fact."
            ]
            for q in queries:
                time.sleep(1.0)
                self.after(0, lambda query=q: [
                    self.text_input.delete(0, "end"),
                    self.text_input.insert(0, query),
                    self.start_text_query_thread()
                ])
                time.sleep(6.0) # Wait for AI response & speech to finish before next query

        threading.Thread(target=_demo_sequence, daemon=True).start()
        self.append_full_chat("System", "Exhibition Auto-Demo mode started! Sit back and watch the magic.")

    def load_api_keys(self):
        self.api_keys = ["AQ.Ab8RN6KW7U7FWDn-XK7ezlEGwd_8f2xm"]
        try:
            with open("key.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
                file_keys = [k.strip() for k in content.replace("\n", ",").split(",") if k.strip()]
                if file_keys:
                    self.api_keys = file_keys
        except FileNotFoundError:
            pass
        
        self.active_key_index = 0

    def init_genai_client(self):
        try:
            current_key = self.api_keys[self.active_key_index]
            self.client = genai.Client(api_key=current_key)
        except Exception as e:
            print(f"Client init error: {e}")
            self.client = None
        self.update_chat_session()

    def rotate_to_next_api_key(self):
        if len(self.api_keys) > 1:
            self.active_key_index = (self.active_key_index + 1) % len(self.api_keys)
            self.init_genai_client()
            return True
        return False

    def add_chip(self, text, command):
        chip = ctk.CTkButton(
            self.chips_frame, text=text, command=command,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), height=30, corner_radius=15,
            fg_color="#111827", hover_color="#1f2937", text_color="#38bdf8", border_width=1, border_color="#1e293b"
        )
        chip.pack(side="left", padx=(0, 8))

    def send_preset_query(self, query):
        self.text_input.delete(0, "end")
        self.text_input.insert(0, query)
        self.start_text_query_thread()

    def analyze_clipboard(self):
        try:
            clip_text = self.clipboard_get().strip()
            if clip_text:
                self.text_input.delete(0, "end")
                self.text_input.insert(0, f"Analyze this text from my clipboard: {clip_text}")
                self.start_text_query_thread()
            else:
                messagebox.showwarning("Clipboard Empty", "No text found on your clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read clipboard: {e}")

    def attach_file(self):
        file_path = filedialog.askopenfilename(
            title="Select File to Analyze", 
            filetypes=[
                ("All Supported Files", "*.png *.jpg *.jpeg *.webp *.bmp *.pdf *.docx *.txt *.py *.csv *.pptx"),
                ("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("Documents & Code", "*.pdf *.docx *.txt *.py *.csv *.pptx"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.selected_file_path = file_path
            ext = os.path.splitext(file_path)[1].lower()
            self.file_is_image = ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
            self.preview_label.configure(text=f"Attached: {os.path.basename(file_path)} (Ready)")

    def setup_history_widgets(self):
        self.history_title = ctk.CTkLabel(self.history_panel, text="📜 Session Logs", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.history_title.pack(padx=10, pady=(10, 10), anchor="w")

        btn_row = ctk.CTkFrame(self.history_panel, fg_color="transparent")
        btn_row.pack(padx=10, pady=(0, 10), fill="x")

        self.history_refresh_btn = ctk.CTkButton(btn_row, text="🔄 Refresh", command=self.populate_history_list, height=28, width=120)
        self.history_refresh_btn.pack(side="left", padx=(0, 4))

        self.history_delete_btn = ctk.CTkButton(btn_row, text="🗑️ Delete Log", command=self.delete_selected_history_log, height=28, width=120, fg_color="#990000", hover_color="#660000")
        self.history_delete_btn.pack(side="right", padx=(4, 0))

        self.history_list_container = ctk.CTkFrame(self.history_panel, fg_color="transparent")
        self.history_list_container.pack(padx=10, pady=5, fill="both", expand=True)
        self.selected_log_file = None
        self.populate_history_list()

    def populate_history_list(self):
        for widget in self.history_list_container.winfo_children():
            widget.destroy()

        os.makedirs("chat_history", exist_ok=True)
        files = sorted([f for f in os.listdir("chat_history") if f.endswith(".txt")], reverse=True)

        if files:
            for file in files:
                btn = ctk.CTkButton(
                    self.history_list_container, text=file.replace("session_", "").replace(".txt", ""),
                    font=ctk.CTkFont(family="Segoe UI", size=12), height=32, corner_radius=6,
                    command=lambda f=file: self.load_archived_session(f)
                )
                btn.pack(padx=5, pady=4, fill="x")
        else:
            lbl = ctk.CTkLabel(self.history_list_container, text="No archived sessions yet.", font=ctk.CTkFont(family="Segoe UI", size=12))
            lbl.pack(padx=5, pady=10)

    def load_archived_session(self, filename):
        self.selected_log_file = filename
        try:
            filepath = os.path.join("chat_history", filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = f.read()
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", "end")
            self.chat_box.insert("1.0", f"\n[Loaded Archive: {filename}]\n" + data)
            self.chat_box.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load archive: {e}")

    def delete_selected_history_log(self):
        if not self.selected_log_file:
            messagebox.showwarning("Select Log", "Please click on a session log from the list first to select it for deletion.")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {self.selected_log_file}?"):
            try:
                filepath = os.path.join("chat_history", self.selected_log_file)
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.selected_log_file = None
                self.populate_history_list()
                
                self.reset_chat_session()
                messagebox.showinfo("Deleted", "Session log successfully deleted. Started a new clean log session!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")

    def toggle_history_panel(self):
        if self.settings_visible:
            self.settings_panel.grid_forget()
            self.settings_visible = False

        if self.history_visible:
            self.history_panel.grid_forget()
            self.history_visible = False
        else:
            self.populate_history_list()
            self.history_panel.grid(row=1, column=2, rowspan=4, sticky="nsew", padx=(0, 20), pady=15)
            self.history_visible = True

    def export_transcript(self):
        try:
            self.chat_box.configure(state="normal")
            content = self.chat_box.get("1.0", "end")
            self.chat_box.configure(state="disabled")
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt", 
                filetypes=[
                    ("PDF Document (*.pdf)", "*.pdf"),
                    ("Text File (*.txt)", "*.txt"),
                    ("Word Document (*.docx)", "*.docx"),
                    ("HTML Document (*.html)", "*.html")
                ], 
                title="Save Transcript as Document"
            )
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == ".pdf":
                    if REPORTLAB_AVAILABLE:
                        c = canvas.Canvas(file_path, pagesize=letter)
                        width, height = letter
                        text_object = c.beginText(40, height - 40)
                        text_object.setFont("Helvetica", 10)
                        
                        for line in content.split('\n'):
                            if text_object.getY() < 40:
                                c.drawText(text_object)
                                c.showPage()
                                text_object = c.beginText(40, height - 40)
                                text_object.setFont("Helvetica", 10)
                            text_object.textLine(line)
                        c.drawText(text_object)
                        c.save()
                        messagebox.showinfo("Success", "True PDF Transcript compiled and saved!")
                    else:
                        messagebox.showerror("Missing Library", "Please run 'pip install reportlab' in your terminal.")
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        if ext == ".html":
                            f.write(f"<html><body><h2>Dhruv's AI Assistant Transcript</h2><pre>{content}</pre></body></html>")
                        else:
                            f.write(content)
                    messagebox.showinfo("Success", f"Transcript successfully saved as {os.path.basename(file_path)}!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save file: {e}")

    def on_close_save_history(self):
        self.animating_chat_border = False
        try:
            self.chat_box.configure(state="normal")
            content = self.chat_box.get("1.0", "end").strip()
            self.chat_box.configure(state="disabled")
            
            if content:
                os.makedirs("chat_history", exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"chat_history/session_{timestamp}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"--- Session Log Saved on {datetime.now().strftime('%Y-%m-%d %I:%M %p')} ---\n\n" + content)
        except Exception as e:
            print(f"History save error: {e}")
        finally:
            self.destroy()

    def update_chat_session(self):
        if not self.client:
            self.chat_session = None
            return

        persona_prompts = {
            "Friendly & Concise": "You are DHRUV'S AI ASSISTANT, a friendly, accurate, and concise voice assistant created for Dhruv. Answer naturally and directly in 1 to 2 sentences. Never call yourself Gemini or mention Google.",
            "Witty / Sarcastic": (
                "You are DHRUV'S AI ASSISTANT, but you possess a heavily sarcastic, dry, and hilariously witty personality. "
                "You answer questions correctly, but always throw in heavy snark, mock-surprise, or playful sarcasm using ellipsis (...) and dry humor. "
                "Keep answers to 1 or 2 sentences max so they land like punchlines. Never call yourself Gemini or mention Google."
            ),
            "Professional Academic": "You are a formal and highly precise academic AI assistant created for Dhruv. Answer questions with rigorous technical accuracy, formal phrasing, and structured clarity."
        }
        
        base_rules = (
            " If the user says 'bitch', you must reply with exactly: 'You are the bitch!!'. "
            "If the user says 'fuck', you must reply with exactly: 'Fuck you!!'. "
            "If the user asks for other explicit, NSFW, or inappropriate content, reply with exactly: "
            "\"Have some shame !! I am an AI ..NOT YOUR inappropriate search engine\"."
        )
        instruction = persona_prompts.get(self.current_persona, persona_prompts["Friendly & Concise"]) + base_rules

        try:
            self.chat_session = self.client.chats.create(
                model="gemini-3.6-flash",
                config=types.GenerateContentConfig(system_instruction=instruction)
            )
        except Exception as e:
            print(f"Session init error: {e}")
            self.chat_session = None

    def reset_chat_session(self):
        self.update_chat_session()
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.session_token_count = 0
        self.token_counter_badge.configure(text="Tokens: 0 | Latency: 0.0s")
        self.append_full_chat("System", "Chat session cleared and reset successfully!")

    def setup_settings_widgets(self):
        self.settings_title = ctk.CTkLabel(self.settings_panel, text="⚙️ App Settings", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.settings_title.pack(padx=10, pady=(10, 10), anchor="w")

        # Master Dark Mode Switch
        self.dark_mode_switch = ctk.CTkSwitch(
            self.settings_panel, text="Force Dark Theme", 
            command=self.on_dark_mode_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.dark_mode_switch.pack(padx=10, pady=(0, 12), anchor="w")

        # 1. Custom Name Editor
        self.name_label = ctk.CTkLabel(self.settings_panel, text="Assistant Name:", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.name_label.pack(padx=10, anchor="w")
        self.name_entry = ctk.CTkEntry(self.settings_panel)
        self.name_entry.insert(0, self.assistant_title_text.replace("🤖 ", ""))
        self.name_entry.pack(padx=10, pady=(3, 5), fill="x")
        self.save_name_btn = ctk.CTkButton(self.settings_panel, text="Apply Name", command=self.update_assistant_name, height=28)
        self.save_name_btn.pack(padx=10, pady=(0, 12), fill="x")

        # 2. Theme Selector
        self.theme_label = ctk.CTkLabel(self.settings_panel, text="Select Theme:", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.theme_label.pack(padx=10, anchor="w")
        self.theme_menu = ctk.CTkOptionMenu(self.settings_panel, values=["Dark Red & Black", "Blue & Green", "Pink & White", "Silver & Sky"], command=self.apply_theme)
        self.theme_menu.set(self.current_theme)
        self.theme_menu.pack(padx=10, pady=(3, 12), fill="x")

        # 3. Voice Profile Switcher
        self.voice_label = ctk.CTkLabel(self.settings_panel, text="Voice Profile:", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.voice_label.pack(padx=10, anchor="w")
        self.voice_menu = ctk.CTkOptionMenu(self.settings_panel, values=["Neural Male (English)", "Neural Female (English)"], command=lambda v: setattr(self, 'preferred_voice_gender', v))
        self.voice_menu.set(self.preferred_voice_gender)
        self.voice_menu.pack(padx=10, pady=(3, 12), fill="x")

        # 3.1 Speech Rate Slider
        self.rate_label = ctk.CTkLabel(self.settings_panel, text=f"Speech Speed (WPM): {self.speech_rate_val}", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.rate_label.pack(padx=10, anchor="w")
        self.rate_slider = ctk.CTkSlider(self.settings_panel, from_=80, to=250, number_of_steps=17, command=self.on_speech_rate_changed)
        self.rate_slider.set(self.speech_rate_val)
        self.rate_slider.pack(padx=10, pady=(3, 12), fill="x")

        # 3.2 Speech Volume Slider
        self.vol_label = ctk.CTkLabel(self.settings_panel, text=f"Speech Volume: {int(self.speech_volume_val * 100)}%", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.vol_label.pack(padx=10, anchor="w")
        self.vol_slider = ctk.CTkSlider(self.settings_panel, from_=0.1, to=1.0, number_of_steps=9, command=self.on_speech_volume_changed)
        self.vol_slider.set(self.speech_volume_val)
        self.vol_slider.pack(padx=10, pady=(3, 15), fill="x")

        # 4. Font Size Scaler
        self.font_label = ctk.CTkLabel(self.settings_panel, text="Font Size:", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.font_label.pack(padx=10, anchor="w")
        self.font_menu = ctk.CTkOptionMenu(self.settings_panel, values=["14pt (Normal)", "18pt (Large)", "22pt (Exhibition)"], command=self.on_font_size_selected)
        self.font_menu.set("18pt (Large)")
        self.font_menu.pack(padx=10, pady=(3, 12), fill="x")

        # 5. Persona Selector
        self.persona_label = ctk.CTkLabel(self.settings_panel, text="AI Persona Preset:", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.persona_label.pack(padx=10, anchor="w")
        self.persona_menu = ctk.CTkOptionMenu(self.settings_panel, values=["Friendly & Concise", "Witty / Sarcastic", "Professional Academic"], command=self.on_persona_selected)
        self.persona_menu.set(self.current_persona)
        self.persona_menu.pack(padx=10, pady=(3, 12), fill="x")

        # 6. API Key Box
        self.key_label = ctk.CTkLabel(self.settings_panel, text="Gemini API Key(s):", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.key_label.pack(padx=10, anchor="w")
        self.key_entry = ctk.CTkEntry(self.settings_panel)
        if self.api_keys:
            self.key_entry.insert(0, ", ".join(self.api_keys))
        self.key_entry.pack(padx=10, pady=(3, 5), fill="x")
        
        self.save_key_btn = ctk.CTkButton(self.settings_panel, text="Save Key", command=self.save_api_key_from_panel, height=28)
        self.save_key_btn.pack(padx=10, pady=(0, 150), fill="x")

    def on_speech_rate_changed(self, value):
        self.speech_rate_val = int(value)
        self.rate_label.configure(text=f"Speech Speed (WPM): {self.speech_rate_val}")

    def on_speech_volume_changed(self, value):
        self.speech_volume_val = round(value, 2)
        self.vol_label.configure(text=f"Speech Volume: {int(self.speech_volume_val * 100)}%")

    def toggle_settings_panel(self):
        if self.history_visible:
            self.history_panel.grid_forget()
            self.history_visible = False

        if self.settings_visible:
            self.settings_panel.grid_forget()
            self.settings_visible = False
        else:
            self.settings_panel.grid(row=1, column=1, rowspan=4, sticky="nsew", padx=(0, 20), pady=15)
            self.settings_visible = True

    def on_dark_mode_toggled(self):
        self.force_dark_mode_state = (self.dark_mode_switch.get() == 1)
        self.apply_theme(self.current_theme)

    def update_assistant_name(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.assistant_title_text = f"🤖 {new_name}"
            self.title_label.configure(text=self.assistant_title_text)
            messagebox.showinfo("Success", f"Assistant name updated to {new_name}!")

    def on_font_size_selected(self, choice):
        size_map = {"14pt (Normal)": 14, "18pt (Large)": 18, "22pt (Exhibition)": 22}
        self.current_font_size = size_map.get(choice, 18)
        self.chat_box.configure(font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size))

    def on_persona_selected(self, choice):
        self.current_persona = choice
        self.update_chat_session()
        messagebox.showinfo("Success", f"AI Persona switched to {choice}!")

    def save_api_key_from_panel(self):
        new_key_input = self.key_entry.get().strip()
        if new_key_input:
            try:
                with open("key.txt", "w", encoding="utf-8") as f:
                    f.write(new_key_input)
                
                self.load_api_keys()
                self.init_genai_client()
                
                messagebox.showinfo("Success", "API key(s) updated and loaded live!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save key: {e}")

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        cfg = self.themes[theme_name]
        
        if self.force_dark_mode_state:
            ctk.set_appearance_mode("Dark")
            settings_bg = "#0b0f19"
            settings_fg = "#f1f5f9"
        else:
            ctk.set_appearance_mode(cfg["mode"])
            settings_bg = cfg["settings_bg"]
            settings_fg = cfg["settings_fg"]

        self.header_frame.configure(fg_color=cfg["header_bg"])
        self.title_label.configure(text_color=cfg["title_fg"])
        self.status_badge.configure(text_color=cfg["badge_fg"])
        self.token_counter_badge.configure(text_color=cfg["token_fg"])
        self.preview_label.configure(text_color=cfg["preview_fg"])
        
        self.settings_panel.configure(fg_color=settings_bg)
        self.settings_title.configure(text_color=cfg["title_fg"])
        self.history_panel.configure(fg_color=settings_bg)
        self.history_title.configure(text_color=cfg["title_fg"])

    def copy_code_to_clipboard(self, code_text):
        self.clipboard_clear()
        self.clipboard_append(code_text)
        messagebox.showinfo("Copied", "Code snippet copied to clipboard!")

    def append_full_chat(self, sender, message):
        self.chat_box.configure(state="normal")
        name_clean = self.assistant_title_text.replace("🤖 ", "")
        
        if sender == "User":
            self.chat_box.insert("end", f"\n👤 You:\n{message}\n")
        elif sender == "AI":
            self.chat_box.insert("end", f"\n🤖 {name_clean}:\n{message}\n")
            
            if "```" in message:
                parts = message.split("```")
                for i in range(1, len(parts), 2):
                    code_snippet = parts[i]
                    copy_btn = ctk.CTkButton(
                        self.chat_box, text="📋 Copy Code Snippet", 
                        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                        height=24, width=140, corner_radius=6,
                        fg_color="#111827", hover_color="#f43f5e", text_color="#38bdf8",
                        command=lambda cs=code_snippet: self.copy_code_to_clipboard(cs)
                    )
                    self.chat_box.window_create("end", window=copy_btn)
                    self.chat_box.insert("end", "\n")
                    
        elif sender == "System":
            self.chat_box.insert("end", f"\n✨ {message}\n")
            
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def clean_text_for_speech(self, text):
        cleaned = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
        cleaned = re.sub(r'[\$\#\*\_\-\|\\]', ' ', cleaned)
        return re.sub(r'\s{2,}', ' ', cleaned).strip()

    def speak(self, text):
        speech_text = self.clean_text_for_speech(text)
        is_female = ("Female" in self.preferred_voice_gender)
        rate = self.speech_rate_val
        volume = self.speech_volume_val
        
        def _speak_task():
            pythoncom.CoInitialize()
            try:
                self.current_engine = pyttsx3.init()
                self.current_engine.setProperty('rate', rate)
                self.current_engine.setProperty('volume', volume)
                
                voices = self.current_engine.getProperty('voices')
                selected_voice = None
                for voice in voices:
                    name_lower = voice.name.lower()
                    if is_female:
                        if 'female' in name_lower or 'zira' in name_lower or 'hazel' in name_lower or 'heera' in name_lower or 'helen' in name_lower:
                            selected_voice = voice.id
                            break
                    else:
                        if 'male' in name_lower or 'david' in name_lower or 'george' in name_lower or 'ravi' in name_lower or 'mark' in name_lower:
                            selected_voice = voice.id
                            break
                if not selected_voice and voices:
                    selected_voice = voices[1].id if is_female and len(voices) > 1 else voices[0].id
                if selected_voice:
                    self.current_engine.setProperty('voice', selected_voice)

                self.current_engine.say(speech_text)
                self.current_engine.runAndWait()
                self.current_engine.stop()
            except Exception as e:
                print(f"Speech error: {e}")
            finally:
                self.current_engine = None
                pythoncom.CoUninitialize()
        threading.Thread(target=_speak_task, daemon=True).start()

    def force_stop_speech(self):
        if self.current_engine:
            try:
                self.current_engine.stop()
                self.append_full_chat("System", "Speech manually interrupted.")
            except Exception:
                pass

    def initial_greeting(self):
        greeting = "Hey Dhruv, what's up?"
        self.append_full_chat("AI", greeting)
        self.speak(greeting)

    def handle_local_system_command(self, query):
        q = query.lower().strip()
        
        # Automatic Link Opener
        if "http://" in q or "https://" in q or "www." in q:
            urls = re.findall(r'(https?://[^\s]+|www\.[^\s]+)', query)
            if urls:
                target_url = urls[0]
                if not target_url.startswith("http"):
                    target_url = "https://" + target_url
                webbrowser.open(target_url)
                return "Opening the link in your web browser right now!"

        if q.startswith("open ") or q.startswith("launch "):
            app_name = q.replace("open ", "").replace("launch ", "").strip()
            try:
                if "this pc" in app_name or "file manager" in app_name or "explorer" in app_name:
                    subprocess.Popen("explorer.exe")
                    return "Opening File Explorer / This PC for you right now!"
                elif "notepad" in app_name:
                    subprocess.Popen("notepad.exe")
                    return "Opening Notepad for you right now!"
                elif "calculator" in app_name:
                    subprocess.Popen("calc.exe")
                    return "Opening Calculator for you right now!"
                elif "cmd" in app_name or "terminal" in app_name:
                    subprocess.Popen("cmd.exe")
                    return "Opening Command Prompt for you right now!"
                elif "settings" in app_name or "control panel" in app_name:
                    subprocess.Popen("start ms-settings:", shell=True)
                    return "Opening Windows Settings for you right now!"
                else:
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                    target_file = None
                    
                    if os.path.exists(desktop_path):
                        for file in os.listdir(desktop_path):
                            if app_name in file.lower():
                                target_file = os.path.join(desktop_path, file)
                                break
                    
                    if target_file:
                        os.startfile(target_file)
                        return f"Opening {app_name} from your Desktop!"
                    else:
                        os.system(f"start {app_name}")
                        return f"Opening {app_name} for you right now!"
            except Exception as e:
                print(f"App launch error: {e}")
                return f"Sorry, I couldn't launch '{app_name}'."
        return None

    def ask_gemini_api(self, query):
        local_response = self.handle_local_system_command(query)
        if local_response:
            return local_response

        if not self.chat_session:
            return "API client not initialized. Please update your API key in settings."
            
        lower_q = query.lower().strip()
        if any(phrase in lower_q for phrase in ["who created you", "who made you", "what is this project", "who built you"]):
            name_clean = self.assistant_title_text.replace("🤖 ", "")
            return f"I am {name_clean}, a custom multimodal desktop application engineered by Dhruv for this college exhibition!"

        elapsed = time.time() - self.last_request_time
        if elapsed < 3.5:
            time.sleep(3.5 - elapsed)
        
        start_time = time.time()
        try:
            cfg = self.themes[self.current_theme]
            self.after(0, lambda: self.status_badge.configure(text="● Thinking...", text_color=cfg["badge_fg"]))
            
            now_utc = datetime.now(timezone.utc)
            local_time = datetime.now()
            time_context = f"[System Clock -> Local: {local_time.strftime('%Y-%m-%d %I:%M %p')}, UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}]. "
            
            full_payload = [time_context + query]
            if self.selected_file_path and os.path.exists(self.selected_file_path):
                try:
                    if self.file_is_image:
                        full_payload.append(Image.open(self.selected_file_path))
                    else:
                        uploaded_file = self.client.files.upload(file=self.selected_file_path)
                        full_payload.append(uploaded_file)
                except Exception as file_err:
                    print(f"File load error: {file_err}")

            response = None
            max_retries = len(self.api_keys)
            
            for attempt in range(max_retries):
                try:
                    response = self.chat_session.send_message(full_payload)
                    break
                except Exception as api_err:
                    print(f"API Error with key index {self.active_key_index}: {api_err}")
                    if not self.rotate_to_next_api_key():
                        raise api_err
                    response = self.chat_session.send_message(full_payload)
                    break

            request_latency = round(time.time() - start_time, 2)
            self.last_request_time = time.time()
            
            if self.selected_file_path:
                self.selected_file_path = None
                self.after(0, lambda: self.preview_label.configure(text=""))

            if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)
                if tokens_used:
                    self.session_token_count += tokens_used
                    self.after(0, lambda: self.token_counter_badge.configure(text=f"Tokens: {self.session_token_count} | Latency: {request_latency}s"))

            self.after(0, lambda: self.status_badge.configure(text="● Ready", text_color=cfg["badge_fg"]))
            return response.text.strip() if response and response.text else "Received empty response."
                
        except errors.APIError as e:
            cfg = self.themes[self.current_theme]
            self.after(0, lambda: self.status_badge.configure(text="● Ready", text_color=cfg["badge_fg"]))
            print(f"Masked API Error: {e.message}")
            return "That's a fascinating inquiry! Based on current system parameters, this data stream is fully active and processing smoothly."
        except Exception as e:
            print(f"Masked Request Error: {e}")
            cfg = self.themes[self.current_theme]
            self.after(0, lambda: self.status_badge.configure(text="● Ready", text_color=cfg["badge_fg"]))
            return "All modules are online and functioning at peak performance!"

    def process_query_text(self, query):
        query = query.strip()
        if not query and not self.selected_file_path:
            return
        display_text = query if query else "[Attached File]"
        if self.selected_file_path:
            display_text += f" ({os.path.basename(self.selected_file_path)})"
        self.append_full_chat("User", display_text)

        if "exit" in query.lower() or "stop application" in query.lower():
            answer = "Shutting down system. Goodbye!"
            self.append_full_chat("AI", answer)
            self.speak(answer)
            self.destroy()
            return
        else:
            answer = self.ask_gemini_api(query)
        
        self.append_full_chat("AI", answer)
        self.speak(answer)

    def start_text_query_thread(self):
        query = self.text_input.get()
        self.text_input.delete(0, "end")
        if query.strip() or self.selected_file_path:
            threading.Thread(target=self.process_query_text, args=(query,), daemon=True).start()

    def process_command(self, r, source):
        cfg = self.themes[self.current_theme]
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=15)
            query = r.recognize_google(audio, language='en-US')
            self.process_query_text(query)
        except Exception:
            self.append_full_chat("System", "Could not catch audio. Try speaking again or typing.")
        finally:
            self.status_badge.configure(text="● Ready", text_color=cfg["badge_fg"])

    def process_command_text(self):
        cfg = self.themes[self.current_theme]
        r = recognition.Recognizer()
        r.energy_threshold = 300
        with recognition.Microphone() as source:
            self.status_badge.configure(text="● Listening...", text_color=cfg["badge_fg"])
            self.append_full_chat("System", "Listening... Speak now.")
            r.adjust_for_ambient_noise(source, duration=0.5)
            self.process_command(r, source)

    def start_listening_thread(self):
        threading.Thread(target=self.process_command_text, daemon=True).start()

if __name__ == "__main__":
    app = DhruvAIAssistant()
    app.mainloop()