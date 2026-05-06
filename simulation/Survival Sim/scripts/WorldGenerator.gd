extends Node2D

@export var food_scene: PackedScene
@export var hazard_scene: PackedScene
@export var landmark_scene: PackedScene

@export var map_size = Vector2(1152, 648)
@export var margin = 100
@export var min_dist_between_objects = 150.0 

var spawned_positions = []
var next_id = 1 

func _ready():
	randomize()
	spawned_positions.clear()
	
	spawn_group(landmark_scene, 8)
	spawn_group(hazard_scene, 6)
	spawn_group(food_scene, 25)

func spawn_group(scene: PackedScene, count: int):
	if not scene: return
	
	for i in range(count):
		var pos = get_valid_position()
		if pos != Vector2.ZERO:
			var inst = scene.instantiate()
			inst.position = pos
			inst.set_meta("unique_id", next_id)
			next_id += 1
			
			add_child(inst)
			spawned_positions.append(pos)

func get_valid_position() -> Vector2:
	var attempts = 0
	while attempts < 20:
		attempts += 1
		var potential_pos = Vector2(
			randf_range(margin, map_size.x - margin),
			randf_range(margin, map_size.y - margin)
		)
		
		var is_safe = true
		for existing_pos in spawned_positions:
			if potential_pos.distance_to(existing_pos) < min_dist_between_objects:
				is_safe = false
				break
		
		if is_safe:
			return potential_pos
			
	return Vector2.ZERO
