# Generated meshes

Generator for committed files: TripoSR (`stabilityai/TripoSR`), MIT, copyright 2024 Tripo AI and Stability AI. See `LICENSE-TRIPOSR.txt`.

Hunyuan3D-2 previews are not committed. The game server does not run either model.

Each file is one object, Y-up, base on y = 0, 1 unit = 1 meter. Scatter kits are a single mesh of at most 100000 triangles. Landmarks are at most 400000 triangles. Reference images for a rebuild live next to the meshes in `kits/references/` and `landmarks/references/`.

If a name is missing, the procedural builder in `web/js/kits/` is the mesh the player sees.

Rebuild one scatter kit with the shared script, not an ad-hoc TripoSR call:

```bash
python tools/generate_kit_mesh.py <kit-name>
```

That runs `stabilityai/TripoSR` at marching cubes resolution 256, decimates to at most 100000 triangles before baking one 2048 atlas, and writes a non-metallic GLB (`baseColorFactor` white, `metallicFactor` 0, `roughnessFactor` 1). The reference is already cut out so the subject's longer side is 90% of the frame. `rabbit`, `spiral_tree`, `tree_branched`, and `tree_broad` stay as they are.

Earlier files were generated with TripoSR from a single reference image:

Kits: pitcher, sundew, snap_maw, acid_cup, vine_noose, spiral_tree, blossom_tree, glass_leaf, staghorn, fiddlehead, epiphyte, heron, grazer, loris, dragonfly, kite_bird, glow_moth, lantern_frog, beetle_lamp, brine_skipper.

Landmarks: great_fall, cathedral_heart, spore_well, bloom_ridge, pitcher_throne, lantern_monarch, mirror_pan, heron_bend, vine_gate, amber_circle, fern_nave, sundew_jewel.

Common pieces added after that set, also TripoSR, same triangle cap:

- Neutral ground, moss and a few mild biomes: flower_pink, flower_blue, flower_gold, flower_white, mushroom_brown, mushroom_gold, grass_patch, dirt_patch, fallen_leaves, rabbit, worm, songbird, butterfly, tree_tall, tree_yellow, tree_branched, tree_broad.
- One biome only: monkey in hanging vines, water_puddle in the river, mud_patch in the carnivorous bog, tree_dead in the cathedral, mushroom_white in strange fauna.

Prompts are the sentences in `docs/plans/02-forest-catalog.md` under Task 3.

The common trees, mushrooms, animals, and ground patches below use the same script: marching cubes resolution 256, one 2048 atlas, at most 100000 triangles. Their images are in `kits/references/`. `rabbit`, `spiral_tree`, `tree_branched`, and `tree_broad` are not part of that rebuild.

tree_tall, tree_yellow, tree_branched, tree_broad, mushroom_brown, mushroom_gold, mushroom_white, grass_patch, dirt_patch, mud_patch, fallen_leaves, water_puddle, monkey, rabbit, worm, songbird, butterfly, lantern_frog, loris, kite_bird, beetle_lamp, brine_skipper.
