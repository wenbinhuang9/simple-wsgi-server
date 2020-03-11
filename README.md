# simple-wsgi-server
It a simple http server based on Python web server gateway interface.

# quick start


```

SERVER_ADDRESS = (HOST, PORT) = '', 9999

def make_server(server_address, application):
	server = WSGIserver(server_address)
	server.set_app(application)
	return server

if __name__ == '__main__':
    ## application define
    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['<h1>Hello, web!</h1>']

    httpd = make_server(SERVER_ADDRESS, application)
    ## run application 
    httpd.serve_forever()
 ```
