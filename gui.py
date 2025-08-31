import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from renamer import FileRenamer
from utils import resource_path, check_drag_drop, DRAG_DROP_AVAILABLE, DND_FILES


class BatchRenamer:
    """Main application class for the Batch File Renamer"""

    def __init__(self):
        if DRAG_DROP_AVAILABLE:
            from tkinterdnd2 import TkinterDnD
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        try:
            icon_file = resource_path("myicon.ico")
            self.root.iconbitmap(icon_file)
        except Exception as e:
            print(f"Icon not found or failed to load, using default. ({e})")

        self.root.title("QuickRenamer")
        self.center_window(800, 600)
        self.root.resizable(False, False)

        # Start with dark mode
        # Theme Management
        self.style = ttk.Style(self.root)
        self.theme_var = tk.StringVar(value="dark")
        self.style.theme_use("xpnative")

        # State
        self.selected_files = []
        self.preview_names = []
        self.renamer = FileRenamer()

        # Setup GUI
        self.setup_gui()

        # Drag & Drop
        if DRAG_DROP_AVAILABLE:
            self.setup_drag_drop()

    # ---------------- GUI Setup ----------------

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        self.setup_file_selection(main_frame)
        self.setup_rename_options(main_frame)
        self.setup_file_list(main_frame)
        self.setup_action_buttons(main_frame)
        self.setup_status_bar(main_frame)

    def setup_file_selection(self, parent):
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Button(file_frame, text="Browse Files", command=self.browse_files).grid(row=0, column=0, padx=(0, 10))

        if DRAG_DROP_AVAILABLE:
            drop_text = "Or drag and drop files here"
        else:
            drop_text = "Drag and drop not available (install tkinterdnd2)"

        self.drop_label = ttk.Label(file_frame, text=drop_text, foreground="gray")
        self.drop_label.grid(row=0, column=1, sticky=tk.W)

        ttk.Button(file_frame, text="Clear All", command=self.clear_files).grid(row=0, column=2)

    def setup_rename_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="Rename Options", padding="5")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        # Sequential rename
        seq_frame = ttk.Frame(options_frame)
        seq_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        seq_frame.columnconfigure(1, weight=1)

        self.use_sequential = tk.BooleanVar()
        ttk.Checkbutton(seq_frame, text="Sequential rename:", variable=self.use_sequential,
                        command=self.update_preview).grid(row=0, column=0, sticky=tk.W)

        seq_options = ttk.Frame(seq_frame)
        seq_options.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(20, 0))

        ttk.Label(seq_options, text="Base name:").grid(row=0, column=0, sticky=tk.W)
        self.base_name = tk.StringVar(value="file")
        ttk.Entry(seq_options, textvariable=self.base_name, width=15).grid(row=0, column=1, padx=(5, 10))

        ttk.Label(seq_options, text="Start number:").grid(row=0, column=2, sticky=tk.W)
        self.start_number = tk.StringVar(value="1")
        ttk.Entry(seq_options, textvariable=self.start_number, width=8).grid(row=0, column=3, padx=(5, 10))

        ttk.Label(seq_options, text="Padding:").grid(row=0, column=4, sticky=tk.W)
        self.number_padding = tk.StringVar(value="2")
        ttk.Entry(seq_options, textvariable=self.number_padding, width=5).grid(row=0, column=5, padx=(5, 0))

        # Prefix/Suffix
        prefix_frame = ttk.Frame(options_frame)
        prefix_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        prefix_frame.columnconfigure(1, weight=1)
        prefix_frame.columnconfigure(3, weight=1)

        self.use_prefix = tk.BooleanVar()
        ttk.Checkbutton(prefix_frame, text="Add prefix:", variable=self.use_prefix,
                        command=self.update_preview).grid(row=0, column=0, sticky=tk.W)
        self.prefix_text = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=self.prefix_text, width=20).grid(row=0, column=1, padx=(5, 20), sticky=(tk.W, tk.E))

        self.use_suffix = tk.BooleanVar()
        ttk.Checkbutton(prefix_frame, text="Add suffix:", variable=self.use_suffix,
                        command=self.update_preview).grid(row=0, column=2, sticky=tk.W)
        self.suffix_text = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=self.suffix_text, width=20).grid(row=0, column=3, padx=(5, 0), sticky=(tk.W, tk.E))

        for var in [self.base_name, self.start_number, self.number_padding, self.prefix_text, self.suffix_text]:
            var.trace('w', lambda *args: self.update_preview())

    def setup_file_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Files to Rename", padding="5")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        # naya toolbar for move up/down and remove
        button_toolbar = ttk.Frame(list_frame)
        button_toolbar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        # --- Move Up/Down & Remove Buttons ---
        ttk.Button(button_toolbar, text="▲ Move Up", command=self.move_item_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_toolbar, text="▼ Move Down", command=self.move_item_down).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_toolbar, text="Remove", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))

        # --- Theame ---
        self.theme_switch = ttk.Checkbutton(
            button_toolbar,
            text="Dark Mode",
            command=self.apply_theme,
        )
        self.theme_switch.pack(side=tk.RIGHT, padx=(5, 0))

        columns = ('original', 'preview')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        self.file_tree.heading('original', text='Original Name')
        self.file_tree.heading('preview', text='New Name (Preview)')
        self.file_tree.column('original', width=300)
        self.file_tree.column('preview', width=300)

        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.file_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=2, column=0, sticky=(tk.W, tk.E))

    def setup_action_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(button_frame, text="Redo", command=self.rename_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="undo", command=self.rename_files).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Rename Files", command=self.rename_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT)

    def setup_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def setup_drag_drop(self):
        self.file_tree.drop_target_register(DND_FILES)
        self.file_tree.dnd_bind('<<Drop>>', self.on_drop)

    def apply_theme(self):
        """Applies the selected (light or dark) theme to the application."""
        theme = self.theme_var.get()

        if theme == "dark":
            bg_color = "#221f1f"
            fg_color = "#FFFFFF"
            entry_bg = "#1c1e1f"
            entry_fg = "#4B4B4D"
            button_bg = "#2B2E2F"
            select_bg = '#0078d7'
            tree_heading_bg = '#3c3f41'
            drop_label_fg = "#FFFFFF"
            self.theme_var.set("light")
        else:
            bg_color = 'SystemButtonFace'
            fg_color = 'SystemWindowText'
            entry_bg = 'SystemWindow'
            entry_fg = 'SystemWindowText'
            button_bg = 'SystemButtonFace'
            select_bg = '#0078d7'
            tree_heading_bg = 'SystemButtonFace'
            drop_label_fg = 'gray'
            self.theme_var.set("dark")

        # Apply to root window
        self.root.configure(bg=bg_color)

        # --- Frame and Labels ---
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color)
        self.style.configure('TLabelframe', background=bg_color, foreground=fg_color, borderwidth=2)
        self.style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)

        # --- Buttons ---
        self.style.configure('TButton',
                            background=button_bg,
                            foreground=fg_color if theme == 'light' else 'black',
                            borderwidth=2,
                            focusthickness=2,
                            focuscolor=fg_color)
        self.style.map('TButton',
                    background=[('active', '#6e7274')],
                    foreground=[('disabled', '#a9a9a9')])

        # --- Checkbutton ---
        self.style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
        self.style.map('TCheckbutton',
                    background=[('active', bg_color)],
                    foreground=[('disabled', '#888888')])

        # --- Entry ---
        self.style.configure('TEntry',
                            fieldbackground=entry_bg,
                            foreground=entry_fg,
                            insertcolor=fg_color,
                            borderwidth=2,
                            focusthickness=2,
                            focuscolor=fg_color)

        # --- Treeview ---
        self.style.configure('Treeview',
                            background=entry_bg,
                            foreground=fg_color,
                            fieldbackground=entry_bg,
                            rowheight=25,
                            borderwidth=1)
        self.style.configure('Treeview.Heading',
                            background=tree_heading_bg,
                            foreground=fg_color if theme == 'light' else 'black',
                            relief='flat')
        self.style.map('Treeview.Heading',
                    background=[('active', button_bg)])
        self.style.map('Treeview',
                    background=[('selected', select_bg)],
                    foreground=[('selected', 'white')],
                    fieldbackground=[('selected', select_bg)])

        # --- Custom Widgets (drop label, status bar) ---
        if hasattr(self, 'drop_label'):
            self.drop_label.config(background=bg_color, foreground=drop_label_fg)

        if hasattr(self, 'status_bar'):
            self.status_bar.config(
                background=button_bg if theme == 'light' else bg_color,
                foreground=fg_color
            )

    def center_window(self, win_w, win_h):
        # Get the screen width and height
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Calculate position x, y
        x = (screen_w // 2) - (win_w // 2)
        y = (screen_h // 2) - (win_h // 2)

        # Set the geometry
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # ---------------- File Handling ----------------

    def browse_files(self):
        files = filedialog.askopenfilenames(title="Select files to rename", filetypes=[("All files", "*.*")])
        if files:
            self.add_files(files)

    def on_drop(self, event):
        files = self.file_tree.tk.splitlist(event.data)
        self.add_files(files)

    def add_files(self, file_paths):
        new_files = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.is_file() and str(path) not in [str(f) for f in self.selected_files]:
                new_files.append(path)

        self.selected_files.extend(new_files)
        self.update_file_list()
        self.update_preview()

        if new_files:
            self.status_var.set(f"Added {len(new_files)} files. Total: {len(self.selected_files)} files")

    def clear_files(self):
        """Clear all selected files and previews"""
        self.selected_files.clear()
        self.preview_names.clear()
        self.update_file_list()
        self.status_var.set("Cleared all files")
        self.update_preview()

    def update_file_list(self):
        """Update the file list display"""
        # Clear existing items
        self.file_tree.delete(*self.file_tree.get_children())
        
        # Add current files
        for idx, file_path in enumerate(self.selected_files):
            preview_name = self.preview_names[idx] if idx < len(self.preview_names) else ""
            self.file_tree.insert("", "end", values=(file_path.name, preview_name))

    def update_preview(self, *args):
        """Generate and update preview names for all selected files"""
        self.preview_names.clear()
        self.file_tree.delete(*self.file_tree.get_children())

        for idx, file_path in enumerate(self.selected_files):
            new_name = self.renamer.generate_new_name(
                file_path=file_path,
                index=idx,
                use_sequential=self.use_sequential.get(),
                base_name=self.base_name.get(),
                start_number=self.start_number.get(),
                number_padding=self.number_padding.get(),
                use_prefix=self.use_prefix.get(),
                prefix_text=self.prefix_text.get(),
                use_suffix=self.use_suffix.get(),
                suffix_text=self.suffix_text.get(),
            )
            self.preview_names.append(new_name)
            self.file_tree.insert("", "end", values=(file_path.name, new_name))

    def rename_files(self):
        """Execute the file renaming operation"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to rename first.")
            return

        if not self.preview_names:
            messagebox.showwarning("No Preview", "Please generate preview names first.")
            return

        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Rename", 
            f"Are you sure you want to rename {len(self.selected_files)} files?"
        )
        if not result:
            return

        # Perform the renaming
        self.status_var.set("Renaming files...")
        self.root.update()

        success_count, error_count, errors = self.renamer.rename_files(
            self.selected_files, self.preview_names
        )

        # Update status and show results
        if error_count == 0:
            self.status_var.set(f"Successfully renamed {success_count} files")
            messagebox.showinfo("Success", f"Successfully renamed {success_count} files!")
        else:
            self.status_var.set(f"Renamed {success_count} files, {error_count} errors")
            error_message = f"Renamed {success_count} files successfully.\n{error_count} errors occurred:\n\n"
            error_message += "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_message += f"\n... and {len(errors) - 10} more errors"
            messagebox.showerror("Rename Errors", error_message)

        # Refresh the file list with updated names
        self.update_file_list()
        self.update_preview()

    def move_item_up(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            return
        
        all_items = list(self.file_tree.get_children())
        # Sort selected items by their index ascending---- to avoid messing order when moving up
        selected_indices = sorted([all_items.index(item) for item in selected_items])
            
        for index in selected_indices:
            item = all_items[index]
            if index == 0:
                self.file_tree.move(item, '', 'end')
            else:
                self.file_tree.move(item, '', index - 1)
        
        # Re-select moved items----
        self.file_tree.selection_set(selected_items)

        for item in selected_items:
            self.file_tree.see(item)

    def move_item_down(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            return

        all_items = list(self.file_tree.get_children())

        selected_indices = sorted([all_items.index(item) for item in selected_items], reverse=True)

        for index in selected_indices:
            item = all_items[index]
            if index == len(all_items) - 1:
                self.file_tree.move(item, '', 0)
            else:
                self.file_tree.move(item, '', index + 1)

        self.file_tree.selection_set(selected_items)

        for item in selected_items:
            self.file_tree.see(item)

    def remove_selected(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a file to remove.")
            return
            
        # Highest index se remove karna shuru karein taaki index shift na ho
        indices_to_remove = sorted([self.file_tree.index(item) for item in selected_items], reverse=True)
        
        for index in indices_to_remove:
            self.selected_files.pop(index)
            
        self.update_preview()
        self.status_var.set(f"Removed {len(indices_to_remove)} files. Total: {len(self.selected_files)} files")

    def run(self):
        """Start the application"""
        self.root.mainloop()