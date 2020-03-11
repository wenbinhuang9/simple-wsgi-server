import socket
import sys
from io import StringIO
from threading import Thread
from threading import local
## todo implement routing, how routing is implemented ?
## todo routing 应该是应用层的事情了
class WSGIserver(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def set_app(self, application):
        self.application = application

    def __init__(self, server_address):
        self.listen_socket = listen_socket = socket.socket(self.address_family, self.socket_type)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(server_address)
        listen_socket.listen(self.request_queue_size)

        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        self.thread_data = local()

        self.httpheadname_to_wsgikeyname_mapping = {"Content-Type":"CONTENT_TYPE",
                                                    "Content-Length":"CONTENT_LENGTH"}
    def serve_forever(self):
        listen_socket = self.listen_socket
        while True:
            conn, client_address = listen_socket.accept()
            t = Thread(target=self.handle_one_request,  args=(conn,))
            t.start()

    def handle_one_request(self, connection):
        try:
            request_data = connection.recv(1024)
            data = request_data.decode('utf-8')

            self.parse_request(data)

            # Construct environment dictionary using request data
            env = self.get_environ(data)
            self.thread_data.env = env

            # 给flask\tornado传递两个参数，environ，start_response
            result = self.application(env, self.start_response)
            self.finish_response(result, connection)
        finally:
            connection.close()

    def parse_request(self, data):
        print(data)
        format_data = data.splitlines()
        print(format_data)
        if len(format_data):
            request_line = data.splitlines()[0]
            print(request_line)
            ##request_line = request_line.rstrip('\r\n')
            (self.request_method, self.path, self.request_version) = request_line.split()  ## ['GET', '/', 'HTTP/1.1']

    def get_environ(self, data):
        env = {}
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO(data)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method
        # GET
        env['PATH_INFO']         = self.path
        # /hello
        env['SERVER_NAME']       = self.server_name
        # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888 		return env
        if '?' in self.path:
            path,query = self.path.split('?',1)
        else:
            path,query = self.path,''
        env['QUERY_STRING'] = query

        headers = {}
        format_data = data.splitlines()
        for i in range(1, len(format_data)):
            each_http_head = format_data[i]
            split_each_http_head = each_http_head.split(':')
            if len(split_each_http_head) >=2:
                key = split_each_http_head[0].strip()
                value = split_each_http_head[1].strip()
                headers[key] = value


        if headers.get('content-type') != None:
            env['CONTENT_TYPE'] = headers['content-type']

        length = headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for k, v in headers.items():
            k=k.replace('-','_').upper(); v=v.strip()
            if k in env:
                continue                    # skip content length, type,etc.
            if 'HTTP_'+k in env:
                env['HTTP_'+k] += ','+v     # comma-separate multiple headers
            else:
                env['HTTP_'+k] = v
        return env

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [('Date', 'Tue, 31 Mar 2019 12:54:48 GMT'), ('Server', 'WSGIServer 0.2')]
        self.thread_data.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result, client_connection):
        status, response_headers = self.thread_data.headers_set
        response = 'HTTP/1.1 {status}\r\n'.format(status=status)
        for header in response_headers:
            response += '{0}: {1}\r\n'.format(*header)
        response += '\r\n'
        for data in result:
            print(data)
            response += data
        client_connection.sendall(response.encode('utf-8'))
        print(''.join(
            '> {line}\n'.format(line=line)
            for line in response.splitlines()
        ))


SERVER_ADDRESS = (HOST, PORT) = '', 9999

def make_server(server_address, application):
	server = WSGIserver(server_address)
	server.set_app(application)
	return server

if __name__ == '__main__':
    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['<h1>Hello, web!</h1>']

    httpd = make_server(SERVER_ADDRESS, application)
    httpd.serve_forever()
