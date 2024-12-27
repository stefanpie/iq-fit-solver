from dataclasses import dataclass

TPointSet = set[tuple[int, int]]


# @dataclass
# class Shape:
#     name: str
#     layouts: dict[int, TPointSet]
#     current_rotation: int = 0
#     current_layout: int = 0

#     def render_layout(self, layout: TPointSet) -> str:
#         min_row = min(row for row, _ in layout)
#         max_row = max(row for row, _ in layout)
#         min_col = min(col for _, col in layout)
#         max_col = max(col for _, col in layout)
#         rendered = ""
#         for row in range(min_row, max_row + 1):
#             for col in range(min_col, max_col + 1):
#                 rendered += "X" if (row, col) in layout else "_"
#             rendered += "\n"
#         return rendered

#     VALID_ROTATIONS = {0, 90, 180, 270}

#     def layout_rotated(self, layout: int, rotation: int) -> TPointSet:
#         if rotation not in self.VALID_ROTATIONS:
#             raise ValueError(f"Invalid rotation: {rotation}")
#         if rotation == 0:
#             return layout
#         rotated = set()
#         for row, col in layout:
#             if rotation == 90:
#                 rotated.add((col, -row))
#             elif rotation == 180:
#                 rotated.add((-row, -col))
#             elif rotation == 270:
#                 rotated.add((-col, row))

#         # offset back to 0, 0
#         min_row = min(row for row, _ in rotated)
#         min_col = min(col for _, col in rotated)
#         rotated = {(row - min_row, col - min_col) for row, col in rotated}

#         return rotated

#     def fill_grid(self, rotation: int, layout_idx: int) -> dict[tuple[int, int], str]:
#         layout = self.layouts[layout_idx]
#         layout_rotated = self.layout_rotated(layout, rotation)
#         min_row = min(row for row, _ in layout_rotated)
#         min_col = min(col for _, col in layout_rotated)
#         max_row = max(row for row, _ in layout_rotated)
#         max_col = max(col for _, col in layout_rotated)
#         grid = {}
#         for row in range(min_row, max_row + 1):
#             for col in range(min_col, max_col + 1):
#                 if (row, col) in layout_rotated:
#                     grid[(row, col)] = self.name
#         return grid

#     def fill_grid_current(self) -> dict[tuple[int, int], str]:
#         return self.fill_grid(self.current_rotation, self.current_layout)


@dataclass(frozen=True)
class ShapeTemplate:
    name: str
    layouts: dict[int, TPointSet]  # Maps layout index to the point set
    VALID_ROTATIONS = {0, 90, 180, 270}

    def layout_rotated(self, layout: TPointSet, rotation: int) -> TPointSet:
        """Compute the rotated layout."""
        if rotation not in self.VALID_ROTATIONS:
            raise ValueError(f"Invalid rotation: {rotation}")
        if rotation == 0:
            return layout
        rotated = set()
        for row, col in layout:
            if rotation == 90:
                rotated.add((col, -row))
            elif rotation == 180:
                rotated.add((-row, -col))
            elif rotation == 270:
                rotated.add((-col, row))

        # Normalize back to origin
        min_row = min(row for row, _ in rotated)
        min_col = min(col for _, col in rotated)
        rotated = {(row - min_row, col - min_col) for row, col in rotated}
        return rotated

    def __hash__(self) -> int:
        return hash(self.name) + hash(
            frozenset(
                {k: frozenset(sorted(v)) for k, v in sorted(self.layouts.items())}
            )
        )

    def render_layout(self, layout: TPointSet) -> str:
        """Render a specific layout."""
        min_row = min(row for row, _ in layout)
        max_row = max(row for row, _ in layout)
        min_col = min(col for _, col in layout)
        max_col = max(col for _, col in layout)
        rendered = ""
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                rendered += "X" if (row, col) in layout else "_"
            rendered += "\n"
        return rendered


@dataclass
class ShapeInstance:
    template: ShapeTemplate
    current_layout: int = 0
    current_rotation: int = 0

    def render_current(self) -> str:
        """Render the current state of the shape."""
        layout = self.template.layouts[self.current_layout]
        rotated_layout = self.template.layout_rotated(layout, self.current_rotation)
        return self.template.render_layout(rotated_layout)

    def get_current_grid(self) -> TPointSet:
        """Get the current layout in grid coordinates."""
        layout = self.template.layouts[self.current_layout]
        return self.template.layout_rotated(layout, self.current_rotation)

    def fill_grid(self) -> dict[tuple[int, int], str]:
        """Fill the grid with the current layout."""
        layout = self.get_current_grid()
        min_row = min(row for row, _ in layout)
        min_col = min(col for _, col in layout)
        max_row = max(row for row, _ in layout)
        max_col = max(col for _, col in layout)
        grid = {}
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                if (row, col) in layout:
                    grid[(row, col)] = self.template.name
        return grid


# light green
# X _
# X _
# X X
# or
# X X
# _ X
# X X
SHAPE_LG = ShapeTemplate(
    name="light_green",
    layouts={
        0: {(0, 0), (1, 0), (2, 0), (2, 1)},
        1: {(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)},
    },
)

# dark green
# _ X
# X X
# _ X
# or
# X _
# X X
# X X
SHAPE_DG = ShapeTemplate(
    name="dark_green",
    layouts={
        0: {(0, 1), (1, 0), (1, 1), (2, 1)},
        1: {(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)},
    },
)

# dark blue
# _ X
# X X
# _ X
# or
# X X
# X _
# X X
SHAPE_DB = ShapeTemplate(
    name="dark_blue",
    layouts={
        0: {(0, 1), (1, 0), (1, 1), (2, 1)},
        1: {(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)},
    },
)

# blue
# X _
# X _
# X _
# X X
# or
# _ X
# X X
# _ X
# X X
SHAPE_B = ShapeTemplate(
    name="blue",
    layouts={
        0: {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)},
        1: {(0, 1), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)},
    },
)

# red
# X _
# X _
# X _
# X X
# or
# X X
# _ X
# _ X
# X X
SHAPE_R = ShapeTemplate(
    name="red",
    layouts={
        0: {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)},
        1: {(0, 0), (0, 1), (1, 1), (2, 1), (3, 0), (3, 1)},
    },
)

# light blue
# X _
# X _
# X X
# X _
# or
# _ X
# X X
# X X
# _ X
SHAPE_LB = ShapeTemplate(
    name="light_blue",
    layouts={
        0: {(0, 0), (1, 0), (2, 0), (2, 1), (3, 0)},
        1: {(0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1)},
    },
)

# orange
# X _
# X _
# X X
# X _
# or
# X X
# _ X
# X X
# _ X
SHAPE_O = ShapeTemplate(
    name="orange",
    layouts={
        0: {(0, 0), (1, 0), (2, 0), (2, 1), (3, 0)},
        1: {(0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 1)},
    },
)

# yellow
# X X
# X _
# X _
# X _
# or
# _ X
# _ X
# X X
# X X
SHAPE_Y = ShapeTemplate(
    name="yellow",
    layouts={
        0: {(0, 0), (0, 1), (1, 0), (2, 0), (3, 0)},
        1: {(0, 1), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)},
    },
)

# pink
# _ X
# _ X
# X X
# _ X
# or
# X _
# X _
# X X
# X X
SHAPE_P = ShapeTemplate(
    name="pink",
    layouts={
        0: {(0, 1), (1, 1), (2, 0), (2, 1), (3, 1)},
        1: {(0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (3, 1)},
    },
)

# purple
# _ X
# _ X
# X X
# or
# X X
# X X
# X _
SHAPE_PU = ShapeTemplate(
    name="purple",
    layouts={
        0: {(0, 1), (1, 1), (2, 0), (2, 1)},
        1: {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)},
    },
)


SHAPES_ALL = [
    SHAPE_LG,
    SHAPE_DG,
    SHAPE_DB,
    SHAPE_B,
    SHAPE_R,
    SHAPE_LB,
    SHAPE_O,
    SHAPE_Y,
    SHAPE_P,
    SHAPE_PU,
]

colormap_for_matplotlib = {
    "light_green": "lightgreen",
    "dark_green": "darkgreen",
    "dark_blue": "darkblue",
    "blue": "blue",
    "red": "red",
    "light_blue": "skyblue",
    "orange": "orange",
    "yellow": "yellow",
    "pink": "pink",
    "purple": "purple",
}


def get_color(shape_name: str) -> str:
    if shape_name in colormap_for_matplotlib:
        return colormap_for_matplotlib[shape_name]
    else:
        # random color from matplotlib
        return "C" + str(hash(shape_name) % 10)


if __name__ == "__main__":
    for shape in SHAPES_ALL:
        print(shape.name)
        for layout_idx, layout in shape.layouts.items():
            print(f"Layout {layout_idx}")
            print(shape.render_layout(layout))
            print()
            for r in shape.VALID_ROTATIONS:
                print(f"Rotated {r}")
                layout_rotated = shape.layout_rotated(layout, r)
                print(shape.render_layout(layout_rotated))
                print(layout_rotated)
            print()
        print()
