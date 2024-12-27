from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import product

import matplotlib.pyplot as plt
import pulp
from matplotlib.patches import Rectangle

from shapes import (
    SHAPE_B,
    SHAPE_DB,
    SHAPE_DG,
    SHAPE_LB,
    SHAPE_LG,
    SHAPE_O,
    SHAPE_P,
    SHAPE_PU,
    SHAPE_R,
    SHAPE_Y,
    SHAPES_ALL,
    ShapeInstance,
    ShapeTemplate,
    colormap_for_matplotlib,
    get_color,
)


@dataclass
class Board:
    shape_board: tuple[int, int] = (5, 10)  # 5 rows, 10 columns
    # placements: dict[tuple[int, int], ShapeInstance] = field(default_factory=dict)
    placements: dict[tuple[int, int], list[ShapeInstance]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def fill_grid(self) -> dict[tuple[int, int], str]:
        grid = {}
        for placement, shapes in self.placements.items():
            for shape in shapes:
                grid_shape = shape.fill_grid()
                for row, col in grid_shape:
                    if (placement[0] + row, placement[1] + col) not in grid:
                        grid[(placement[0] + row, placement[1] + col)] = set()
                    grid[(placement[0] + row, placement[1] + col)].add(
                        grid_shape[(row, col)]
                    )
        return grid

    def occupied_cells(self) -> list[tuple[int, int]]:
        return sorted(list(self.fill_grid().keys()))

    def is_valid_placement(self) -> bool:
        grid = self.fill_grid()
        for row, col in grid:
            if len(grid[(row, col)]) > 1:
                return False
            if row < 0 or row >= self.shape_board[0]:
                return False
            if col < 0 or col >= self.shape_board[1]:
                return False
        return True

    def render_mpl(self):
        fig, ax = plt.subplots(1, 1)
        ax.grid(True)
        ax.set_aspect("equal")
        ax.set_xlim(0, self.shape_board[1])
        ax.set_ylim(0, self.shape_board[0])
        # make increments of 1
        ax.set_xticks(range(self.shape_board[1]))
        ax.set_yticks(range(self.shape_board[0]))
        for (row, col), shape_set in self.fill_grid().items():
            for shape in shape_set:
                ax.add_patch(
                    Rectangle(
                        (col, row),
                        1,
                        1,
                        # facecolor=colormap_for_matplotlib[shape],
                        facecolor=get_color(shape),
                        alpha=0.5,
                    )
                )
            ax.text(col + 0.5, row + 0.5, shape_set, ha="center", va="center")
        ax.invert_yaxis()
        fig.tight_layout()
        plt.show()


# test_board = Board()
# test_board.placements[(0, 0)] = ShapeInstance(SHAPE_LG, 1, 90)
# test_board.placements[(0, 4)] = ShapeInstance(SHAPE_DG, 0, 0)

# print(test_board.fill_grid())


# write a solver to place all shapes on the board
# shapes can be rotated and oinly one layout can be used at a time
# shapes cannot overlap
# shapes cannot be placed outside the board
# only one of each shape can be placed on the board


def brute_force_solver(
    init_board: Board, shapes_to_place: list[ShapeTemplate]
) -> Board | None:
    placement_locations = [
        (row, col)
        for row in range(init_board.shape_board[0])
        for col in range(init_board.shape_board[1])
    ]
    layouts = [0, 1]
    rotations = [0, 90, 180, 270]

    single_shape_combo_set = list(product(placement_locations, layouts, rotations))
    print(f"len(single_shape_combo_set): {len(single_shape_combo_set)}")

    combos_all = list(product(single_shape_combo_set, repeat=len(shapes_to_place)))
    print(f"len(combos_all): {len(combos_all)}")

    solution_found = False
    solution = None

    for combo in combos_all:
        board_trial = deepcopy(init_board)

        for shape, combo_part in zip(shapes_to_place, combo):
            print(f"shape: {shape.name}")
            placement, layout, rotation = combo_part
            board_trial.placements[placement].append(
                ShapeInstance(shape, layout, rotation)
            )

        if board_trial.is_valid_placement():
            solution_found = True
            solution = board_trial
            break

    if solution_found:
        assert solution is not None
        print("Solution found!")
        print(solution.fill_grid())
        return solution
    else:
        print("No solution found.")
        return None


def get_occupied_cells(
    shape_template: ShapeTemplate,
    layout_idx: int,
    rotation: int,
    row: int,
    col: int,
) -> list[tuple[int, int]]:
    board = Board()
    board.placements[(row, col)].append(
        ShapeInstance(shape_template, layout_idx, rotation)
    )
    grid = board.fill_grid()
    locs = sorted(list(grid.keys()))
    return locs


def mip_solver(
    init_board: Board,
    shapes_to_place: list[ShapeTemplate],
    max_solutions: int = 5,
    allow_holes: bool = False,
) -> list[Board] | None:
    layout_versions = [0, 1]
    rotations = [0, 90, 180, 270]
    shape_name_map = {shape.name: shape for shape in shapes_to_place}
    shape_names = list(shape_name_map.keys())

    problem = pulp.LpProblem("iq_fit")

    x = pulp.LpVariable.dicts(
        "x",
        (
            shape_names,
            layout_versions,
            rotations,
            range(init_board.shape_board[0]),
            range(init_board.shape_board[1]),
        ),
        cat=pulp.LpBinary,
    )
    print(x)

    # Constraint 1: Each piece must be placed exactly once
    for shape in shape_names:
        problem += (
            pulp.lpSum(
                x[shape][layout][rotation][row][col]
                for layout in layout_versions
                for rotation in rotations
                for row in range(init_board.shape_board[0])
                for col in range(init_board.shape_board[1])
            )
            == 1
        )

    # Constraint 2: Only one layout version per piece
    for shape in shape_names:
        for layout in layout_versions:
            problem += (
                pulp.lpSum(
                    x[shape][layout][rotation][row][col]
                    for rotation in rotations
                    for row in range(init_board.shape_board[0])
                    for col in range(init_board.shape_board[1])
                )
                <= 1
            )

    # Constraint 3: Only one rotation per layout version
    for shape in shape_names:
        for layout in layout_versions:
            for rotation in rotations:
                problem += (
                    pulp.lpSum(
                        x[shape][layout][rotation][row][col]
                        for row in range(init_board.shape_board[0])
                        for col in range(init_board.shape_board[1])
                    )
                    <= 1
                )

    # Constraint 4: pieces are in bounds of the board
    for shape in shape_names:
        for layout in layout_versions:
            for rotation in rotations:
                for row in range(init_board.shape_board[0]):
                    for col in range(init_board.shape_board[1]):
                        # Get the real grid points occupied by the piece
                        occupied_points = get_occupied_cells(
                            shape_name_map[shape],
                            layout,
                            rotation,
                            row,
                            col,
                        )

                        # Check if all occupied points are within bounds
                        for occupied_row, occupied_col in occupied_points:
                            if not (
                                0 <= occupied_row < init_board.shape_board[0]
                                and 0 <= occupied_col < init_board.shape_board[1]
                            ):
                                # If out of bounds, force x = 0 for this configuration
                                # problem += x[shape, layout, rotation, row, col] == 0
                                problem += x[shape][layout][rotation][row][col] == 0

    # Constraint: Pieces must not overlap

    # Define auxiliary variables for grid cell occupancy
    y = pulp.LpVariable.dicts(
        "y",
        (
            (row, col)
            for row in range(init_board.shape_board[0])
            for col in range(init_board.shape_board[1])
        ),
        cat=pulp.LpBinary,
    )

    init_board_occupied_cells = init_board.occupied_cells()
    occupied_already = {
        (r, c): 1 if (r, c) in init_board_occupied_cells else 0
        for r in range(init_board.shape_board[0])
        for c in range(init_board.shape_board[1])
    }

    # Link y[row][col] to x[shape, layout, rotation, base_row, base_col]
    for row in range(init_board.shape_board[0]):
        for col in range(init_board.shape_board[1]):
            # Collect all piece configurations that can occupy cell (row, col)
            covering_configs = []
            for shape in shape_names:
                for layout in layout_versions:
                    for rotation in rotations:
                        for base_row in range(init_board.shape_board[0]):
                            for base_col in range(init_board.shape_board[1]):
                                # Check if the current configuration covers this cell
                                if (row, col) in get_occupied_cells(
                                    shape_name_map[shape],
                                    layout,
                                    rotation,
                                    base_row,
                                    base_col,  # <-- Fix: pass in the base_row, base_col
                                ):
                                    covering_configs.append(
                                        (shape, layout, rotation, base_row, base_col)
                                    )

            # Link y[row][col] to the covering configurations
            problem += (
                y[row, col]
                == occupied_already[row, col]
                + pulp.lpSum(
                    x[shape][layout][rotation][base_row][base_col]
                    for shape, layout, rotation, base_row, base_col in covering_configs
                ),
                f"Link_y_Cell_{row}_{col}",
            )

    # Ensure no overlaps
    for row in range(init_board.shape_board[0]):
        for col in range(init_board.shape_board[1]):
            problem += y[row, col] <= 1, f"No_Overlap_Cell_{row}_{col}"
            if not allow_holes:
                problem += y[row, col] == 1, f"MustCover_Cell_{row}_{col}"

    # # Solve the problem
    # status = problem.solve()

    # # Check solution status
    # if pulp.LpStatus[status] == "Optimal":
    #     # Update init_board with solution
    #     for shape in shapes_to_place:
    #         for layout in layout_versions:
    #             for rotation in rotations:
    #                 for row in range(init_board.shape_board[0]):
    #                     for col in range(init_board.shape_board[1]):
    #                         if x[shape.name][layout][rotation][row][col].varValue == 1:
    #                             init_board.placements[(row, col)].append(
    #                                 ShapeInstance(shape, layout, rotation)
    #                             )
    #     return init_board
    # else:
    #     return None

    solutions = []  # Will store boards
    used_solutions_cuts = []  # Will store the "exclude solution" constraints

    while True:
        # Solve
        status = problem.solve()

        # If no more feasible solutions, stop
        if pulp.LpStatus[status] not in ("Optimal", "Feasible"):
            break

        # Extract this solution's chosen positions
        selected_positions = []
        for shape in shapes_to_place:
            s_name = shape.name
            for layout in layout_versions:
                for rotation in rotations:
                    for row in range(init_board.shape_board[0]):
                        for col in range(init_board.shape_board[1]):
                            val = pulp.value(x[s_name][layout][rotation][row][col])
                            if abs(val - 1.0) < 1e-6:  # or just == 1
                                selected_positions.append(
                                    (s_name, layout, rotation, row, col)
                                )

        # Build a *copy* of init_board with these new placements
        # (So you don’t mutate init_board for subsequent solves)
        # new_board = init_board.copy()  # Or implement your own deep-copy logic
        new_board = deepcopy(init_board)
        for s_name, layout, rotation, row, col in selected_positions:
            new_board.placements[(row, col)].append(
                ShapeInstance(shape_name_map[s_name], layout, rotation)
            )
        solutions.append(new_board)
        if len(solutions) >= max_solutions:
            break

        # ---- Add a cut to exclude this exact solution ----
        # We want: sum(x of these chosen positions) <= (len(selected_positions) - 1)
        # so at least one chosen variable must flip from 1 to 0 in the next solution.
        cut_name = f"Exclude_Solution_{len(solutions)}"
        problem += (
            (
                pulp.lpSum(
                    x[s][l][r][rr][cc] for (s, l, r, rr, cc) in selected_positions
                )
                <= len(selected_positions) - 1
            ),
            cut_name,
        )

        used_solutions_cuts.append(cut_name)

    # After enumerating all solutions, return them
    if not solutions:
        return None  # No feasible solutions
    else:
        return solutions


test_board = Board()
# add a light blue shape to initial board
# test_board.placements[(0, 0)].append(ShapeInstance(SHAPE_LG, 1, 270))
# test_board.placements[(1, 0)].append(ShapeInstance(SHAPE_DB, 0, 0))
# test_board.placements[(3, 0)].append(ShapeInstance(SHAPE_B, 1, 90))
# test_board.placements[(1, 4)].append(ShapeInstance(SHAPE_R, 0, 0))
# test_board.placements[(0, 4)].append(ShapeInstance(SHAPE_LB, 1, 270))
# test_board.placements[(0, 7)].append(ShapeInstance(SHAPE_DG, 1, 270))
# test_board.placements[(2, 6)].append(ShapeInstance(SHAPE_Y, 0, 90))
# test_board.placements[(2, 5)].append(ShapeInstance(SHAPE_PU, 0, 90))


# test_board.placements[(0, 2)].append(ShapeInstance(SHAPE_DG, 0, 90))
# test_board.placements[(3, 4)].append(ShapeInstance(SHAPE_LB, 1, 90))
placed_shapes = [
    # SHAPE_DG,
    # SHAPE_LB,
]

test_board.render_mpl()

shapes_to_place = [shape for shape in SHAPES_ALL if shape not in placed_shapes]
# shapes_to_place = [
#     ShapeTemplate(
#         name=f"dark_green_{i}",
#         layouts={
#             0: {(0, 1), (1, 0), (1, 1), (2, 1)},
#             1: {(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)},
#         },
#     )
#     for i in range(0, 10)
# ]


solutions = mip_solver(test_board, shapes_to_place, max_solutions=1, allow_holes=False)
assert solutions is not None
print(f"len(solutions): {len(solutions)}")
for sol in solutions:
    sol.render_mpl()
