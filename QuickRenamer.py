import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import re

# tkinterdnd2 for drag-and-drop functionality
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    print("Warning: tkinterdnd2 not found. Drag-and-drop will be disabled.")
    print("Install with: pip install tkinterdnd2")


class BatchRenamer: #QuickRenamer
    """Main application class for the Batch File Renamer"""
    
    def __init__(self):
        # Initialize the main window
        if DRAG_DROP_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        self.root.title("QuickRenamer")
        self.root.iconbitmap("myicon.ico")
        self.root.resizable(False, False)
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Application state
        self.selected_files = []
        self.preview_names = []
        
        # Setup the GUI
        self.setup_gui()
        
        # Configure drag and drop if available.
        if DRAG_DROP_AVAILABLE:
            self.setup_drag_drop()
    
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection section
        self.setup_file_selection(main_frame)
        
        # Rename options section
        self.setup_rename_options(main_frame)
        
        # File list section
        self.setup_file_list(main_frame)
        
        # Action buttons section
        self.setup_action_buttons(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
    
    def setup_file_selection(self, parent):
        """Setup file selectionn controls"""
        # File selection frame
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Browse buton
        ttk.Button(file_frame, text="Browse Files", 
                  command=self.browse_files).grid(row=0, column=0, padx=(0, 10))
        
        # Drag and drop label
        if DRAG_DROP_AVAILABLE:
            drop_text = "Or drag and drop files here"
        else:
            drop_text = "Drag and drop not available (install tkinterdnd2)"
        
        self.drop_label = ttk.Label(file_frame, text=drop_text, 
                                   foreground="gray")
        self.drop_label.grid(row=0, column=1, sticky=tk.W)
        
        # Clear button-------------------------------------------
        ttk.Button(file_frame, text="Clear All", 
                  command=self.clear_files).grid(row=0, column=2)
    
    def setup_rename_options(self, parent):
        """Setup rename mode options"""
        # Rename options frame
        options_frame = ttk.LabelFrame(parent, text="Rename Options", padding="5")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # Sequential rename section-----------------------------------------------------------------------------------
        seq_frame = ttk.Frame(options_frame)
        seq_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        seq_frame.columnconfigure(1, weight=1)
        
        self.use_sequential = tk.BooleanVar()
        ttk.Checkbutton(seq_frame, text="Sequential rename:", 
                       variable=self.use_sequential,
                       command=self.update_preview).grid(row=0, column=0, sticky=tk.W)
        
        # Sequential options---------------------------------------------------------------------------------------
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
        
        # Prefix/Suffix section-------------------------------------------------------------------------------------
        prefix_frame = ttk.Frame(options_frame)
        prefix_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        prefix_frame.columnconfigure(1, weight=1)
        prefix_frame.columnconfigure(3, weight=1)
        
        # Prefix----------------------------------------------------------------------------------------------------
        self.use_prefix = tk.BooleanVar()
        ttk.Checkbutton(prefix_frame, text="Add prefix:", 
                       variable=self.use_prefix,
                       command=self.update_preview).grid(row=0, column=0, sticky=tk.W)
        
        self.prefix_text = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=self.prefix_text, width=20).grid(row=0, column=1, padx=(5, 20), sticky=(tk.W, tk.E))
        
        # Suffix-------------------------------------------------------------------------------------
        self.use_suffix = tk.BooleanVar()
        ttk.Checkbutton(prefix_frame, text="Add suffix:", 
                       variable=self.use_suffix,
                       command=self.update_preview).grid(row=0, column=2, sticky=tk.W)
        
        self.suffix_text = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=self.suffix_text, width=20).grid(row=0, column=3, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Bind events for live preview-------------------------------------------------------------------------------------
        for var in [self.base_name, self.start_number, self.number_padding, 
                   self.prefix_text, self.suffix_text]:
            var.trace('w', lambda *args: self.update_preview())
    
    def setup_file_list(self, parent):
        """Setup the file list display"""
        # File list frame-------------------------------------------------------------------------------------
        list_frame = ttk.LabelFrame(parent, text="Files to Rename", padding="5")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for file list-------------------------------------------------------------------------------------
        columns = ('original', 'preview')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Define headings-------------------------------------------------------------------------------------
        self.file_tree.heading('original', text='Original Name')
        self.file_tree.heading('preview', text='New Name (Preview)')
        
        # Configure column widths-------------------------------------------------------------------------------------
        self.file_tree.column('original', width=300)
        self.file_tree.column('preview', width=300)
        
        # Add scrollbars-------------------------------------------------------------------------------------
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout-------------------------------------------------------------------------------------
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def setup_action_buttons(self, parent):
        """Setup action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Preview button REMOVED as requested-----------------------------------------------------------------------

        ttk.Button(button_frame, text="Rename Files", 
                  command=self.rename_files).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit).pack(side=tk.LEFT)
    
    def setup_status_bar(self, parent):
        """Setup status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        if DRAG_DROP_AVAILABLE:
            self.file_tree.drop_target_register(DND_FILES)
            self.file_tree.dnd_bind('<<Drop>>', self.on_drop)
    
    def browse_files(self):
        """Open file dialog to select files"""
        files = filedialog.askopenfilenames(
            title="Select files to rename",
            filetypes=[("All files", "*.*")]
        )
        
        if files:
            self.add_files(files)
    
    def on_drop(self, event):
        """Handle drag and drop events"""
        files = self.file_tree.tk.splitlist(event.data)
        self.add_files(files)
    
    def add_files(self, file_paths):
        """Add files to the selection list"""
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
        """Clear all selected files"""
        self.selected_files.clear()
        self.preview_names.clear()
        self.update_file_list()
        self.status_var.set("File list cleared")
    
    def update_file_list(self):
        """Update the file list display"""
        # Clear existing items----------------------------------------
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Add files to tree----------------------------------------
        for i, file_path in enumerate(self.selected_files):
            original_name = file_path.name
            preview_name = self.preview_names[i] if i < len(self.preview_names) else ""
            self.file_tree.insert('', tk.END, values=(original_name, preview_name))
    
    def generate_new_name(self, file_path, index):
        """Generate new name for a file based on current settings"""
        original_name = file_path.stem
        extension = file_path.suffix
        new_name = ""
        
        # Apply sequential renaming----------------------------------------
        if self.use_sequential.get():
            try:
                start_num = int(self.start_number.get())
                padding = int(self.number_padding.get())
                number = start_num + index
                new_name = f"{self.base_name.get()}{number:0{padding}d}"
            except ValueError:
                new_name = f"{self.base_name.get()}{index + 1}"
        else:
            new_name = original_name
        
        # Apply prefix----------------------------------------
        if self.use_prefix.get() and self.prefix_text.get():
            new_name = self.prefix_text.get() + new_name
        
        # Apply suffix----------------------------------------
        if self.use_suffix.get() and self.suffix_text.get():
            new_name = new_name + self.suffix_text.get()
        
        return new_name + extension
    
    def update_preview(self):
        """Update the preview of new file names"""
        if not self.selected_files:
            return
        
        self.preview_names.clear()
        
        for i, file_path in enumerate(self.selected_files):
            new_name = self.generate_new_name(file_path, i)
            self.preview_names.append(new_name)
        
        self.update_file_list()
    
    def get_safe_filename(self, directory, desired_name):
        """Get a safe filename that doesn't conflict with existing files"""
        full_path = directory / desired_name
        
        if not full_path.exists():
            return desired_name
        
        # File exists, find a safe alternative----------------------------------------
        name_stem = full_path.stem
        extension = full_path.suffix
        counter = 1
        
        while True:
            safe_name = f"{name_stem}_{counter}{extension}"
            safe_path = directory / safe_name
            if not safe_path.exists():
                return safe_name
            counter += 1
    
    def rename_files(self):
        """Perform the actual file renaming"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "No files selected for renaming.")
            return
        
        if not self.preview_names:
            self.update_preview()
        
        # Confirm with user----------------------------------------
        if not messagebox.askyesno("Confirm Rename", 
                                  f"Are you sure you want to rename {len(self.selected_files)} files?"):
            return
        
        success_count = 0
        error_count = 0
        errors = []
        
        for i, (old_path, new_name) in enumerate(zip(self.selected_files, self.preview_names)):
            try:
                # Get safe filename to avoid conflicts
                safe_name = self.get_safe_filename(old_path.parent, new_name)
                new_path = old_path.parent / safe_name
                
                # Rename the file
                old_path.rename(new_path)
                success_count += 1
                
                # Update the selected files list with new path
                self.selected_files[i] = new_path
                
            except Exception as e:
                error_count += 1
                errors.append(f"{old_path.name}: {str(e)}")
        
        # Update status----------------------------------------
        if error_count == 0:
            self.status_var.set(f"Successfully renamed {success_count} files")
            messagebox.showinfo("Success", f"Successfully renamed {success_count} files!")
        else:
            self.status_var.set(f"Renamed {success_count} files, {error_count} errors")
            error_msg = f"Renamed {success_count} files with {error_count} errors:\n\n"
            error_msg += "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"
            messagebox.showerror("Rename Errors", error_msg)
        
        # Refresh the preview-----
        self.update_preview()
    
    def run(self):
        #Start the application
        self.root.mainloop()


def main():
    #Main entry pointt---------
    app = BatchRenamer()
    app.run()


if __name__ == "__main__":
    main()
