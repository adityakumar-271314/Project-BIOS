extends Area2D

@export var max_damage: float = 2.0 
@export var heat_radius: float = 80.0 # Visual + Logical radius

func _ready():
	# Update the collision shape to match our intended radius
	if has_node("CollisionShape2D"):
		var shape = CircleShape2D.new()
		shape.radius = heat_radius
		$CollisionShape2D.shape = shape

func get_intensity(agent_pos: Vector2) -> float:
	var dist = global_position.distance_to(agent_pos)
	
	# If agent is inside the heat_radius, calculate damage
	if dist < heat_radius:
		var falloff = clamp(1.0 - (dist / heat_radius), 0.0, 1.0)
		return falloff * max_damage
	return 0.0
