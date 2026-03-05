import math
from OpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import glfw
import vulkan as vk
import numpy as np
import pyopencl as cll
import sys
import os

# Try to import font rendering library (Pillow)
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# File dialog support
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

import json
import os
from pathlib import Path

class GridApplication:
    def __init__(self, width=1200, height=800, title="Grid View App"):
        self.width = width
        self.height = height
        self.title = title
        self.window = None
        
        # Layout dimensions (in pixels)
        self.top_bar_height = 50
        self.middle_split_ratio = 0.30  # 30% left, 70% right
        self.bottom_height = 200
        
        # Divider/gap properties
        self.divider_width = 8
        self.divider_color = (0.35, 0.35, 0.38, 1.0)
        self.divider_hover_color = (0.5, 0.5, 0.55, 1.0)
        
        # Dragging state
        self.dragging_vertical = False  # Vertical divider between middle left/right
        self.dragging_horizontal = False  # Horizontal divider between middle/bottom
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Menu items
        self.menu_items = ['File', 'Edit', 'Settings']
        self.hovered_menu = None
        self.open_menu = None  # Track which menu is open
        self.menu_item_height = 30
        self.menu_items_data = {
            0: ['New', 'Open', 'Save', 'Exit'],  # File menu
            1: ['Undo', 'Redo', 'Cut', 'Copy', 'Paste'],  # Edit menu
            2: ['Preferences', 'About'],  # Settings menu
        }
        
        # DAW state
        self.current_file = None
        self.is_modified = False
        self.hovered_dropdown_item = None
        self.left_panel_modes = ['Audio Tracks', 'Clip Rack', 'Routing']
        self.active_left_panel_mode = 0
        self.right_panel_views = ['Waveform', 'Piano Roll', 'Spectrum']
        self.active_right_view = 0
        self.track_items = [
            {'name': 'Audio Track 1', 'kind': 'audio', 'view': 0, 'notes': [], 'instrument': 'Piano', 'muted': False, 'solo': False},
            {'name': 'Audio Track 2', 'kind': 'audio', 'view': 0, 'notes': [], 'instrument': 'Piano', 'muted': False, 'solo': False},
            {'name': 'Audio Track 3', 'kind': 'audio', 'view': 0, 'notes': [], 'instrument': 'Piano', 'muted': False, 'solo': False},
        ]
        self.selected_track_index = 0
        self.focused_track_index = None  # When set, only show this track on right panel
        
        # Piano roll state
        self.piano_keys = 88  # Standard piano keys
        self.piano_roll_zoom = 1.0
        self.piano_roll_scroll_x = 0
        self.piano_roll_scroll_y = 36  # Start at middle C
        self.piano_editing_note = None  # Currently being placed/edited
        
        # Available instruments
        self.instruments = ['Piano', 'Synth', 'Bass', 'Strings', 'Brass', 'Drums', 'Guitar']
        
        # Track editing tools
        self.track_tools = ['Select', 'Split', 'Trim', 'Fade', 'Normalize', 'Reverse']
        self.active_tool = 0
        
        # Audio processing (OpenCL placeholder)
        self.audio_context = None
        self.audio_enabled = False
        
        # Text rendering cache (textures)
        self.text_textures = {}  # Cache of rendered text textures
        self.pil_font = None
        self.font_name = "none"
        self.init_font()
        
        # State persistence
        self.state_file = Path.home() / ".wera_creative_state.json"
        self.auto_save_enabled = True
        self.load_state()
        
        # Panel colors (RGBA)
        self.colors = {
            'top_bar': (0.2, 0.2, 0.25, 1.0),
            'middle_left': (0.15, 0.2, 0.25, 1.0),
            'middle_right': (0.18, 0.22, 0.27, 1.0),
            'bottom': (0.12, 0.15, 0.2, 1.0),
        }
        
        # Border color
        self.border_color = (0.4, 0.4, 0.45, 1.0)
        self.border_width = 2
        
        self.initialize()
    
    def save_state(self):
        """Save current application state to JSON file."""
        if not self.auto_save_enabled:
            return
        
        state = {
            'version': '1.0',
            'tracks': self.track_items,
            'selected_track_index': self.selected_track_index,
            'active_left_panel_mode': self.active_left_panel_mode,
            'active_right_view': self.active_right_view,
            'middle_split_ratio': self.middle_split_ratio,
            'bottom_height': self.bottom_height,
            'window_width': self.width,
            'window_height': self.height,
            'current_file': self.current_file,
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[State] Failed to save: {e}")
    
    def load_state(self):
        """Load application state from JSON file."""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restore tracks with validation
            if 'tracks' in state and isinstance(state['tracks'], list):
                self.track_items = state['tracks']
                # Ensure all tracks have 'view' field
                for track in self.track_items:
                    if 'view' not in track:
                        track['view'] = 1 if track.get('kind') == 'piano' else 0
            
            # Restore other state
            if 'selected_track_index' in state:
                self.selected_track_index = max(0, min(state['selected_track_index'], len(self.track_items) - 1))
            if 'active_left_panel_mode' in state:
                self.active_left_panel_mode = state['active_left_panel_mode']
            if 'active_right_view' in state:
                self.active_right_view = state['active_right_view']
            if 'middle_split_ratio' in state:
                self.middle_split_ratio = max(0.15, min(0.85, state['middle_split_ratio']))
            if 'bottom_height' in state:
                self.bottom_height = max(50, min(600, state['bottom_height']))
            if 'window_width' in state and 'window_height' in state:
                self.width = max(800, state['window_width'])
                self.height = max(600, state['window_height'])
            if 'current_file' in state:
                self.current_file = state['current_file']
            
            print(f"[State] Loaded {len(self.track_items)} tracks from {self.state_file}")
        except Exception as e:
            print(f"[State] Failed to load: {e}")
    
    def handle_menu_action(self, menu_idx, item_name):
        """Handle menu item actions"""
        if menu_idx == 0:  # File menu
            if item_name == 'New':
                self.new_project()
            elif item_name == 'Open':
                self.open_file()
            elif item_name == 'Save':
                self.save_file()
            elif item_name == 'Exit':
                glfw.set_window_should_close(self.window, True)
        elif menu_idx == 1:  # Edit menu
            print(f"Edit -> {item_name}")
        elif menu_idx == 2:  # Settings menu
            print(f"Settings -> {item_name}")
    
    def new_project(self):
        """Create new audio project"""
        self.current_file = None
        self.is_modified = False
        self.track_items = []
        self.selected_track_index = 0
        self.save_state()
        print("[DAW] New project created")
    
    def open_file(self):
        """Open audio file with file picker"""
        if not HAS_TKINTER:
            print("Error: tkinter not available for file dialog")
            return
        
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        file_path = filedialog.askopenfilename(
            title="Open Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.ogg"), ("All Files", "*.*")]
        )
        
        root.destroy()
        
        if file_path:
            self.current_file = file_path
            self.is_modified = False
            print(f"[DAW] Opened file: {file_path}")
    
    def save_file(self):
        """Save audio project"""
        if self.current_file:
            print(f"[DAW] Saved: {self.current_file}")
            self.is_modified = False
        else:
            print("[DAW] No file to save. Use 'Open' or create a new project.")

    def add_track(self, kind):
        """Add a new track lane to the left track panel."""
        next_index = len(self.track_items) + 1
        if kind == 'piano':
            name = f"Piano Roll {next_index}"
        else:
            name = f"Audio Track {next_index}"
            kind = 'audio'

        default_view = 1 if kind == 'piano' else 0
        self.track_items.append({
            'name': name,
            'kind': kind,
            'view': default_view,
            'notes': [],
            'instrument': 'Piano' if kind == 'piano' else 'Synth',
            'muted': False,
            'solo': False
        })
        self.selected_track_index = len(self.track_items) - 1
        self.active_right_view = default_view
        self.save_state()
        print(f"[DAW] Inserted {name}")

    def get_selected_track(self):
        """Return the currently selected track item."""
        if not self.track_items:
            return None
        self.selected_track_index = max(0, min(self.selected_track_index, len(self.track_items) - 1))
        return self.track_items[self.selected_track_index]

    def point_in_rect(self, x, y, rect):
        """Return True when the cursor is inside a rect dictionary."""
        return (
            x >= rect['x'] and
            x <= rect['x'] + rect['w'] and
            y >= rect['y'] and
            y <= rect['y'] + rect['h']
        )

    def get_left_workspace_ui(self, panels):
        """Build left pane UI hitboxes for tabs, track rows, and insert buttons."""
        panel = panels['middle_left']
        header_h = 34
        tab_h = 24
        tab_w = 82
        tab_gap = 4
        base_x = panel['x'] + 6
        tab_y = panel['y'] + 5

        tabs = []
        tools = []
        instruments = []
        for idx, label in enumerate(self.left_panel_modes):
            tabs.append({
                'index': idx,
                'label': label,
                'x': base_x + (idx * (tab_w + tab_gap)),
                'y': tab_y,
                'w': tab_w,
                'h': tab_h,
            })

        add_audio = {
            'x': panel['x'] + panel['w'] - 126,
            'y': panel['y'] + 5,
            'w': 58,
            'h': 24,
            'label': '+Audio',
        }
        add_piano = {
            'x': panel['x'] + panel['w'] - 64,
            'y': panel['y'] + 5,
            'w': 58,
            'h': 24,
            'label': '+Piano',
        }

        rows = []
        row_start_y = panel['y'] + header_h + 4
        row_h = 32
        for idx, track in enumerate(self.track_items):
            row_y = row_start_y + (idx * (row_h + 2))
            if row_y + row_h > panel['y'] + panel['h'] - 6:
                break
            rows.append({
                'index': idx,
                'track': track,
                'x': panel['x'] + 6,
                'y': row_y,
                'w': panel['w'] - 12,
                'h': row_h,
            })

        return {
            'panel': panel,
            'header': {'x': panel['x'], 'y': panel['y'], 'w': panel['w'], 'h': header_h},
            'tabs': tabs,
            'add_audio': add_audio,
            'add_piano': add_piano,
            'rows': rows,
        }

    def get_right_workspace_ui(self, panels):
        """Build right pane UI hitboxes for editor view buttons."""
        panel = panels['middle_right']
        left_ui = self.get_left_workspace_ui(panels)
        header_h = 34
        btn_w = 92
        btn_h = 22
        btn_gap = 6
        total_w = (len(self.right_panel_views) * btn_w) + ((len(self.right_panel_views) - 1) * btn_gap)
        start_x = panel['x'] + panel['w'] - total_w - 8
        btn_y = panel['y'] + 6

        buttons = []
        for idx, label in enumerate(self.right_panel_views):
            buttons.append({
                'index': idx,
                'label': label,
                'x': start_x + (idx * (btn_w + btn_gap)),
                'y': btn_y,
                'w': btn_w,
                'h': btn_h,
            })

        content = {
            'x': panel['x'] + 6,
            'y': panel['y'] + header_h + 6,
            'w': panel['w'] - 12,
            'h': panel['h'] - header_h - 12,
        }

        rows = []
        # If focused mode, only show the focused track
        if self.focused_track_index is not None:
            if self.focused_track_index < len(self.track_items):
                track = self.track_items[self.focused_track_index]
                rows.append({
                    'index': self.focused_track_index,
                    'track': track,
                    'x': panel['x'] + 6,
                    'y': panel['y'] + header_h + 6,
                    'w': panel['w'] - 12,
                    'h': panel['h'] - header_h - 12,
                })
        else:
            for row in left_ui['rows']:
                row_y = row['y']
                row_h = row['h']
                if row_y + row_h > panel['y'] + panel['h'] - 6:
                    continue
                rows.append({
                    'index': row['index'],
                    'track': row['track'],
                    'x': panel['x'] + 6,
                    'y': row_y,
                    'w': panel['w'] - 12,
                    'h': row_h,
                })

        # Add focus toggle button
        focus_button = {
            'x': panel['x'] + 6,
            'y': panel['y'] + 6,
            'w': 60,
            'h': 22,
            'label': 'Unfocus' if self.focused_track_index is not None else 'Focus',
        }

        return {
            'panel': panel,
            'header': {'x': panel['x'], 'y': panel['y'], 'w': panel['w'], 'h': header_h},
            'buttons': buttons,
            'content': content,
            'rows': rows,
            'focus_button': focus_button,
        }

    def handle_middle_workspace_click(self, x, y, panels):
        """Handle clicks in left/right middle panels and return True if consumed."""
        left_ui = self.get_left_workspace_ui(panels)
        right_ui = self.get_right_workspace_ui(panels)

        if self.point_in_rect(x, y, left_ui['panel']):
            for tab in left_ui['tabs']:
                if self.point_in_rect(x, y, tab):
                    self.active_left_panel_mode = tab['index']
                    self.save_state()
                    return True

            # Track editing tools
            for tool in left_ui.get('tools', []):
                if self.point_in_rect(x, y, tool):
                    self.active_tool = tool['index']
                    print(f"[DAW] Selected tool: {self.track_tools[tool['index']]}")
                    return True

            # Instrument selector
            for inst in left_ui.get('instruments', []):
                if self.point_in_rect(x, y, inst):
                    if self.track_items:
                        self.track_items[self.selected_track_index]['instrument'] = inst['name']
                        self.save_state()
                        print(f"[DAW] Changed instrument to {inst['name']}")
                    return True

            if self.active_left_panel_mode == 0:
                if self.point_in_rect(x, y, left_ui['add_audio']):
                    self.add_track('audio')
                    return True
                if self.point_in_rect(x, y, left_ui['add_piano']):
                    self.add_track('piano')
                    return True

                for row in left_ui['rows']:
                    if self.point_in_rect(x, y, row):
                        self.selected_track_index = row['index']
                        selected = self.get_selected_track()
                        if selected:
                            self.active_right_view = selected.get('view', 0)
                        self.save_state()
                        return True

        if self.point_in_rect(x, y, right_ui['panel']):
            # Focus toggle button
            if self.point_in_rect(x, y, right_ui.get('focus_button', {})):
                if self.focused_track_index is not None:
                    self.focused_track_index = None
                    print("[DAW] Unfocused track")
                else:
                    self.focused_track_index = self.selected_track_index
                    print(f"[DAW] Focused on track {self.selected_track_index}")
                self.save_state()
                return True

            for button in right_ui['buttons']:
                if self.point_in_rect(x, y, button):
                    if self.track_items:
                        self.track_items[self.selected_track_index]['view'] = button['index']
                    self.active_right_view = button['index']
                    self.save_state()
                    return True

            # Handle piano roll note editing
            if self.active_right_view == 1 and self.focused_track_index is not None:
                self.handle_piano_roll_click(x, y, right_ui)
                return True

            for row in right_ui['rows']:
                if self.point_in_rect(x, y, row):
                    self.selected_track_index = row['index']
                    selected = self.track_items[row['index']]
                    self.active_right_view = selected.get('view', 0)
                    self.save_state()
                    return True

        return False

    def handle_piano_roll_click(self, x, y, right_ui):
        """Handle clicking in piano roll to add/remove notes."""
        if not right_ui['rows']:
            return
        
        row = right_ui['rows'][0]  # Focused track row
        track = self.track_items[self.focused_track_index]
        
        # Calculate grid position
        content_x = row['x'] + 80  # Leave space for piano keys
        content_y = row['y'] + 4
        content_w = row['w'] - 84
        content_h = row['h'] - 8
        
        if x < content_x or x > content_x + content_w or y < content_y or y > content_y + content_h:
            return
        
        # Grid calculations
        visible_keys = int(content_h / 12)
        key_h = content_h / visible_keys
        beat_w = 40  # Width of one beat
        
        rel_x = x - content_x
        rel_y = y - content_y
        
        beat = int(rel_x / beat_w)
        key = int(rel_y / key_h) + self.piano_roll_scroll_y
        
        # Check if note exists at this position
        notes = track.get('notes', [])
        note_found = None
        for i, note in enumerate(notes):
            if note['beat'] == beat and note['key'] == key:
                note_found = i
                break
        
        if note_found is not None:
            # Remove note
            notes.pop(note_found)
            print(f"[Piano Roll] Removed note at beat {beat}, key {key}")
        else:
            # Add note
            notes.append({'beat': beat, 'key': key, 'length': 1, 'velocity': 100})
            print(f"[Piano Roll] Added note at beat {beat}, key {key}")
        
        track['notes'] = notes
        self.save_state()

    def get_track_default_view(self, track_kind):
        """Map a track kind to its default right-pane view."""
        if track_kind == 'piano':
            return 1  # Piano Roll
        return 0  # Waveform for audio tracks

    def draw_track_view_content(self, area, view_index):
        """Draw one lane content block using the selected view type."""
        if view_index == 0:
            self.draw_waveform_preview(area)
        elif view_index == 1:
            self.draw_piano_roll_preview(area)
        else:
            self.draw_spectrum_preview(area)
    
    def init_font(self):
        """Initialize font for text rendering"""
        if not HAS_PIL:
            return
        
        font_candidates = [
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\seguisb.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
            "segoeui.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "arial.ttf",
        ]
        for font_path in font_candidates:
            try:
                self.pil_font = ImageFont.truetype(font_path, 14)
                self.font_name = os.path.basename(font_path)
                return
            except OSError:
                continue
        
        # Last-resort fallback.
        self.pil_font = ImageFont.load_default()
        self.font_name = "PIL default"
    
    def render_text_to_texture(self, text, text_color=(210, 210, 220, 255)):
        """Render text using PIL and convert to an OpenGL texture."""
        if not HAS_PIL or self.pil_font is None:
            return None
        
        # Check cache first
        cache_key = (text, text_color)
        if cache_key in self.text_textures:
            return self.text_textures[cache_key]
        
        # Measure exact text bounds and render with transparent background.
        measure_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        measure_draw = ImageDraw.Draw(measure_img)
        left, top, right, bottom = measure_draw.textbbox((0, 0), text, font=self.pil_font)
        text_width = max(1, right - left)
        text_height = max(1, bottom - top)
        
        pad_x = 3
        pad_y = 2
        img_width = int(text_width + (pad_x * 2))
        img_height = int(text_height + (pad_y * 2))
        
        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((pad_x - left, pad_y - top), text, font=self.pil_font, fill=text_color)
        
        # Convert PIL image to OpenGL texture
        img_data = img.tobytes()
        texture_id = glGenTextures(1)
        
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Cache the texture
        self.text_textures[cache_key] = {
            'id': texture_id,
            'width': img.width,
            'height': img.height
        }
        
        return self.text_textures[cache_key]
    
    def draw_text_quad(self, x, y, width, height, texture_info):
        """Draw a textured quad for rendered text"""
        if texture_info is None:
            return
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_info['id'])
        
        glColor4f(1.0, 1.0, 1.0, 1.0)  # White to show texture colors
        glBegin(GL_QUADS)
        
        # Texture coordinates and vertex positions (Pillow data is top-left origin)
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        
        glTexCoord2f(1, 0)
        glVertex2f(x + width, y)
        
        glTexCoord2f(1, 1)
        glVertex2f(x + width, y + height)
        
        glTexCoord2f(0, 1)
        glVertex2f(x, y + height)
        
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def draw_simple_text(self, x, y, text, color=(0.82, 0.82, 0.86, 1.0), size=14):
        """Draw text using Pillow textures."""
        text_color = (
            int(max(0.0, min(1.0, color[0])) * 255),
            int(max(0.0, min(1.0, color[1])) * 255),
            int(max(0.0, min(1.0, color[2])) * 255),
            int(max(0.0, min(1.0, color[3])) * 255),
        )
        texture = self.render_text_to_texture(text, text_color)
        if texture:
            self.draw_text_quad(x, y, texture['width'], texture['height'], texture)
    
    def initialize(self):
        """Initialize GLFW and OpenGL"""
        if not glfw.init():
            print("Failed to initialize GLFW")
            sys.exit(1)
        
        # Create window
        self.window = glfw.create_window(
            self.width, self.height, self.title, None, None
        )
        
        if not self.window:
            print("Failed to create GLFW window")
            glfw.terminate()
            sys.exit(1)
        
        glfw.make_context_current(self.window)
        glfw.set_window_size_callback(self.window, self.on_window_resize)
        glfw.set_key_callback(self.window, self.on_key)
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)
        
        # Setup OpenGL
        glClearColor(0.1, 0.1, 0.12, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.setup_projection()
    
    def setup_projection(self):
        """Setup 2D orthographic projection"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def on_window_resize(self, window, width, height):
        """Handle window resize"""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.setup_projection()
    
    def on_key(self, window, key, scancode, action, mods):
        """Handle keyboard input"""
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)
    
    def on_mouse_button(self, window, button, action, mods):
        """Handle mouse input"""
        if button == glfw.MOUSE_BUTTON_LEFT:
            x, y = glfw.get_cursor_pos(window)
            
            if action == glfw.PRESS:
                # Check if clicking on menu items in dropdown
                if self.open_menu is not None:
                    panels = self.get_panel_dimensions()
                    menu_panel = panels['top_bar_menu']
                    menu_item_width = menu_panel['w'] / len(self.menu_items)
                    menu_x = menu_panel['x'] + (self.open_menu * menu_item_width)
                    menu_y = menu_panel['y'] + menu_panel['h']
                    
                    # Get dropdown items for this menu
                    dropdown_items = self.menu_items_data[self.open_menu]
                    
                    # Check if click is inside dropdown
                    if x > menu_x and x < menu_x + menu_item_width:
                        item_index = int((y - menu_y) / self.menu_item_height)
                        if 0 <= item_index < len(dropdown_items):
                            item_name = dropdown_items[item_index]
                            self.handle_menu_action(self.open_menu, item_name)
                            self.open_menu = None  # Close menu after selection
                        else:
                            self.open_menu = None
                    else:
                        self.open_menu = None
                
                # Check if clicking on menu items in top bar
                panels = self.get_panel_dimensions()
                menu_panel = panels['top_bar_menu']
                
                if y > menu_panel['y'] and y < menu_panel['y'] + menu_panel['h']:
                    menu_item_width = menu_panel['w'] / len(self.menu_items)
                    for i, item in enumerate(self.menu_items):
                        item_x = menu_panel['x'] + (i * menu_item_width)
                        item_x_end = item_x + menu_item_width
                        if x > item_x and x < item_x_end:
                            # Toggle menu open/close
                            if self.open_menu == i:
                                self.open_menu = None
                            else:
                                self.open_menu = i

                # Handle middle workspace controls (track list and editor mode buttons)
                if self.handle_middle_workspace_click(x, y, panels):
                    return
                
                # Check if clicking on vertical divider (between middle panels)
                v_div_x = panels['middle_left']['x'] + panels['middle_left']['w']
                
                if abs(x - v_div_x) < self.divider_width:
                    self.dragging_vertical = True
                    self.last_mouse_x = x
                
                # Check if clicking on horizontal divider (between middle and bottom)
                h_div_y = panels['middle_left']['y'] + panels['middle_left']['h']
                
                if abs(y - h_div_y) < self.divider_width:
                    self.dragging_horizontal = True
                    self.last_mouse_y = y
            
            elif action == glfw.RELEASE:
                # Save state after any drag operation completes
                if self.dragging_vertical or self.dragging_horizontal:
                    self.save_state()
                self.dragging_vertical = False
                self.dragging_horizontal = False
    
    def on_mouse_move(self, window, x, y):
        """Handle mouse movement for dragging dividers"""
        if self.dragging_vertical:
            delta = x - self.last_mouse_x
            # Adjust middle split ratio based on mouse movement
            new_ratio = self.middle_split_ratio + (delta / self.width)
            # Constrain ratio between 0.2 and 0.8
            self.middle_split_ratio = max(0.2, min(0.8, new_ratio))
            self.last_mouse_x = x
        
        if self.dragging_horizontal:
            delta = y - self.last_mouse_y
            # Adjust bottom height based on mouse movement
            new_bottom_height = self.bottom_height - delta
            # Constrain bottom height between 100 and 600 pixels
            self.bottom_height = max(100, min(600, new_bottom_height))
            self.last_mouse_y = y
        
        # Update cursor style based on hovering over dividers
        panels = self.get_panel_dimensions()
        v_div_x = panels['middle_left']['x'] + panels['middle_left']['w']
        h_div_y = panels['middle_left']['y'] + panels['middle_left']['h']
        
        is_over_v_div = abs(x - v_div_x) < self.divider_width and \
                        y > panels['middle_left']['y'] and y < h_div_y
        is_over_h_div = abs(y - h_div_y) < self.divider_width and \
                        x > 0 and x < self.width
        
        # Check if hovering over menu items
        menu_panel = panels['top_bar_menu']
        self.hovered_menu = None
        self.hovered_dropdown_item = None
        
        if y > menu_panel['y'] and y < menu_panel['y'] + menu_panel['h']:
            menu_item_width = menu_panel['w'] / len(self.menu_items)
            for i, item in enumerate(self.menu_items):
                item_x = menu_panel['x'] + (i * menu_item_width)
                item_x_end = item_x + menu_item_width
                if x > item_x and x < item_x_end:
                    self.hovered_menu = i
        # Check if hovering over dropdown items
        elif self.open_menu is not None:
            menu_item_width = menu_panel['w'] / len(self.menu_items)
            menu_x = menu_panel['x'] + (self.open_menu * menu_item_width)
            menu_y = menu_panel['y'] + menu_panel['h']
            
            if x > menu_x and x < menu_x + menu_item_width:
                item_index = int((y - menu_y) / self.menu_item_height)
                dropdown_items = self.menu_items_data[self.open_menu]
                if 0 <= item_index < len(dropdown_items):
                    self.hovered_dropdown_item = item_index
        
        if is_over_v_div or self.dragging_vertical:
            cursor = glfw.create_standard_cursor(glfw.HRESIZE_CURSOR)
            glfw.set_cursor(window, cursor)
        elif is_over_h_div or self.dragging_horizontal:
            cursor = glfw.create_standard_cursor(glfw.VRESIZE_CURSOR)
            glfw.set_cursor(window, cursor)
        else:
            cursor = glfw.create_standard_cursor(glfw.ARROW_CURSOR)
            glfw.set_cursor(window, cursor)
    
    def draw_rect(self, x, y, width, height, color, fill=True):
        """Draw a rectangle"""
        glColor4f(*color)
        if fill:
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + width, y)
            glVertex2f(x + width, y + height)
            glVertex2f(x, y + height)
            glEnd()
        else:
            glLineWidth(self.border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x, y)
            glVertex2f(x + width, y)
            glVertex2f(x + width, y + height)
            glVertex2f(x, y + height)
            glEnd()

    def draw_waveform_preview(self, area):
        """Draw a simple waveform preview for the right pane."""
        center_y = area['y'] + (area['h'] * 0.5)

        glLineWidth(1)
        glColor4f(0.24, 0.28, 0.34, 1.0)
        glBegin(GL_LINES)
        for step in range(0, 11):
            x = area['x'] + ((area['w'] / 10.0) * step)
            glVertex2f(x, area['y'])
            glVertex2f(x, area['y'] + area['h'])
        glEnd()

        glColor4f(0.36, 0.43, 0.54, 1.0)
        glBegin(GL_LINES)
        glVertex2f(area['x'], center_y)
        glVertex2f(area['x'] + area['w'], center_y)
        glEnd()

        glLineWidth(2)
        glColor4f(0.47, 0.77, 0.92, 1.0)
        glBegin(GL_LINE_STRIP)
        samples = 220
        for i in range(samples + 1):
            t = i / float(samples)
            x = area['x'] + 8 + (t * (area['w'] - 16))
            amp = (math.sin(t * 18.0) * 0.48) + (math.sin(t * 42.0) * 0.18)
            y = center_y + (amp * (area['h'] * 0.24))
            glVertex2f(x, y)
        glEnd()

    def draw_piano_roll_preview(self, area):
        """Draw a simple piano-roll style grid preview."""
        self.draw_rect(area['x'], area['y'], area['w'], area['h'], (0.13, 0.16, 0.2, 1.0), fill=True)

        glLineWidth(1)
        glColor4f(0.2, 0.24, 0.3, 1.0)
        glBegin(GL_LINES)
        for row in range(0, 13):
            y = area['y'] + ((area['h'] / 12.0) * row)
            glVertex2f(area['x'], y)
            glVertex2f(area['x'] + area['w'], y)
        for col in range(0, 17):
            x = area['x'] + ((area['w'] / 16.0) * col)
            glVertex2f(x, area['y'])
            glVertex2f(x, area['y'] + area['h'])
        glEnd()

        note_color = (0.49, 0.73, 0.95, 0.95)
        notes = [
            (1, 8, 3),
            (4, 7, 2),
            (7, 9, 4),
            (12, 6, 2),
        ]
        cell_w = area['w'] / 16.0
        cell_h = area['h'] / 12.0
        for beat, key_row, length in notes:
            nx = area['x'] + (beat * cell_w) + 2
            ny = area['y'] + (key_row * cell_h) + 2
            nw = (length * cell_w) - 4
            nh = cell_h - 4
            self.draw_rect(nx, ny, nw, nh, note_color, fill=True)

    def draw_spectrum_preview(self, area):
        """Draw a simple spectrum-like meter preview."""
        self.draw_rect(area['x'], area['y'], area['w'], area['h'], (0.12, 0.16, 0.18, 1.0), fill=True)

        bar_count = 28
        gap = 3
        bar_w = (area['w'] - ((bar_count + 1) * gap)) / bar_count
        for i in range(bar_count):
            t = i / float(max(1, bar_count - 1))
            level = (0.25 + (math.sin((t * 8.0) + 0.8) * 0.35) + (math.sin((t * 19.0) + 1.2) * 0.1))
            level = max(0.08, min(0.92, level))
            bh = area['h'] * level
            bx = area['x'] + gap + (i * (bar_w + gap))
            by = area['y'] + area['h'] - bh
            if level > 0.75:
                color = (0.93, 0.42, 0.36, 0.95)
            elif level > 0.5:
                color = (0.9, 0.69, 0.33, 0.95)
            else:
                color = (0.44, 0.78, 0.53, 0.95)
            self.draw_rect(bx, by, bar_w, bh, color, fill=True)

    def draw_middle_left_workspace(self, panels):
        """Draw track control UI in the left middle pane."""
        ui = self.get_left_workspace_ui(panels)

        self.draw_rect(ui['header']['x'], ui['header']['y'], ui['header']['w'], ui['header']['h'], (0.1, 0.13, 0.17, 1.0), fill=True)

        for tab in ui['tabs']:
            is_active = (tab['index'] == self.active_left_panel_mode)
            tab_color = (0.23, 0.27, 0.34, 1.0) if is_active else (0.16, 0.2, 0.25, 1.0)
            self.draw_rect(tab['x'], tab['y'], tab['w'], tab['h'], tab_color, fill=True)
            self.draw_simple_text(tab['x'] + 6, tab['y'] + 5, tab['label'], (0.83, 0.86, 0.9, 1.0))

        if self.active_left_panel_mode == 0:
            self.draw_rect(ui['add_audio']['x'], ui['add_audio']['y'], ui['add_audio']['w'], ui['add_audio']['h'], (0.19, 0.3, 0.24, 1.0), fill=True)
            self.draw_rect(ui['add_piano']['x'], ui['add_piano']['y'], ui['add_piano']['w'], ui['add_piano']['h'], (0.22, 0.2, 0.32, 1.0), fill=True)
            self.draw_simple_text(ui['add_audio']['x'] + 6, ui['add_audio']['y'] + 5, ui['add_audio']['label'], (0.86, 0.92, 0.88, 1.0))
            self.draw_simple_text(ui['add_piano']['x'] + 6, ui['add_piano']['y'] + 5, ui['add_piano']['label'], (0.86, 0.89, 0.94, 1.0))

            for row in ui['rows']:
                track = row['track']
                selected = (row['index'] == self.selected_track_index)
                row_color = (0.22, 0.27, 0.33, 1.0) if selected else (0.17, 0.22, 0.28, 1.0)
                self.draw_rect(row['x'], row['y'], row['w'], row['h'], row_color, fill=True)

                track_label = f"{row['index'] + 1:02d}  {track['name']}"
                kind_label = 'AUDIO' if track['kind'] == 'audio' else 'PIANO'
                self.draw_simple_text(row['x'] + 8, row['y'] + 8, track_label, (0.84, 0.87, 0.91, 1.0))
                self.draw_simple_text(row['x'] + row['w'] - 62, row['y'] + 8, kind_label, (0.73, 0.8, 0.9, 1.0))
        else:
            mode_label = self.left_panel_modes[self.active_left_panel_mode]
            self.draw_simple_text(ui['panel']['x'] + 10, ui['panel']['y'] + 44, f"{mode_label} mode")
            self.draw_simple_text(ui['panel']['x'] + 10, ui['panel']['y'] + 64, "Reserved for future tools")

    def draw_middle_right_workspace(self, panels):
        """Draw editor UI in the right middle pane based on selected track/view."""
        ui = self.get_right_workspace_ui(panels)
        selected_track = self.get_selected_track()

        self.draw_rect(ui['header']['x'], ui['header']['y'], ui['header']['w'], ui['header']['h'], (0.11, 0.14, 0.18, 1.0), fill=True)

        # Focus toggle button
        focus_btn = ui.get('focus_button', {})
        if focus_btn:
            focus_color = (0.35, 0.50, 0.65, 1.0) if self.focused_track_index is not None else (0.20, 0.25, 0.32, 1.0)
            self.draw_rect(focus_btn['x'], focus_btn['y'], focus_btn['w'], focus_btn['h'], focus_color, fill=True)
            self.draw_simple_text(focus_btn['x'] + 6, focus_btn['y'] + 4, focus_btn['label'], (0.85, 0.90, 0.95, 1.0))

        if selected_track:
            current_view = selected_track.get('view', 0)
            focus_text = " [FOCUSED]" if self.focused_track_index is not None else ""
            title = f"{selected_track['name']} -> {self.right_panel_views[current_view]}{focus_text}"
        else:
            title = f"Project View -> {self.right_panel_views[self.active_right_view]}"
        self.draw_simple_text(ui['panel']['x'] + 72, ui['panel']['y'] + 8, title, (0.84, 0.88, 0.92, 1.0))

        for button in ui['buttons']:
            current_view = selected_track.get('view', 0) if selected_track else 0
            is_active = (button['index'] == current_view)
            button_color = (0.24, 0.3, 0.36, 1.0) if is_active else (0.16, 0.2, 0.24, 1.0)
            self.draw_rect(button['x'], button['y'], button['w'], button['h'], button_color, fill=True)
            self.draw_simple_text(button['x'] + 8, button['y'] + 4, button['label'], (0.82, 0.86, 0.9, 1.0))

        for row in ui['rows']:
            is_selected = (row['index'] == self.selected_track_index)
            is_focused = (self.focused_track_index == row['index'])
            lane_bg = (0.2, 0.24, 0.3, 1.0) if is_selected else (0.15, 0.19, 0.25, 1.0)
            self.draw_rect(row['x'], row['y'], row['w'], row['h'], lane_bg, fill=True)

            track = row['track']
            lane_view = track.get('view', 0)
            
            # For focused tracks, use full area for content
            if is_focused:
                content_area = {
                    'x': row['x'] + 4,
                    'y': row['y'] + 4,
                    'w': max(10, row['w'] - 8),
                    'h': max(10, row['h'] - 8),
                }
                # Draw full piano roll for focused piano tracks
                if lane_view == 1 and track.get('kind') == 'piano':
                    self.draw_piano_roll_full(content_area, track)
                else:
                    self.draw_track_view_content(content_area, lane_view)
            else:
                # Mini preview for non-focused tracks
                lane_view_label = self.right_panel_views[lane_view]
                self.draw_simple_text(row['x'] + 8, row['y'] + 8, lane_view_label, (0.78, 0.83, 0.9, 1.0))

                content_area = {
                    'x': row['x'] + 110,
                    'y': row['y'] + 3,
                    'w': max(10, row['w'] - 114),
                    'h': max(10, row['h'] - 6),
                }
                self.draw_track_view_content(content_area, lane_view)

        # Draw placeholder in case there are no visible rows.
        if not ui['rows']:
            self.draw_simple_text(ui['content']['x'] + 8, ui['content']['y'] + 8, "No tracks in view", (0.8, 0.84, 0.9, 1.0))
    
    def draw_menu_buttons(self, panels):
        """Draw menu buttons in the top bar menu section"""
        menu_panel = panels['top_bar_menu']
        menu_item_width = menu_panel['w'] / len(self.menu_items)
        
        for i, item in enumerate(self.menu_items):
            item_x = menu_panel['x'] + (i * menu_item_width)
            item_y = menu_panel['y']
            
            # Determine button color (darker if hovered or open)
            if self.hovered_menu == i or self.open_menu == i:
                button_color = (0.25, 0.25, 0.3, 1.0)  # Hover/open color
            else:
                button_color = self.colors['top_bar']  # Normal color
            
            # Draw button background
            self.draw_rect(item_x + 2, item_y + 2, menu_item_width - 4, 
                          menu_panel['h'] - 4, button_color, fill=True)
            
            # Draw text label
            if HAS_PIL:
                text_texture = self.render_text_to_texture(item, (220, 220, 230, 255))
                if text_texture:
                    text_x = item_x + ((menu_item_width - text_texture['width']) / 2)
                    text_y = item_y + ((menu_panel['h'] - text_texture['height']) / 2)
                    self.draw_text_quad(int(text_x), int(text_y), text_texture['width'], text_texture['height'], text_texture)
    
    def draw_dropdown_menus(self, panels):
        """Draw dropdown menus when open"""
        if self.open_menu is None:
            return
        
        menu_panel = panels['top_bar_menu']
        menu_item_width = menu_panel['w'] / len(self.menu_items)
        menu_x = menu_panel['x'] + (self.open_menu * menu_item_width)
        menu_y = menu_panel['y'] + menu_panel['h']
        
        dropdown_items = self.menu_items_data[self.open_menu]
        dropdown_width = menu_item_width - 4
        dropdown_height = len(dropdown_items) * self.menu_item_height
        
        # Draw dropdown background
        self.draw_rect(menu_x + 2, menu_y, dropdown_width, dropdown_height, 
                      (0.18, 0.18, 0.22, 1.0), fill=True)
        
        # Draw dropdown border
        glLineWidth(2)
        glColor4f(*self.border_color)
        glBegin(GL_LINE_LOOP)
        glVertex2f(menu_x + 2, menu_y)
        glVertex2f(menu_x + dropdown_width + 2, menu_y)
        glVertex2f(menu_x + dropdown_width + 2, menu_y + dropdown_height)
        glVertex2f(menu_x + 2, menu_y + dropdown_height)
        glEnd()
        
        # Draw menu items
        for i, item in enumerate(dropdown_items):
            item_y = menu_y + (i * self.menu_item_height)
            
            # Draw item background (lighter on hover)
            if self.hovered_dropdown_item == i:
                item_color = (0.28, 0.28, 0.32, 1.0)  # Highlight on hover
            else:
                item_color = (0.22, 0.22, 0.27, 1.0)
            
            self.draw_rect(menu_x + 2, item_y, dropdown_width, self.menu_item_height, 
                          item_color, fill=True)
            
            # Draw text label
            if HAS_PIL:
                text_texture = self.render_text_to_texture(item, (210, 210, 220, 255))
                if text_texture:
                    text_x = menu_x + 8
                    text_y = item_y + ((self.menu_item_height - text_texture['height']) / 2)
                    self.draw_text_quad(int(text_x), int(text_y), text_texture['width'], text_texture['height'], text_texture)
    
    def get_panel_dimensions(self):
        """Calculate panel dimensions based on window size and layout"""
        available_height = self.height - self.top_bar_height - self.bottom_height - self.divider_width
        middle_left_width = int(self.width * self.middle_split_ratio)
        middle_right_width = self.width - middle_left_width - self.divider_width
        
        # Top bar split 20/80 for menu/content (no divider between them)
        top_bar_menu_width = int(self.width * 0.20)
        top_bar_content_width = self.width - top_bar_menu_width
        
        return {
            'top_bar_menu': {'x': 0, 'y': 0, 'w': top_bar_menu_width, 'h': self.top_bar_height},
            'top_bar_content': {'x': top_bar_menu_width, 'y': 0, 'w': top_bar_content_width, 'h': self.top_bar_height},
            'middle_left': {'x': 0, 'y': self.top_bar_height, 'w': middle_left_width, 'h': available_height},
            'v_divider': {'x': middle_left_width, 'y': self.top_bar_height, 'w': self.divider_width, 'h': available_height},
            'middle_right': {'x': middle_left_width + self.divider_width, 'y': self.top_bar_height, 'w': middle_right_width, 'h': available_height},
            'h_divider': {'x': 0, 'y': self.top_bar_height + available_height, 'w': self.width, 'h': self.divider_width},
            'bottom': {'x': 0, 'y': self.top_bar_height + available_height + self.divider_width, 'w': self.width, 'h': self.bottom_height},
        }
    
    def render(self):
        """Render the grid layout"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        panels = self.get_panel_dimensions()
        
        # Draw main panels
        main_panels = ['top_bar_menu', 'top_bar_content', 'middle_left', 'middle_right', 'bottom']
        for panel_name in main_panels:
            if panel_name in panels:
                p = panels[panel_name]
                color = self.colors.get(panel_name, (0.5, 0.5, 0.5, 1.0))
                # Use slightly different color for top_bar_content
                if panel_name == 'top_bar_content':
                    color = (0.22, 0.22, 0.27, 1.0)
                self.draw_rect(p['x'], p['y'], p['w'], p['h'], color, fill=True)
        
        # Draw menu buttons
        self.draw_menu_buttons(panels)

        # Draw DAW workspace controls and editors in middle panes
        self.draw_middle_left_workspace(panels)
        self.draw_middle_right_workspace(panels)
        
        # Draw dividers
        v_div = panels['v_divider']
        h_div = panels['h_divider']
        
        # Determine divider colors based on hover state
        x, y = glfw.get_cursor_pos(self.window)
        
        v_div_hover = abs(x - (v_div['x'] + v_div['w'] / 2)) < self.divider_width and \
                      y > v_div['y'] and y < v_div['y'] + v_div['h']
        h_div_hover = abs(y - (h_div['y'] + h_div['h'] / 2)) < self.divider_width and \
                      x > h_div['x'] and x < h_div['x'] + h_div['w']
        
        v_color = self.divider_hover_color if (v_div_hover or self.dragging_vertical) else self.divider_color
        h_color = self.divider_hover_color if (h_div_hover or self.dragging_horizontal) else self.divider_color
        
        self.draw_rect(v_div['x'], v_div['y'], v_div['w'], v_div['h'], v_color, fill=True)
        self.draw_rect(h_div['x'], h_div['y'], h_div['w'], h_div['h'], h_color, fill=True)
        
        # Draw borders around main panels
        glLineWidth(self.border_width)
        for panel_name in main_panels:
            if panel_name in panels:
                p = panels[panel_name]
                self.draw_rect(p['x'], p['y'], p['w'], p['h'], self.border_color, fill=False)
        
        # Draw dropdown menus last so they appear on top of everything
        self.draw_dropdown_menus(panels)
        
        glfw.swap_buffers(self.window)
    
    def print_layout_info(self):
        """Print current layout information"""
        panels = self.get_panel_dimensions()
        print("\n" + "="*70)
        print(f"Window Size: {self.width}x{self.height}")
        print(f"Top Bar Menu Items: {' | '.join(self.menu_items)}")
        for menu_idx, items in self.menu_items_data.items():
            print(f"  {self.menu_items[menu_idx]}: {', '.join(items)}")
        print(f"Top Bar: Menu (20%) | Content (80%)")
        print(f"Middle Split Ratio: {self.middle_split_ratio*100:.1f}% / {(1-self.middle_split_ratio)*100:.1f}%")
        print(f"Bottom Panel Height: {self.bottom_height}px")
        print(f"Divider Width: {self.divider_width}px")
        print("Panel Dimensions:")
        for name in ['top_bar_menu', 'top_bar_content', 'middle_left', 'v_divider', 'middle_right', 'h_divider', 'bottom']:
            if name in panels:
                dims = panels[name]
                print(f"  {name:18}: x={dims['x']:4}, y={dims['y']:4}, w={dims['w']:4}, h={dims['h']:4}")
        print("="*70 + "\n")
    
    def run(self):
        """Main application loop"""
        print("Starting Grid View Application (Simple DAW - Audacity/Blender inspired)")
        print("Layout: Top Bar (Menu 20% | Content 80%) | Middle (30/70 split) | Bottom")
        print("\nFeatures:")
        print(f"  - File dialog support: {'✓ Available (tkinter)' if HAS_TKINTER else '✗ Not available'}")
        print(f"  - Font rendering: {'✓ Pillow/PIL enabled' if HAS_PIL else '✗ Not available'}")
        if HAS_PIL:
            print(f"  - Active font: {self.font_name}")
        print("\nControls:")
        print("  - ESC: Close window")
        print("  - File menu: New (create new project), Open (file picker), Save, Exit")
        print("  - Click menu items (File, Edit, Settings) to open dropdown menus")
        print("  - Click items in dropdown to execute them")
        print("  - Resize window to see layout adapt")
        print("  - Drag vertical divider (between middle panels) to adjust left/right split")
        print("  - Drag horizontal divider (between middle and bottom) to adjust heights")
        print("  - Cursor changes to indicate draggable dividers")
        self.print_layout_info()
        
        while not glfw.window_should_close(self.window):
            self.render()
            glfw.poll_events()
        
        glfw.destroy_window(self.window)
        glfw.terminate()
        print("Application closed")


if __name__ == "__main__":
    app = GridApplication(width=1200, height=800, title="Grid View App - GLFW/OpenGL")
    app.run()
