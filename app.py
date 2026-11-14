"""BuzzzHub as a desktop app (its own window, no browser).

Starts the local server on a free port and shows it in a WebView2 window (WebKit on macOS).
Run with:  pythonw app.py   (no console)  or through the Desktop shortcut.
Errors go to buzzzhub.log, next to this file.
"""
import threading
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    import webview
    import server

    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.H)
    server.PORT = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    webview.create_window(
        "BuzzzHub",
        f"http://127.0.0.1:{server.PORT}/",
        width=1320, height=860, min_size=(760, 520),
        background_color="#fbf6ef",
    )
    icon = HERE / "buzzzhub.ico"
    webview.start(
        icon=str(icon) if icon.exists() else None,
        private_mode=False,                       # remembers the chosen project, theme and language
        storage_path=str(HERE / ".webview"),
    )
    srv.shutdown()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (HERE / "buzzzhub.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
