extends CharacterBody2D
@onready	var ray_c = $Sensors/RayCenter
@onready	var ray_l = $Sensors/RayLeft
@onready	var ray_r = $Sensors/RayRight
#@export var speed = 400.0

#func _physics_process(delta):
	## This captures 8-way movement (WASD/Arrows) and normalizes it
	## so diagonal movement isn't faster than straight movement.
	#var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	#
	#if direction:
		#velocity = direction * speed
	#else:
		## Stop smoothly when no input is detected
		#velocity = velocity.move_toward(Vector2.ZERO, speed)
#
	## move_and_slide() uses the 'velocity' property to handle collisions automatically
	#move_and_slide()
	#print("Velocity: ", velocity, " | Position: ", global_position)

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

func execute_move(motor_data: Dictionary):
	var thrust = motor_data.get("thrust", 0.0)
	var steer = motor_data.get("steer", 0.0)
	
	# 1. Update Rotation based on steer primitive
	rotation += steer * get_process_delta_time() * 4.0 
	
	# 2. Update Velocity based on NEW rotation
	velocity = Vector2.RIGHT.rotated(rotation) * (thrust * 150.0)
	
	move_and_slide()
