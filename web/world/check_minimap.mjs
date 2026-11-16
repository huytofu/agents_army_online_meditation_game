import { compassCode, facingName, formatDistance, project, travelHeading } from "../js/minimap.js";

const meta = { world_min: -2000, world_max: 2000 };
const [westNorthX, westNorthY] = project(meta, -2000, 2000, 4000, 0);
const [eastSouthX, eastSouthY] = project(meta, 2000, -2000, 4000, 0);
const [originX, originY] = project(meta, 0, 0, 4000, 0);

if (westNorthX !== 0 || westNorthY !== 0) throw new Error("northwest corner");
if (eastSouthX !== 4000 || eastSouthY !== 4000) throw new Error("southeast corner");
if (originX !== 2000 || originY !== 2000) throw new Error("origin");
if (facingName(0) !== "north") throw new Error("north");
if (facingName(Math.PI / 2) !== "east") throw new Error("east");
if (facingName(Math.PI) !== "south") throw new Error("south");
if (facingName(-Math.PI / 2) !== "west") throw new Error("west");
if (compassCode(Math.PI / 2) !== "E") throw new Error("compass east");
if (compassCode(-Math.PI / 2) !== "W") throw new Error("compass west");
if (travelHeading(0, 0, 10, 0) !== "east") throw new Error("travel east");
if (travelHeading(0, 0, 0, -10) !== "south") throw new Error("travel south");
if (formatDistance(450) !== "450 m") throw new Error("meters");
if (formatDistance(1400) !== "1.4 km") throw new Error("kilometers");

process.stdout.write("minimap ok\n");
