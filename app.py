"""BuzzzHub ca aplicație de desktop (fereastră proprie, fără browser).

Pornește serverul local pe un port liber și îl afișează într-o fereastră WebView2.
Rulează cu:  pythonw app.py   (fără consolă)  sau prin scurtătura de pe Desktop.
Erorile ajung în buzzzhub.log, lângă fișier.
"""
import threading
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path

AICI = Path(__file__).resolve().parent


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
    icon = AICI / "buzzzhub.ico"
    webview.start(
        icon=str(icon) if icon.exists() else None,
        private_mode=False,                       # ține minte proiectul ales între porniri
        storage_path=str(AICI / ".webview"),
    )
    srv.shutdown()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (AICI / "buzzzhub.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
