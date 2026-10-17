# Label Lens

Label Lens turns a photo of an Italian product label into a plain-English
diet-aware verdict and a small Italian vocabulary lesson.

## Project areas

- `backend/` is Person A's stateless FastAPI service for image analysis.
- The frontend can be developed independently by Person B and should call
  `POST /api/v1/analyze`.

See [backend/README.md](backend/README.md) for setup, the request contract,
privacy notes, and local run instructions.

## Product boundaries

The prototype does not use accounts, a database, photo storage, scan history,
barcode lookup, or medical advice. The API always includes a notice telling
users to check the physical package for allergies.
