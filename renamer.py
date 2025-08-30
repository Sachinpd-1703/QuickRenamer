from pathlib import Path


class FileRenamer:
    """Handles file renaming logic"""

    def generate_new_name(self, file_path, index, use_sequential, base_name, start_number,
                          number_padding, use_prefix, prefix_text, use_suffix, suffix_text):
        original_name = file_path.stem
        extension = file_path.suffix
        new_name = ""

        if use_sequential:
            try:
                start_num = int(start_number)
                padding = int(number_padding)
                number = start_num + index
                new_name = f"{base_name}{number:0{padding}d}"
            except ValueError:
                new_name = f"{base_name}{index + 1}"
        else:
            new_name = original_name

        if use_prefix and prefix_text:
            new_name = prefix_text + new_name

        if use_suffix and suffix_text:
            new_name = new_name + suffix_text

        return new_name + extension

    def get_safe_filename(self, directory, desired_name):
        full_path = directory / desired_name
        if not full_path.exists():
            return desired_name

        name_stem = full_path.stem
        extension = full_path.suffix
        counter = 1

        while True:
            safe_name = f"{name_stem}_{counter}{extension}"
            safe_path = directory / safe_name
            if not safe_path.exists():
                return safe_name
            counter += 1

    def rename_files(self, selected_files, preview_names):
        success_count = 0
        error_count = 0
        errors = []
        self.rename_history = []  # reset history each run

        for i, (old_path, new_name) in enumerate(zip(selected_files, preview_names)):
            try:
                safe_name = self.get_safe_filename(old_path.parent, new_name)
                new_path = old_path.parent / safe_name
                old_path.rename(new_path)

                # track rename history for undo
                self.rename_history.append((old_path, new_path))

                # update reference in list
                selected_files[i] = new_path
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"{old_path.name}: {str(e)}")

        # ✅ Only return 3 values (to match your GUI code)
        return success_count, error_count, errors

    def undo_last_rename(self):
        """Undo the last batch of renames (if possible)."""
        restored = 0
        for old_path, new_path in reversed(self.rename_history):
            try:
                if new_path.exists():
                    new_path.rename(old_path)
                    restored += 1
            except Exception:
                pass
        self.rename_history = []
        return restored