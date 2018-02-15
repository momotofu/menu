from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

class webserverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += """
                    <html>
                        <body>hello!</body>
                        <a href="/main">Go to the main page</a>
                    </html>
                    """
                self.wfile.write(bytes(output.encode()))
                print(output)
                return

            if self.path.endswith("/main"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += """
                    <html>
                        <body>The main page!</body>
                        <a href="/hello">Go to hello page</a>
                    </html>
                    """
                self.wfile.write(bytes(output.encode()))
                print(output)
                return

            if self.path.endswith("/"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += """<form method='POST'
                action='/'><h2>What would you like me to say?</h2><input
                name='message'><input type='submit'
                value='Submit'></form>"""

                output += "</body></html>"

                self.wfile.write(bytes(output.encode()))
                print(output)
                return

        except IOError:
            self.send_error(404, "File not found %s" % self.path)


    def do_POST(self):
        try:
            self.send_response(301)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            length = int(self.headers.get('Content-length', 0))
            body = self.rfile.read(length).decode()
            params = parse_qs(body)
            message_content = params["message"][0]

            output = ""
            output += "<html><body>"
            output += "<h2> Okay, how about this: </h2>"
            output += "<h1> %s </h1>" % message_content

            output += """<form method='POST'
            action='/'><h2>What would you like me to say?</h2><input
            name='message'><input type='submit'
            value='Submit'></form>"""

            output += "</body></html>"
            self.wfile.write(bytes(output.encode()))
            print(output)
            return

        except IOError:
            pass

def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print("Web server running on port %s" % port)
        server.serve_forever()

    except KeyboardInterrupt:
        # A python defined exception when the user
        # presses control-C on their keyboard
        print("^C entered, stopping web server...")
        server.socket.close()

if __name__ == '__main__':
    main()
