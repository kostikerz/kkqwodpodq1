"""Dependency-first component order with explicit cycle groups."""


def finishing_order(edges):
    """Iterative DFS postorder, with no recursion even on long chains."""
    seen, result = set(), []
    for start in edges:
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(edges[start]))]
        while stack:
            name, children = stack[-1]
            child = next(children, None)
            if child is None:
                result.append(name)
                stack.pop()
            elif child not in seen:
                seen.add(child)
                stack.append((child, iter(edges[child])))
    return result


def load_order(edges):
    """Return dependency-first strongly connected components (Kosaraju)."""
    reverse = {name: [] for name in edges}
    for name, children in edges.items():
        for child in children:
            reverse[child].append(name)
    seen, groups = set(), []
    for start in reversed(finishing_order(edges)):
        if start in seen:
            continue
        component, stack = [], [start]
        seen.add(start)
        while stack:
            name = stack.pop()
            component.append(name)
            for parent in reverse[name]:
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        groups.append(sorted(component))
    return list(reversed(groups))


def format_order(edges):
    """Mark cyclic components instead of inventing an internal ordering."""
    lines = []
    for position, group in enumerate(load_order(edges), start=1):
        cyclic = len(group) > 1 or group[0] in edges[group[0]]
        label = "cycle group: " if cyclic else ""
        lines.append(f"{position}. {label}{', '.join(group)}")
    return "\n".join(lines)
