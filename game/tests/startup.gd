extends SceneTree
## Explicitly launch the configured main scene and quit with an intentional status.
## This avoids platform-specific implicit --quit-after exit codes on headless Windows.

func _initialize() -> void:
	call_deferred("run_startup")

func run_startup() -> void:
	var main_path: String = ProjectSettings.get_setting("application/run/main_scene", "")
	if main_path != "res://school_lab.tscn":
		printerr("FAIL: unexpected main scene: " + main_path)
		quit(1)
		return
	var packed = load(main_path)
	if packed == null:
		printerr("FAIL: configured main scene could not be loaded")
		quit(1)
		return
	var scene = packed.instantiate()
	root.add_child(scene)
	await process_frame
	for frame in range(5):
		await physics_frame
	if scene.player == null or scene.camera == null or scene.http == null:
		printerr("FAIL: player/camera/HTTP bridge components missing at startup")
		quit(1)
		return
	print("PASS: configured school lab scene started for multiple engine frames")
	quit(0)
