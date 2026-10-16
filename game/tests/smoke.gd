extends SceneTree
## Headless engine integration, with a real loopback backend fixture started by tools.verify.
## Exercises scene scripting and backend-driven state. NOT a GUI rendering/mouse usability test.

var lab
var failures := 0

func check(condition: bool, message: String) -> void:
	if condition:
		print("PASS: " + message)
	else:
		failures += 1
		printerr("FAIL: " + message)

func _initialize() -> void:
	call_deferred("run_checks")

func run_checks() -> void:
	var packed = load("res://school_lab.tscn")
	if packed == null:
		printerr("FAIL: main scene could not be loaded")
		quit(1)
		return
	lab = packed.instantiate()
	root.add_child(lab)
	await process_frame
	check(lab.player != null and lab.camera != null, "player and camera instantiated")
	check(lab.ray_targets.values().has("pc-b") and lab.ray_targets.values().has("sw1:fa0/3"), "equipment collider IDs present")
	lab._capture(true)
	var before: float = lab.player.position.z
	Input.action_press("ui_up")
	for i in range(6):
		await physics_frame
	Input.action_release("ui_up")
	check(lab.player.position.z < before - 0.02, "forward movement changes player position")
	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(10, 10)
	lab._unhandled_input(motion)
	check(lab.camera.rotation.x < -0.001, "mouse motion changes camera pitch")
	lab.player.position = Vector3(3.3, 0.05, 0)
	lab.camera.look_at(Vector3(3.3, 1.45, -3.25))
	await physics_frame
	var origin: Vector3 = lab.camera.global_position
	var query := PhysicsRayQueryParameters3D.create(origin, origin - lab.camera.global_transform.basis.z * 5.5)
	query.exclude = [lab.player.get_rid()]
	var hit: Dictionary = lab.get_world_3d().direct_space_state.intersect_ray(query)
	var hit_id := 0
	if not hit.is_empty():
		hit_id = hit["collider"].get_instance_id()
	check(not hit.is_empty() and lab.ray_targets.get(hit_id, "") == "pc-b",
		"crosshair ray can reach PC B")
	lab._capture(false)
	lab._interact("pc-a")
	check("pc-a" in lab.notice.text, "computer inspection prompt")
	lab._interact("sw1")
	check("switch" in lab.notice.text, "switch inspection prompt")
	lab.token = OS.get_environment("NETFORGE_TOKEN")
	if lab.token == "":
		printerr("FAIL: NETFORGE_TOKEN missing from fixture")
		quit(1)
		return
	lab._request("GET", "/state")
	await lab.http.request_completed
	check(lab.state.has("assessment") and lab.state.get("storage", "") == "SQLite", "authenticated initial backend state")
	if not lab.state.has("ports"):
		quit(1)
		return
	check(not lab.state["ports"]["pc-b:eth0"]["linked"], "repair cable initially disconnected")
	check("Repair cable connected" in lab.details.text, "mission rubric feedback visible in HUD text")
	lab.pc_select.select(1)
	lab.ip_input.text = "10.20.30.11/24"
	lab._configure_ip()
	await lab.http.request_completed
	check(lab.state["ports"]["pc-b:eth0"]["address"] == "10.20.30.11/24", "Godot address control updates backend state")
	lab.ip_input.text = "192.168.10.11/24"
	lab._configure_ip()
	await lab.http.request_completed
	check(lab.state["ports"]["pc-b:eth0"]["address"] == "192.168.10.11/24", "Godot address control restores original subnet")
	lab._interact("pc-b")
	check("192.168.10.11/24" in lab.details.text, "inspection displays modeled interface address")
	lab._interact("cable")
	lab._interact("pc-b")
	lab._interact("sw1:fa0/3")
	await lab.http.request_completed
	check(lab.state["ports"]["pc-b:eth0"]["linked"] and lab.repair_visual.visible and not lab.cable_mesh.visible, "interaction connects modeled and visible cable")
	await action({"action":"ping", "source":"pc-b:eth0", "target":"pc-a:eth0"})
	check(lab.state["assessment"]["mission_a"]["complete"], "mission A outcome evidence")
	check("2/2 points" in lab.details.text, "weighted mission A score visible in HUD text")
	for line in ["enable", "configure terminal", "interface fastethernet 0/3", "switchport port-security", "switchport port-security mac-address sticky", "end"]:
		lab._submit_cli(line)
		await lab.http.request_completed
	await action({"action":"ping", "source":"pc-b:eth0", "target":"pc-a:eth0"})
	lab._submit_cli("write memory")
	await lab.http.request_completed
	check(lab.state["assessment"]["mission_b"]["complete"] and lab.state["assessment"]["mission_b"]["score"] == 5,
		"sticky MAC mission scored from validated state")
	check("write memory" in lab.cli_output.text, "simulated switch terminal output updated")
	check("5/5 points" in lab.details.text, "weighted mission B score visible in HUD text")
	await action({"action":"checkpoint"})
	check(not lab.state["checkpoints"].is_empty(), "checkpoint control persisted state")
	var id = lab.state["checkpoints"][0]["id"]
	check(lab._selected_checkpoint_id() == id, "checkpoint selector reflects backend metadata")
	await action({"action":"reset"})
	check(not lab.state["ports"]["pc-b:eth0"]["linked"] and not lab.repair_visual.visible,
		"reset clears cable both logically and visually")
	await action({"action":"restore", "checkpoint_id":id})
	check(lab.state["assessment"]["mission_b"]["complete"] and lab.repair_visual.visible, "checkpoint restore recovers assessed mission")
	lab.pending_delete_id = id
	lab._delete_checkpoint()
	await lab.http.request_completed
	check(lab.state["checkpoints"].is_empty(), "checkpoint delete control removes persisted snapshot")
	await action({"action":"disconnect", "port":"pc-b:eth0"})
	check(not lab.state["ports"]["pc-b:eth0"]["linked"] and lab.cable_mesh.visible, "disconnect restores loose cable visual")
	await action({"action":"reset"})
	check(not lab.state["assessment"]["mission_a"]["complete"], "repeated reset clears mission evidence")
	if failures:
		printerr("Godot headless integration failed checks: " + str(failures))
		quit(1)
	else:
		print("Godot headless integration passed; graphical mouse/visibility still require manual review")
		quit(0)

func action(payload: Dictionary) -> void:
	lab._action(payload)
	await lab.http.request_completed
