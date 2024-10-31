import os


def print_directory_structure(root_dir, max_depth=2, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = [
            "venv",
            "__pycache__",
            ".git",
        ]  # Aggiungi altre cartelle da escludere

    for root, dirs, files in os.walk(root_dir):
        # Calcola il livello attuale rispetto alla root
        relative_path = os.path.relpath(root, root_dir)
        level = relative_path.count(os.sep)

        # Limita la profondità della scansione
        if level >= max_depth:
            dirs.clear()  # Evita di scendere ulteriormente in questa cartella
            continue

        # Rimuove le directory da ignorare dalla lista `dirs`
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Stampa la struttura delle directory e dei file con indentazione
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")

        sub_indent = " " * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")


# Specifica la root del progetto come la cartella sopra `utils`
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print_directory_structure(
    root_dir, max_depth=2, exclude_dirs=["venv", "__pycache__", ".git", "node_modules"]
)
