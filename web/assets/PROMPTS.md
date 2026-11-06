# Generated meshes

Generator for committed files: TripoSR (`stabilityai/TripoSR`), MIT, copyright 2024 Tripo AI and Stability AI. See `LICENSE-TRIPOSR.txt`.

Hunyuan3D-2 previews are not committed. The game server does not run either model.

Each file is one object, Y-up, base on y = 0, 1 unit = 1 meter. Scatter kits are a single mesh of at most 5000 triangles. Landmarks are at most 80000 triangles.

If a name is missing, the procedural builder in `web/js/kits/` is the mesh the player sees.

Generated with TripoSR `stabilityai/TripoSR` from a single reference image, marching cubes resolution 80, then decimated:

Kits: pitcher, sundew, snap_maw, acid_cup, vine_noose, spiral_tree, blossom_tree, glass_leaf, staghorn, fiddlehead, epiphyte, heron, grazer, loris, dragonfly, kite_bird, glow_moth, lantern_frog, beetle_lamp, brine_skipper.

Landmarks: great_fall, cathedral_heart, spore_well, bloom_ridge, pitcher_throne, lantern_monarch, mirror_pan, heron_bend, vine_gate, amber_circle, fern_nave, sundew_jewel.

Prompts are the sentences in `docs/plans/02-forest-catalog.md` under Task 3.
