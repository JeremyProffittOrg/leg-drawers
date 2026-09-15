# plan.md — parametric table-leg zip-tie drawers

## Locked decisions (user-confirmed; do not revisit)

- 2026-09-15: Build one OpenSCAD file with Customizer settings for drawer count, drawer height, drawer length/width, table-leg X/Y, table-leg left/right, ledge heights on top left/right/back and top front.
- 2026-09-15: Housing and drawers are separate parts. Housing always prints with openings up. Drawers always print bottom-down.
- 2026-09-15: Always printable on a Bambu Lab H2D (single-nozzle guard 320 x 315 x 320 mm under 325 x 320 x 325).
- 2026-09-15: Side C-channel mount for zip ties onto a table leg.
- 2026-09-15: Produce 10 variants and email a PDF catalog of drawings and renders.

## Verified facts

- OpenSCAD 2021.01 at `C:\Program Files\OpenSCAD\openscad.exe`
- H2D single-nozzle: 325 x 320 x 325 mm (Bambu wiki / TDS)
- Operator mail: `proffitt.jeremy@gmail.com` from `@jeremy.ninja` via SES us-east-1
- Repo: `JeremyProffittOrg/leg-drawers` on `main`

## Stop conditions (only these)

- SES identity rejected
- OpenSCAD cannot export a watertight STL for a variant
- A variant cannot be made to fit the H2D guard without changing the asked parameters

## parametric-scad — one Customizer file

- [x] scad-model — `leg-drawers.scad` compiles and exports housing_print + drawer_print STL
- [x] ten-variants — `variants.json` has 10 named sets; each H2D PASS
- [x] render-catalog — 10 cameras per variant + catalog PDF (23 pages, 4491516 bytes)
- [x] pdf-email — SES MessageId 010001a0a40aed4f-8d63fed5-8b08-42c5-822c-23db06b50831-000000

## Execution log

- 2026-09-15: First ISO showed a table-top slab covering the tray. Removed it. Context is a ghost leg only.
- 2026-09-15: Front/back U-arms were horizontal plates in the openings-up print (roofs). Replaced with a C-channel: outer wall is a vertical print wall, back stop sits on the bed, front stays open so the unit slides onto a standing leg.
- 2026-09-15: All 10 variants H2D PASS. Catalog `docs/leg-drawers-variant-catalog.pdf` is 23 pages. Cover, comparison, 10 x 2 plates (ISO + drawings/print poses), Customizer reference. Pages 1-5 and 23 inspected via pdftoppm.
