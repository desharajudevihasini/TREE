# How the illustrated homepage is organized

1. **Universe scene** — `frontend/art/green-universe.svg`, used as a background image, drawn for TREE.
2. **Floating sign** — HTML in `#welcome` + CSS `.hero-sign`, `.orbit-antenna`, `.sign-interior`.
3. **Second-chance section** — `#about` introduces the premise of a digital twin.
4. **Four adventure cards** — `#adventures` uses each button's `data-go` attribute to open a real working TREE tool.
5. **Lab** — `#lab`, with `#view-dashboard`, `#view-chat`, `#view-scenarios`, `#view-ranking`, `#view-evaluation`. Only one tool is shown at a time.
6. **JavaScript wiring** — `openView()` controls pages; `api()` fetches calculations; `renderDashboard()` populates retrofit cards; click handlers submit calculations to FastAPI.

The backgrounds are illustrations, not GIS, certified energy simulations or live sensor data. This is a local prototype.
