extends CharacterBody2D

@onready var ray_c = $Sensors/RayCenter
@onready var ray_l = $Sensors/RayLeft
@onready var ray_r = $Sensors/RayRight
@onready var proximity_sensor = $Sensors/ProximitySensor
@export var speed = 400.0

var current_normals = []
var prev_vel = Vector2.ZERO # Added for acceleration


func _physics_process(_delta):
	current_normals.clear()
	for i in range(get_slide_collision_count()):
		var norm = get_slide_collision(i).get_normal()
		if not current_normals.has(norm):
			current_normals.append(norm)

func get_sensory_data() -> Dictionary:
	var cur_vel = get_real_velocity()
	var delta = get_physics_process_delta_time()
	#for debug
	var x = global_position.x 
	var y = global_position.y

	# Prevent division by zero if delta is somehow 0
	var accel = (cur_vel - prev_vel) / delta if delta > 0 else Vector2.ZERO
	prev_vel = cur_vel 
	
	var physically_stuck = velocity.length() > 10 and cur_vel.length() < 15
	var normals_data = []
	for n in current_normals: 
		normals_data.append({"x": n.x, "y": n.y})

	var data = {
		"delta" : delta,
		"accel": {"x": accel.x, "y": accel.y},
		"ray_c": 1.0, "ray_l": 1.0, "ray_r": 1.0,
		"current_rotation": rotation, 
		"is_stuck": physically_stuck,
		"collision_normals": normals_data,
		"sensed_objects": [],
		"global_x": x,
		"global_y": y
	}

	# Raycasts
	if ray_c.is_colliding(): data["ray_c"] = ray_c.global_position.distance_to(ray_c.get_collision_point()) / 200.0
	if ray_l.is_colliding(): data["ray_l"] = ray_l.global_position.distance_to(ray_l.get_collision_point()) / 200.0
	if ray_r.is_colliding(): data["ray_r"] = ray_r.global_position.distance_to(ray_r.get_collision_point()) / 200.0

	# Proximity
	var detections = proximity_sensor.get_overlapping_bodies() + proximity_sensor.get_overlapping_areas()
	for obj in detections:
		if obj == self or (obj is StaticBody2D and obj.name == "Walls"): continue
		
		var target = obj
		if not (obj.is_in_group("food") or obj.is_in_group("hazard") or obj.is_in_group("landmark")):
			target = obj.get_parent()
			
		var type = "unknown"
		if target.is_in_group("food"): type = "food"
		elif target.is_in_group("hazard"): type = "hazard"
		elif target.is_in_group("landmark"): type = "landmark"
		
		if type != "unknown":
			var to_obj = target.global_position - global_position
			var u_id = -1
			if target.has_meta("unique_id"):
				u_id = target.get_meta("unique_id")
			elif target.get_parent() and target.get_parent().has_meta("unique_id"):
				u_id = target.get_parent().get_meta("unique_id")

			data["sensed_objects"].append({
				"id": u_id, "type": type, "dist": to_obj.length(), 
				"angle": Vector2.RIGHT.rotated(rotation).angle_to(to_obj)
			})
	return data

func execute_move(motor_data: Dictionary):
	rotation += motor_data.get("steer", 0.0) * get_process_delta_time() * 4.0 
	velocity = Vector2.RIGHT.rotated(rotation) * (motor_data.get("thrust", 0.0) * 150.0)
	move_and_slide()
