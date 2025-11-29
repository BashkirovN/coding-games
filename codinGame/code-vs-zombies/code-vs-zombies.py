import sys
import math
import numpy as np

# Save humans, destroy zombies!
# To debug: print("Debug messages...", file=sys.stderr, flush=True)

Z_SPEED = 400
ASH_SPEED = 1000
ASH_RANGE = 2000
LURE_MIN = 2401


class Human:
    def __init__(self, x, y, id):
        self.x = x
        self.y = y
        self.id = id

    def __repr__(self):
        return f'{self.id}, ({self.x},{self.y})'


class Zombie:
    def __init__(self, x, y, next_x, next_y, id):
        self.x = x
        self.y = y
        self.next_x = next_x
        self.next_y = next_y
        self.id = id

    def __repr__(self):
        return f'{self.id}, ({self.x},{self.y})'


def get_distance(x, y, x1, y1):
    return round(math.sqrt((x - x1)**2 + (y - y1)**2))


def predict_next_point(x, y, x_t, y_t, speed=Z_SPEED):
    """
    Predicts the next point along a straight path.

    Args:
        x, y (int): Current position
        x_t, y_t (int): Fixed target position.
        speed (int): Distance the unit moves in one tick.

    Returns:
        tuple: (next_x, next_y) coordinates.
    """

    # Calculate the Displacement Vector (D)
    Dx = x_t - x
    Dy = y_t - y

    # Calculate the Magnitude (|D|)
    magnitude = math.sqrt(Dx**2 + Dy**2)

    if magnitude == 0:
        return (x, y)

    # Calculate the Unit Direction Vector (D_hat)
    unit_Dx = Dx / magnitude
    unit_Dy = Dy / magnitude

    # Calculate the Next Position (P_next)
    x_next = x + (unit_Dx * speed)
    y_next = y + (unit_Dy * speed)

    return (x_next, y_next)


def get_humans_by_closest_zombie():
    global humans, zombies
    humans_and_closest_z = {
        h.id: min([get_distance(h.x, h.y, z.x, z.y) for z in zombies]) for h in humans}
    sorted_humans = sorted(humans_and_closest_z.items(),
                           key=lambda item: item[1])
    return sorted_humans


def get_zombies_by_closest_human():
    """
    returns [z_id, (h_id, dist)]
    """
    global humans, zombies
    zombies_and_distance = {z.id: min([
        (h.id, get_distance(h.x, h.y, z.x, z.y)) for h in humans
    ], key=lambda item: item[1]
    ) for z in zombies}
    sorted_zombies = sorted(zombies_and_distance.items(),
                            key=lambda item: item[1][1])
    return sorted_zombies


def get_zombie_by_id(id):
    global zombies
    for z in zombies:
        if z.id == id:
            return z


def get_human_by_id(id):
    global humans
    for h in humans:
        if h.id == id:
            return h


def can_be_saved(human, z_dist, ash_x, ash_y,):
    z_ticks = z_dist // Z_SPEED
    ash_ticks = max(
        0, (get_distance(human.x, human.y, ash_x, ash_y) - ASH_RANGE) // ASH_SPEED)
    return z_ticks >= ash_ticks


def is_linearly_separable(humans, zombies, max_iterations=1000):
    """
    Checks for linear separability between two lists of points using the PLA.

    Args:
        humans (list): List of (x, y) tuples 
        zombies (list): List of (x, y) tuples
        max_iterations (int): Maximum number of passes through the data.

    Returns:
        bool: True separable, False otherwise.
    """

    all_points = np.array(humans + zombies)

    # Create the labels array (+1 for humans, -1 for zombies)
    labels_c1 = np.ones(len(humans))
    labels_c2 = -np.ones(len(zombies))
    labels = np.concatenate((labels_c1, labels_c2))

    # Augment Data (Add the bias term: 1)
    #   X becomes an N x 3 array: (x, y, 1)
    X = np.hstack((all_points, np.ones((all_points.shape[0], 1))))

    # Initialize Weights
    #   weights = (w1, w2, b)
    weights = np.zeros(X.shape[1])

    # Run PLA
    for _ in range(max_iterations):
        misclassified_count = 0

        for i in range(X.shape[0]):
            # Prediction: sign(w1*x + w2*y + b)
            prediction = np.sign(np.dot(X[i], weights))

            # Check for misclassification (0.0 means misclassified for our purposes too)
            if prediction != labels[i]:
                misclassified_count += 1

                # Update weights: w = w + label * data_point
                weights += labels[i] * X[i]

        # If no misclassifications, it is separable
        if misclassified_count == 0:
            return True

    # If max iterations reached, it's assumed not separable
    return False


def can_lure(z, h, ash_x, ash_y):
    ticks = 1
    z_last_x, z_last_y = z.x, z.y
    while True:
        z_next_x, z_next_y = predict_next_point(
            z.x, z.y, h.x, h.y, Z_SPEED * ticks)
        new_ash_to_z_dist = get_distance(
            z_last_x, z_last_y, ash_x, ash_y) - ASH_SPEED * ticks
        new_h_to_z_dist = get_distance(z_next_x, z_next_y, h.x, h.y)
        if new_h_to_z_dist < Z_SPEED:
            return False
        if new_ash_to_z_dist < new_h_to_z_dist:
            return True
        z_last_x, z_last_y = z_next_x, z_next_y
        ticks += 1


def is_lured(ash_pos, z_cur_pos, z_next_pos, angle_tolerance=0.999):
    """
    Determines if a unit's movement vector, if extended, 
    would hit the Ash's location.

    Args:
        ash_pos (tuple): Fixed (x, y)
        z_cur_pos (tuple): (x, y) coordinates of the zombie now
        z_next_pos (tuple): (x, y) coordinates of the zombie after one step


    Returns:
        bool: True if the zombie is aiming directly at ash_pos, False otherwise.
    """
    P_unit = np.array(z_cur_pos, dtype=float)
    P_next = np.array(z_next_pos, dtype=float)
    P_you = np.array(ash_pos, dtype=float)

    V_unit = P_next - P_unit
    D_target = P_you - P_unit

    norm_V = np.linalg.norm(V_unit)
    norm_D = np.linalg.norm(D_target)

    if norm_V == 0 or norm_D == 0:
        return False

    # Calculate the dot product
    dot_product = np.dot(V_unit, D_target)

    # Normalize the dot product to get the cosine of the angle (cos(theta))
    cos_theta = dot_product / (norm_V * norm_D)

    # Check if the cosine is very close to 1 (meaning the angle is very close to 0)
    return cos_theta > angle_tolerance


def calculate_waypoint(current_pos, target_pos, zombies_positions, speed=ASH_SPEED, separation_distance=LURE_MIN*2, separation_weight=599999.0):
    """
    Calculates the next waypoint vector based on goal seeking and collision avoidance.

    Args:
        current_pos (tuple/list): (x, y) coordinates of Ash
        target_pos (tuple/list): (x, y) coordinates of the final target.
        zombies_positions (list of tuples): List of (x, y) coordinates of nearby zombies.
        speed (int): Maximum distance Ash can travel in one step.
        separation_distance (int): Distance to maintain from other units.
        separation_weight (float): Experimentally determined multiplier for the avoidance force

    Returns:
        tuple: (x_waypoint, y_waypoint) coordinates.
    """

    P_current = np.array(current_pos)
    P_target = np.array(target_pos)

    # --- Helper Functions ---
    def normalize(vector):
        """Returns the unit vector."""
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else np.zeros(2)

    def limit(vector, max_magnitude):
        """Limits the magnitude of a vector."""
        magnitude = np.linalg.norm(vector)
        if magnitude > max_magnitude:
            return normalize(vector) * max_magnitude
        return vector

    # Goal Seeking Force (V_seek)
    D_target = P_target - P_current

    # If already at the target, stop moving
    if np.linalg.norm(D_target) < speed:
        return target_pos

    V_seek = normalize(D_target) * speed

    # Separation Force (V_separate)
    V_separate = np.zeros(2)

    for P_other in zombies_positions:
        P_other = np.array(P_other)

        # Vector from the other unit to our unit (repulsion direction)
        D_other = P_current - P_other
        distance = np.linalg.norm(D_other)

        if 0 < distance < separation_distance:
            # Calculate repulsion force: stronger when closer
            repulsion_force_magnitude = separation_weight / distance

            # Apply force in the direction D_other
            V_repel = normalize(D_other) * repulsion_force_magnitude
            V_separate += V_repel

    # Combine Forces (V_result)
    V_result = V_seek + V_separate

    # Limit Speed
    V_final = limit(V_result, speed)

    # Calculate New Waypoint
    P_waypoint = P_current + V_final

    return tuple([min(19000, max(0, math.ceil(c))) for c in P_waypoint])


def find_optimal_capture_position_path(
    unit_positions,
    ash_pos,
    grid_resolution=25  # More will likely timeout
):
    """
    Finds the optimal reachable waypoint that maximizes zombie capture, 
    considering all points along the path and the final arrival point.

    Args:
        unit_positions (list of tuples): List of (x, y) coordinates
        ash_pos (tuple): (x, y) coordinates
        grid_resolution (int): Experimentally determined number of search points per axis in the reachable area

    Returns:
        tuple: (best_x, best_y) coordinates of the optimal center, and units captured.
    """
    if not unit_positions:
        return ash_pos, 0

    points = np.array(unit_positions, dtype=float)
    P_start = np.array(ash_pos, dtype=float)

    # Define the Search Area (Reachable Circle)
    max_move = ASH_SPEED

    search_min_x = P_start[0] - max_move
    search_max_x = P_start[0] + max_move
    search_min_y = P_start[1] - max_move
    search_max_y = P_start[1] + max_move

    x_coords = np.linspace(search_min_x, search_max_x, grid_resolution)
    y_coords = np.linspace(search_min_y, search_max_y, grid_resolution)

    best_capture_count = -1
    best_center = P_start

    # Path-Based Capture Evaluation
    for cx in x_coords:
        for cy in y_coords:
            P_candidate = np.array([cx, cy])

            # Check reachability first
            path_vector = P_candidate - P_start
            path_length = np.linalg.norm(path_vector)

            if path_length > max_move:
                continue

            current_capture_count = 0

            # Iterate through each unit to check for capture along the path
            for P_unit in points:
                # Minimum squared distance from P_unit to the line segment P_start -> P_candidate

                # Check 1: Calculate the projection of the unit onto the path line
                # Vector from start to unit
                vec_start_to_unit = P_unit - P_start

                # Length of the path vector squared
                path_length_sq = path_length**2

                if path_length_sq == 0:
                    # If unit doesn't move, just check distance to P_start
                    t = 0
                else:
                    # Calculate 't', the scalar projection onto the path line.
                    # t=0 is P_start, t=1 is P_candidate, 0 < t < 1 is on the segment.
                    t = np.dot(vec_start_to_unit, path_vector) / path_length_sq

                # Check 2: Clamp t to the [0, 1] segment
                t_clamped = np.clip(t, 0.0, 1.0)

                # Find the point on the segment closest to the unit
                P_closest_on_segment = P_start + t_clamped * path_vector

                # Check 3: Calculate the distance from the unit to the closest point on the segment
                distance_sq = np.sum((P_unit - P_closest_on_segment) ** 2)

                # If the unit is within range of the path (including the final point)
                if distance_sq <= ASH_RANGE**2:
                    current_capture_count += 1

            # Update the Best Result
            if current_capture_count > best_capture_count:
                best_capture_count = current_capture_count
                best_center = P_candidate

    final_center = tuple(np.clip(np.round(best_center), 0, 19000))
    return (round(c) for c in final_center)


humans = []
zombies = []

# game loop
while True:
    humans.clear()
    zombies.clear()

    x, y = [int(i) for i in input().split()]
    human_count = int(input())
    for i in range(human_count):
        human_id, human_x, human_y = [int(j) for j in input().split()]
        humans.append(Human(human_x, human_y, human_id))
    zombie_count = int(input())
    for i in range(zombie_count):
        zombie_id, zombie_x, zombie_y, zombie_xnext, zombie_ynext = [
            int(j) for j in input().split()]
        zombies.append(Zombie(zombie_x, zombie_y,
                       zombie_xnext, zombie_ynext, zombie_id))

    # Discard those who can't be saved :(
    sorted_humans = get_humans_by_closest_zombie()
    for h in sorted_humans:
        h_in_danger = get_human_by_id(h[0])
        if not can_be_saved(h_in_danger, h[1], x, y):
            print(h_in_danger.id, "has been written-off :(",
                  file=sys.stderr, flush=True)
            humans.remove(h_in_danger)

    sorted_zombies = get_zombies_by_closest_human()

    lineraly_separable = is_linearly_separable(
        [(h.x, h.y) for h in humans], [(z.x, z.y) for z in zombies])
    can_lure_all = all([can_lure(get_zombie_by_id(
        z[0]), get_human_by_id(z[1][0]), x, y) for z in sorted_zombies])
    if len(humans) > 1 and len(zombies) > 1 and lineraly_separable and can_lure_all:

        zombies_by_prox_to_ash = sorted(
            zombies, key=lambda z: get_distance(x, y, z.x, z.y))

        lured = [z for z in zombies if is_lured(
            (x, y), (z.x, z.y), (z.next_x, z.next_y))]

        next_z = None

        for entry in sorted_zombies:
            z = get_zombie_by_id(entry[0])
            if z not in lured:
                next_z = z
                break

        print('next_z', next_z, file=sys.stderr, flush=True)

        z_distances_to_ash = [get_distance(x, y, z.x, z.y) for z in zombies]
        surrounded = sum(d-Z_SPEED < ASH_RANGE for d in z_distances_to_ash) > 3
        all_arrived_to_the_party = max(z_distances_to_ash) < 3000

        if all_arrived_to_the_party or surrounded:
            print("Time to Reap!", file=sys.stderr, flush=True)
            target_x, target_y = find_optimal_capture_position_path(
                [(z.next_x, z.next_y) for z in zombies], (x, y))

            print(target_x, target_y)
            continue
        else:
            print("Time to Lure!", file=sys.stderr, flush=True)
            if not next_z:
                next_z = get_zombie_by_id(sorted_zombies[-1][0])
            target_x, target_y = calculate_waypoint((x, y), (next_z.next_x, next_z.next_y), [
                                                    (z.next_x, z.next_y) for z in lured])

            print(target_x, target_y)
            continue

    z = sorted_zombies[0]
    target = get_zombie_by_id(z[0])

    # Your destination coordinates
    print(target.x, target.y)
