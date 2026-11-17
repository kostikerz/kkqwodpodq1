"""Generate PlantUML and render it locally using the official JAR."""

import os
import subprocess
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RENDER_TIMEOUT = 90


def plantuml(graph, root):
    """Create deterministic safe aliases and all dependency arrows."""
    names = sorted(graph.edges)
    aliases = {name: f"n{i}" for i, name in enumerate(names)}
    lines = ["@startuml", "!pragma layout smetana",
             "left to right direction", "skinparam shadowing false",
             "skinparam defaultFontName SansSerif",
             f"title Ubuntu dependencies: {root}"]
    for name in names:
        suffix = " [missing]" if name in graph.missing else ""
        label = (name + suffix).replace("\\", "\\\\").replace('"', '\\"')
        color = " #D6EAF8" if name == root else ""
        lines.append(f'rectangle "{label}" as {aliases[name]}{color}')
    for parent in names:
        for child in graph.edges[parent]:
            lines.append(f"{aliases[parent]} --> {aliases[child]}")
    return "\n".join([*lines, "@enduml", ""])


def render_png(source, output):
    """Render via java -jar; reject failures without saving error images."""
    jar = os.environ.get("PLANTUML_JAR", "plantuml.jar")
    if not Path(jar).is_file():
        raise ValueError("Set PLANTUML_JAR to the local PlantUML JAR file")
    java = os.environ.get("JAVA", "java")
    command = [java, "-Djava.awt.headless=true", "-jar", jar,
               "-pipe", "-tpng", "-charset", "UTF-8"]
    result = subprocess.run(command, input=source.encode("utf-8"),
                            capture_output=True, timeout=RENDER_TIMEOUT,
                            check=False)
    if result.returncode or not result.stdout.startswith(PNG_SIGNATURE):
        message = result.stderr.decode("utf-8", errors="replace")
        raise ValueError(f"PlantUML failed: {message.strip()}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.stdout)
    return output


def save_diagram(graph, root, output):
    """Save editable .puml plus PNG, keeping text if rendering fails."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    source = plantuml(graph, root)
    output.with_suffix(".puml").write_text(source, encoding="utf-8")
    render_png(source, output)
    return source
