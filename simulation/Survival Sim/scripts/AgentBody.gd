extends CharacterBody2D
@onready	var ray_c = $Sensors/RayCenter
@onready	var ray_l = $Sensors/RayLeft
@onready	var ray_r = $Sensors/RayRight
@onready	var proximity_sensor = $Sensors/ProximitySensor
@export var speed = 400.0

func _physics_process(delta):
	var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if direction:
		velocity = direction * speed
	else:
		velocity = velocity.move_toward(Vector2.ZERO, speed)
	move_and_slide()

var last_position = Vector2.ZERO
var stuck_timer = 0.0



func get_ray_data() -> Dictionary:
	var current_vel = get_real_velocity().length()
		
	var intended_vel = velocity.length()
	

	var physically_stuck = intended_vel > 10 and current_vel < 15
	var data = {
		"ray_c": 1.0, 
		"ray_l": 1.0, 
		"ray_r": 1.0,
		"current_rotation": rotation, 
		"is_stuck": physically_stuck
	}
	if ray_c.is_colliding():
		data["ray_c"] = ray_c.global_position.distance_to(ray_c.get_collision_point()) / 200.0
	if ray_l.is_colliding():
		data["ray_l"] = ray_l.global_position.distance_to(ray_l.get_collision_point()) / 200.0
	if ray_r.is_colliding():
		data["ray_r"] = ray_r.global_position.distance_to(ray_r.get_collision_point()) / 200.0
	

	return data



func get_sensory_data() -> Dictionary:
	var ray_data = get_ray_data()
	var sensed_objects = []
	
	
	# Detect BOTH solid bodies and trigger areas
	var detections = proximity_sensor.get_overlapping_bodies()
	detections.append_array(proximity_sensor.get_overlapping_areas())
	
	for obj in detections:
		# Skip self or the ground
		if obj == self or obj is StaticBody2D and obj.name == "Walls": continue
			
		var to_obj = obj.global_position - global_position
		var dist = to_obj.length()
		var type = "unknown"
		
		if obj.is_in_group("food") or obj.get_parent().is_in_group("food"): 
			type = "food"
		elif obj.is_in_group("hazard") or obj.get_parent().is_in_group("hazard"): 
			type = "hazard"
		if type != "unknown":
			pass
			# debug print("GODOT SCANNER SEES: ", type, " | Distance: ", snapped(to_obj.length(), 1))
		# Skip ghosts (dist 0)
		if dist < 5: continue 
		
		var angle = Vector2.RIGHT.rotated(rotation).angle_to(to_obj)
		
		
		if obj.is_in_group("food"): type = "food"
		elif obj.is_in_group("hazard"): type = "hazard"
		elif obj.is_in_group("landmark"): type = "landmark"
		
		# If it's still unknown, check the parent (common for complex scenes)
		if type == "unknown" and obj.get_parent().is_in_group("food"): type = "food"

		sensed_objects.append({"type": type, "dist": dist, "angle": angle})
		
	ray_data["sensed_objects"] = sensed_objects
	


	return ray_data


func execute_move(motor_data: Dictionary):
	var thrust = motor_data.get("thrust", 0.0)
	var steer = motor_data.get("steer", 0.0)
	
	# 1. Update Rotation based on steer primitive
	rotation += steer * get_process_delta_time() * 4.0 
	
	# 2. Update Velocity based on NEW rotation
	velocity = Vector2.RIGHT.rotated(rotation) * (thrust * 150.0)
	
	move_and_slide()
