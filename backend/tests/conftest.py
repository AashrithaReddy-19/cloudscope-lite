import os,tempfile
from pathlib import Path

# app.main reads FRONTEND_DIST_DIR once at import time to decide whether to
# mount static file serving, and every test file that imports app.main
# shares the same already-imported module - so this must be set here,
# before pytest imports any test module, not inside an individual test file.
os.environ.setdefault("DATABASE_URL","sqlite:///./test.db")
_static_dir=Path(tempfile.mkdtemp())
(_static_dir/"assets").mkdir()
(_static_dir/"index.html").write_text("<div id=root>cloudscope frontend</div>",encoding="utf-8")
(_static_dir/"assets"/"app.js").write_text("console.log('cloudscope')",encoding="utf-8")
os.environ.setdefault("FRONTEND_DIST_DIR",str(_static_dir))
