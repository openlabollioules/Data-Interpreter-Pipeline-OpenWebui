# import matplotlib.pyplot as plt  # plt.show(block=False) plt.savefig(path)
import ast


def extract_python(filepath):
    """Extrait des informations complètes d'un fichier Python (.py) en utilisant le module ast et en lisant le fichier directement."""
    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Utiliser ast pour parser le fichier Python
    parsed_code = ast.parse(file_content)
    extracted_data = {
        "module_code": file_content,
        "functions": [],
        "classes": [],
        "imports": [],
        "docstrings": ast.get_docstring(parsed_code),
    }

    # Parcourir l'arbre de syntaxe abstraite (AST)
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            function_info = {
                "name": node.name,
                "arguments": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
                "line_number": node.lineno,
                "content": ast.get_source_segment(
                    file_content, node
                ),  # Récupérer le contenu exact de la fonction
            }
            extracted_data["functions"].append(function_info)

        elif isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "methods": [],
                "docstring": ast.get_docstring(node),
                "line_number": node.lineno,
                "content": ast.get_source_segment(
                    file_content, node
                ),  # Récupérer le contenu exact de la classe
            }
            # Ajouter les méthodes de la classe
            for class_node in node.body:
                if isinstance(class_node, ast.FunctionDef):
                    method_info = {
                        "name": class_node.name,
                        "arguments": [arg.arg for arg in class_node.args.args],
                        "docstring": ast.get_docstring(class_node),
                        "line_number": class_node.lineno,
                        "content": ast.get_source_segment(
                            file_content, class_node
                        ),  # Récupérer le contenu exact de la méthode
                    }
                    class_info["methods"].append(method_info)
            extracted_data["classes"].append(class_info)

        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            import_info = {
                "module": getattr(node, "module", None),
                "names": [alias.name for alias in node.names],
                "line_number": node.lineno,
            }
            extracted_data["imports"].append(import_info)

    return extracted_data
