"""
Servidor de Pré-visualização Local do PWA (Guto & Jé)
Roda um servidor HTTP estático local na porta 8095 para testar no computador ou no celular via Wi-Fi.
"""

import os
import sys
import http.server
import socketserver

PORT = 8095
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        # Desativa cache para desenvolvimento local ágil
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def iniciar():
    print(f"==================================================================")
    print(f"🏠 Servidor Local PWA Finanças da Casa (Guto & Jé)")
    print(f"Diretório web: {WEB_DIR}")
    print(f"Acesse no navegador do computador: http://127.0.0.1:{PORT}")
    print(f"Pressione Ctrl+C para encerrar.")
    print(f"==================================================================")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor finalizado.")

if __name__ == "__main__":
    iniciar()
