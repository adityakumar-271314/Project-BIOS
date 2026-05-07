extends Node2D

@export var food_scene: PackedScene
@export var hazard_scene: PackedScene
@export var landmark_scene: PackedScene

# =====================================================
# WORLD SETTINGS
# =====================================================

@export var map_size: Vector2 = Vector2(1152, 648)
@export var margin: float = 100.0
@export var min_dist_between_objects: float = 150.0

# =====================================================
# DETERMINISTIC SIMULATION
# =====================================================

@export var world_seed: int = 42

var rng := RandomNumberGenerator.new()

# =====================================================
# AGENT SPAWN EXCLUSION ZONE
# =====================================================

const AGENT_SPAWN := Vector2(576, 324)

# Agent is 64x64
const AGENT_HALF_SIZE := 32.0

# Extra safe radius around spawn
const AGENT_SAFE_RADIUS := 120.0

# =====================================================
# INTERNAL STATE
# =====================================================

var spawned_positions: Array[Vector2] = []

var next_id: int = 1

# =====================================================
# READY
# =====================================================

func _ready() -> void:

	# Deterministic world generation
	rng.seed = world_seed

	spawned_positions.clear()

	# Spawn order matters for determinism
	spawn_group(landmark_scene, 8)
	spawn_group(hazard_scene, 6)
	spawn_group(food_scene, 25)

# =====================================================
# SPAWNING
# =====================================================

func spawn_group(scene: PackedScene, count: int) -> void:

	if scene == null:
		return

	for i in range(count):

		var pos = get_valid_position()

		# Failed to find valid position
		if pos == null:
			push_warning(
				"Failed to place object after max attempts."
			)
			continue

		var inst = scene.instantiate()

		inst.position = pos

		# Stable deterministic IDs
		inst.set_meta("unique_id", next_id)

		next_id += 1

		add_child(inst)

		spawned_positions.append(pos)

# =====================================================
# POSITION VALIDATION
# =====================================================

func get_valid_position() -> Variant:

	var attempts := 0

	while attempts < 50:

		attempts += 1

		var potential_pos := Vector2(
			rng.randf_range(
				margin,
				map_size.x - margin
			),
			rng.randf_range(
				margin,
				map_size.y - margin
			)
		)

		# =============================================
		# EXCLUDE AGENT SPAWN AREA
		# =============================================

		if potential_pos.distance_to(AGENT_SPAWN) < AGENT_SAFE_RADIUS:
			continue

		# =============================================
		# OBJECT SPACING
		# =============================================

		var is_safe := true

		for existing_pos in spawned_positions:

			if potential_pos.distance_to(existing_pos) < min_dist_between_objects:

				is_safe = false
				break

		if is_safe:
			return potential_pos

	return null

# =====================================================
# OPTIONAL DEBUG OUTPUT
# =====================================================

func print_world_summary() -> void:

	print("----------------------------------")
	print("WORLD SEED: ", world_seed)
	print("OBJECT COUNT: ", spawned_positions.size())
	print("----------------------------------")
